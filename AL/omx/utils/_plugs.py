# Copyright © 2023 Animal Logic. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.#
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

import functools

from AL.omx.utils._stubs import cmds
from AL.omx.utils._stubs import om2
from AL.omx.utils import _exceptions

logger = logging.getLogger(__name__)


def createAttributeDummy():
    """Create a dummy node with a message attribute called 'kMessage', this is
    often for a connection to force Maya to create an element plug etc.

    Notes:
        Usually this temp node will need to be removed soon after the attribute is used.
        More info in the notes for :func:`getOrExtendMPlugArray()`.

    Returns:
        om2.MObject: The MObject created.
    """
    dagMod = om2.MDagModifier()
    dummyNode = dagMod.createNode("transform")
    dagMod.doIt()

    fnMsgAttr = om2.MFnMessageAttribute()
    attr = fnMsgAttr.create("kMessage", "kMessage")

    depFn = om2.MFnDependencyNode(dummyNode)
    depFn.addAttribute(attr)

    return dummyNode


def getOrExtendMPlugArray(arrayPlug, logicalIndex, dummy=None):
    """Get the element plug by logicIndex if the element exists, otherwise
    extend the array until the logical index exists.

    Args:
        arrayPlug (om2.MPlug): A valid array plug.

        logicalIndex (int): The logical index.

        dummy (None | om2.MObject, optional): The dummy MObject that contains a 'kMessage',
            createAttributeDummy() will be called to create one if it is None.

    Notes:
        Using this function without a persistent dummy in quick iterations
        will most likely hard crash Maya for you as it struggles to create,
        connect from and delete nodes repeatedly in a short span of time.
        Use autoDummy (dummy argument = None) sparingly and only if you are certain
        this runs with plenty elbow room around it or only once.

    Returns:
        om2.MPlug: The plug at the logical index, or None if it is not a valid array plug.
    """
    cleanUpDummy = False
    if dummy is None:
        dummy = createAttributeDummy()
        cleanUpDummy = True

    # We catch a string that findPlug can't resolve here.
    # Chances are the plug is a subplug of an array, a compound,
    #  or a nesting of a combination of both
    if not arrayPlug.isArray or logicalIndex < 0:
        return None

    aCount = arrayPlug.evaluateNumElements()
    if aCount >= (logicalIndex + 1):
        return arrayPlug.elementByLogicalIndex(logicalIndex)

    dummyDestination = findPlug("kMessage", dummy)
    if not dummyDestination:
        logger.error("Dummy has no kMessage attribute.")
        return None

    dg_mod = om2.MDGModifier()
    for i in range(aCount, logicalIndex + 1):
        srcPlug = arrayPlug.elementByLogicalIndex(i)
        dg_mod.connect(srcPlug, dummyDestination)
        dg_mod.disconnect(srcPlug, dummyDestination)

    dg_mod.doIt()
    if cleanUpDummy:
        dg_mod.deleteNode(dummy)
        dg_mod.doIt()

    return arrayPlug.elementByLogicalIndex(logicalIndex)


def _findLeafPlug(plug, iterCount=None, maxRecursion=8, relaxed=False):
    """ Given a plug it will walk the plug down compound or array elements
    until a leaf plug (one not of type compound or array) is found.

    Args:
        plug (om2.MPlug): the root plug to recursively walk
        iterCount (int, optional): this is just to ensure an iteration lock to prevent odd
                        infinite loops, something for the function, when it runs
                        recursively, to pass back to itself and increment
        maxRecursion (int, optional): the maximum number of recursions allowed
        relaxed (bool, optional): Whether we keep silent on the potential error 

    Raises:
        StopIteration: If iteration exceeds the maxRecursion.
        :class:`PlugArrayOutOfBounds`: If the plug is an array plug with no elements.

    Returns:
        None : If there is an error (shouldn't return).
        om2.MPlug: Of the leaf if one is found.
        om2.MPlug (of the argument plug):  If the supplied plug was already a leaf.
    """
    if iterCount is None:
        iterCount = 0

    if iterCount >= maxRecursion:
        raise StopIteration(
            f"max recursion limit reached at {iterCount} without finding a viable leaf plug"
        )

    iterCount += 1

    # It's important the array test runs first
    if plug.isArray:
        plugCount = plug.evaluateNumElements()

        if plugCount <= 0:
            if not relaxed:
                raise _exceptions.PlugArrayOutOfBounds(
                    f"finding the leaf plug of {plug.name()} failed as it's an unitialized array attribute"
                )

            plugCount = 1

        for i in range(plugCount):
            subPlug = plug.elementByLogicalIndex(i)
            return _findLeafPlug(subPlug, iterCount, maxRecursion, relaxed)

    if plug.isCompound:
        for i in range(plug.numChildren()):
            subPlug = plug.child(i)
            return _findLeafPlug(subPlug, iterCount, maxRecursion, relaxed)

    return plug


def findSubplugByName(plug, token):
    """ Give a plug recursively through all nested compounds looking for plug by name

    Args:
        plug (om2.MPlug): The compound plug.
        token (str): The attribute name / path

    Returns:
        om2.MPlug: The child / descendent plug.
    """
    if not plug.isCompound:
        return None

    if not token:
        return plug

    attrPath = plug.partialName(includeNodeName=False, useFullAttributePath=True)
    plugName = f"{attrPath}.{token}"
    return findPlug(plugName, plug.node())


def _findPlugOnNodeInternal(mob, plugName, networked=False, relaxed=False):
    """
    Args:
        mob (om2.MObject): Maya MObject for a node we want to find the plug on
        plugName (str): string for the name of the plug we want to look for. Paths supported
        networked (bool, optional): pass-through or emulation for Maya's argument that will
                        ensure the only plugs returned are networked ones
        relaxed (bool, optional): clients of this function potentially deal with large sets of data
                        that might contain None, False, or something else flagging
                        an uninteresting index. Relaxed will ensure invalid mobs will
                        be silently skipped if set to True

    Returns:
        om2.MPlug: the plug found unless it outright fails.
            Caller needs to ensure it's not null to know if it's valid or not

    Notes:
        The "networked" argument would be better named ifNetworked or ifConnected,
        but we chose to remain consistent with Maya's semantics and choices over our own.
    """

    # First we validate mob
    if mob is None or (isinstance(mob, om2.MObject) and mob.isNull()):
        if not relaxed:
            raise ValueError("Parameter mob is MObject.kNullObj or None")

        logger.error("Parameter mob is null or None")
        return om2.MPlug()

    try:
        dep = om2.MFnDependencyNode(mob)
    except Exception as e:
        # depNode constructor failure, object is not a MObject
        if not relaxed:
            raise ValueError("Parameter mob is not a valid MObject") from e

        logger.error("Parameter mob is not a valid MObject")
        return om2.MPlug()

    # Now we find the plug
    try:
        return dep.findPlug(plugName, networked)

    except RuntimeError as e:
        # We catch a string that findPlug can't resolve here.
        # Chances are the plug is a subplug of an array, a compound,
        #  or a nesting of a combination of both
        cleanUpDummy = False
        dummy = None
        compoundSplit = plugName.split(".")  # any compounding will be dot delimited
        currPlug = None
        firstRun = False
        for token in compoundSplit:  # for each subPlug, even if just one, in the path
            aIndex = None
            # mutate token and store index if it's an array plug
            if token[-1] == "]":
                trimPoint = token.rfind("[") + 1
                aIndex = int(token[trimPoint:-1])
                token = token[: trimPoint - 1]

            if currPlug is None:  # first traversal
                try:
                    currPlug = dep.findPlug(
                        token, False
                    )  # this covers compound or head of array
                except RuntimeError as err:
                    if not relaxed:
                        logger.error("Cannot find plug: %s", token)
                        logger.error(err)
                        return om2.MPlug()  # early escape
                firstRun = True

            if aIndex is not None:  # if it's an array plug...
                if currPlug is None or currPlug.isNull:
                    if relaxed:
                        logger.warning(
                            "Error finding currPlug on plug: %s, root token %s not found on node %s",
                            plugName,
                            token,
                            dep.name(),
                        )
                        return om2.MPlug()

                    raise RuntimeError(
                        f"findplug failed in finding array entry for plugname {plugName}"
                    ) from e

                if (
                    aIndex != 0
                    and aIndex not in currPlug.getExistingArrayAttributeIndices()
                ):
                    if not relaxed:
                        raise _exceptions.PlugArrayOutOfBounds(
                            f"plug {plugName} was queried for unavailable index {aIndex} on node {dep.name()}"
                        ) from e

                    dummy = createAttributeDummy()
                    cleanUpDummy = True
                    if dummy is not None:
                        currPlug = getOrExtendMPlugArray(currPlug, aIndex, dummy)
                else:
                    currPlug = currPlug.elementByLogicalIndex(aIndex)

            if not firstRun and currPlug.isCompound:
                # We care for compounding only when we get to some level where it's not
                #  an Array any longer, otherwise arrays of compounds would always overextend and fail
                currPlug = findSubplugByName(currPlug, token)
            else:
                firstRun = False

        if cleanUpDummy:
            dg_mod = om2.MDGModifier()
            dg_mod.deleteNode(dummy)
            dg_mod.doIt()
        # This section emulates Maya's "isNetworked" flag in findPlug()
        if not networked:
            return currPlug

        # This should only ever be reached if a plug was found, and isNetworked is on
        #  which means we want to ensure that the plug is connected before we return it
        if currPlug and currPlug.isConnected:
            return currPlug

        # Plug exists, but isNetworked is on and the plug is disconnected
        return om2.MPlug()


def findPlug(plugName, node=None):
    """ Find the om2.MPlug by name (and node)

    It allows to pass either attribute name plus node om2.MObject
    or the full plug path without a node.

    Args:
        plugName (str): plug name or node.attr
        node(om2.MObject, optional): node of the plug, it is optional.

    Returns:
        om2.MPlug if found None otherwise
    """
    # most of time, MFnDependencyNode.findPlug() will work and be faster, but just
    # be aware of the behavior differences between the two:
    # 1. We need to check and return None for a plug whose node is invalid (e.g. deleted),
    #    as MFnDependencyNode.findPlug() will still return a valid plug even when the
    #    node has been removed, MSelectionList.getPlug() does the check for you.
    # 2. MSelectionList supports nodeName.plugName notion, even with [] or . for array element
    #    plug or child plug full path, MFnDependencyNode.findPlug() does not.
    # 3. MSelectionList always returns non-networked plug, while MFnDependencyNode.findPlug()
    #    depends on the argument you passed in.
    # 4. MSelectionList.getPlug() will find a plug on a child shape node if such plug does not
    #    exist on a transform, when you passed in "transformNodeName.shapeAttrName", which
    #    doesn't sound right but client code might expect that behavior.

    if node and not node.isNull() and om2.MObjectHandle(node).isValid():
        fnDep = om2.MFnDependencyNode(node)
        # Avoid processing child plug full path, array element, or plug on child shape.
        if fnDep.hasAttribute(plugName):
            try:
                # We need to use non-network plug as you can never know if the plug
                # will be disconnected later.
                plug = fnDep.findPlug(plugName, False)
                return None if plug.isNull else plug

            except Exception:
                return _findPlugOnNodeInternal(node, plugName, relaxed=True)

    # Then we deal with complex plug path, e.g. compound.child, array[index], etc.
    if node:
        if node.hasFn(om2.MFn.kDagNode):
            nodeName = om2.MFnDagNode(node).fullPathName()
        else:
            nodeName = om2.MFnDependencyNode(node).absoluteName()
        plugName = f"{nodeName}.{plugName}"

    # to avoid expensive check for existence, wrap with try except...
    # A cmds.objExists() test will return True for duplicate-named nodes, but it will
    # still raise run-time error when you add them to om2.MSelectionList.
    sl = om2.MSelectionList()
    try:
        sl.add(plugName)
    except RuntimeError as e:
        logger.debug("Plug: %r does not exist. \n%s", plugName, e)
        return None

    if sl.length() == 1:
        try:
            plug = sl.getPlug(0)
        except TypeError:
            # The following is a workaround for a bug in MSelectionList.getPlug()
            # We reported it in Nov 2019 and can remove this as soon as a patch is released.
            # To reproduce it, do a 'getPlug()' on 'someJoint.rotatePivot' for example.
            # or on 'someCurveShape.cp[0]'
            if not node:
                node = sl.getDependNode(0)
            fnDep = om2.MFnDependencyNode(node)
            plugNameOnly = plugName[plugName.find(".") + 1 :]
            try:
                plug = fnDep.findPlug(plugNameOnly, True)
            except Exception:
                if cmds.objExists(plugName):
                    # we should never end up here...
                    logger.debug(
                        """
                    We should not end up here.
                    This is a bug a plug that refuses to be found using
                    MSelectionList.getPlug() or MFnDependencyNode.findPlug()
                    PlugName: %s
                    """,
                        plugName,
                    )
                    plug = _findPlugOnNodeInternal(node, plugName, relaxed=True)
                else:
                    return None

        if not plug.isNull:
            return plug

        logger.error('Plug: "%s" is Null.', plugName)

    elif sl.length() > 1:
        logger.error('Plug: "%s" is not unique.', plugName)

    return None


def plugIsValid(plug):
    """Checks for plug validity working around various Maya issues. See notes.

    Notes:
       Courtesy of Maya having issues when a plug;
       - can be obtained that is fully formed
       - responds to methods such as isCompound, isElement etc. 
       - also respond negatively to isNull BUT actually has an uninitialized array in its stream and will
       therefore hard crash if queried for anything relating to its array properties such as numElements etc.

    Args:
        plug (om2.MPlug): The plug to do validity check.
    
    Returns:
        bool: True if it is a valid plug, False otherwise.
    """
    if (not plug) or plug.isNull:
        return False

    if plug.isChild:
        return plugIsValid(plug.parent())

    if not plug.isElement:
        return True

    if plug.logicalIndex() == -1:  # kInvalidIndex:
        return False

    return plugIsValid(plug.array())


def plugEnumNames(plug):
    """Get enum name list from an enum plug, None otherwise.

    Args:
        plug (om2.MPlug): the enum plug to get the enum name list.
    
    Returns:
        tuple | None: A tuple of enum names, None if failed.
    """
    if not plugIsValid(plug):
        return None

    attrType, fn = attributeTypeAndFnFromPlug(plug)
    if attrType == om2.MFn.kEnumAttribute:
        return tuple([fn.fieldName(i) for i in range(fn.getMin(), fn.getMax() + 1)])

    return None


def nextAvailableElementIndex(plug):
    """Get the next available element index that does not exist yet.

    Args:
        plug (om2.MPlug): the array plug to get the index for.
    
    Returns:
        int: the next available element index, -1 if failed.
    """
    if not plugIsValid(plug) or not plug.isArray:
        return -1

    indices = plug.getExistingArrayAttributeIndices()
    idx = max(indices) + 1 if indices else 0
    idx = [i for i in range(idx + 1) if i not in indices][0]
    return idx


def nextAvailableElement(plug):
    """Get the next available element plug that does not exist yet.

    Args:
        plug (om2.MPlug): the array plug to get the element plug for.
    
    Returns:
        om2.MPlug: the next available element plug, or null plug if failed.
    """
    idx = nextAvailableElementIndex(plug)
    return plug.elementByLogicalIndex(idx)


def _plugLockElision(f):
    """ Internal use only. It is a decorator to enable functions operating on plugs as 
    first argument or plug keyed argument to elide eventual locks present on the plug

    Args:
        f (function): the python function to wrap.

    Notes:
        This requires the functor getting decorated has a argument call "plug" and "_wasLocked".

    Examples:
        @_plugLockElision
        def someFunction(plug, ...)
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        plug = kwargs.get("plug", args[0])
        isValidPlug = plugIsValid(plug)
        if isValidPlug:
            restoreLocked = plug.isLocked
            plug.isLocked = False
        else:
            restoreLocked = False
            logger.warning(
                "Invalid plug: %s. Skipping plug unlocking for %s", plug, f.__name__
            )

        result = f(*args, _wasLocked=restoreLocked, **kwargs)

        if isValidPlug:
            plug.isLocked = restoreLocked

        return result

    return wrapper


_ATTRIBUTE_MFUNCTORS_BY_TYPE = {
    om2.MFn.kNumericAttribute: om2.MFnNumericAttribute,
    om2.MFn.kUnitAttribute: om2.MFnUnitAttribute,
    om2.MFn.kEnumAttribute: om2.MFnEnumAttribute,
    om2.MFn.kTypedAttribute: om2.MFnTypedAttribute,
    om2.MFn.kMatrixAttribute: om2.MFnMatrixAttribute,
    om2.MFn.kMessageAttribute: om2.MFnMessageAttribute,
    om2.MFn.kCompoundAttribute: om2.MFnCompoundAttribute,
    om2.MFn.kGenericAttribute: om2.MFnGenericAttribute,
    om2.MFn.kLightDataAttribute: om2.MFnLightDataAttribute,
}


def iterAttributeFnTypesAndClasses():
    """Iter through all the attribute MFn types and its MFn*Attribute classes.
    """
    for fnType, fnCls in _ATTRIBUTE_MFUNCTORS_BY_TYPE.items():
        yield fnType, fnCls


def attributeTypeAndFnFromPlug(plug):
    """Get the attribute type and MFn*Attribute class for the plug.

    Args:
        plug (om2.MPlug): The plug to query type and attribute functor for.

    Returns:
        om2.MFn.*, om2.MFn*Attribute.
    """
    attr = plug.attribute()

    retFn = None
    retType = om2.MFn.kAttribute
    for attrType, fn in iterAttributeFnTypesAndClasses():
        if attr.hasFn(attrType):
            retFn = fn(attr)
            retType = attrType
            break
    if retFn is None:
        retFn = om2.MFnAttribute(attr)

    return retType, retFn


def valueFromPlug(
    plug,
    context=om2.MDGContext.kNormal,
    faultTolerant=True,
    flattenComplexData=True,
    returnNoneOnMsgPlug=False,
    asDegrees=False,
):
    """Get the value of the plug.

    Args:
        plug (om2.MPlug): The plug to get the value from.

        context (om2.MDGContext, optional): The DG context to get the value for.

        faultTolerant (bool, optional): Whether to raise on errors or proceed silently

        flattenComplexData (bool, optional): Whether to convert MMatrix to list of doubles

        returnNoneOnMsgPlug (bool, optional): Whether we return None on message plug or the plug itself.

        asDegrees (bool, optional): For an angle unit attribute we return the value in degrees
            or in radians.

    Returns:
        om2.MFn.*, om2.MFn*Attribute.
    """
    if plug.isArray:
        numElem = plug.evaluateNumElements()
        indices = plug.getExistingArrayAttributeIndices()
        arrLength = 1 + max(indices) if indices else numElem
        arr = [None] * arrLength
        for i in plug.getExistingArrayAttributeIndices():
            arr[i] = valueFromPlug(
                plug.elementByLogicalIndex(i),
                context=context,
                faultTolerant=faultTolerant,
                flattenComplexData=flattenComplexData,
                returnNoneOnMsgPlug=returnNoneOnMsgPlug,
                asDegrees=asDegrees,
            )
        return arr

    if plug.isCompound:
        serialiseAsDict = True
        if plug.attribute().hasFn(om2.MFn.kNumericAttribute):
            attrFn = om2.MFnNumericAttribute(plug.attribute())
            if attrFn.numericType() != om2.MFnNumericData.kInvalid:
                serialiseAsDict = False

        childPlugs = (plug.child(i) for i in range(plug.numChildren()))
        if serialiseAsDict:
            return {
                om2.MFnAttribute(childPlug.attribute()).name: valueFromPlug(
                    childPlug,
                    context=context,
                    faultTolerant=faultTolerant,
                    flattenComplexData=flattenComplexData,
                    returnNoneOnMsgPlug=returnNoneOnMsgPlug,
                    asDegrees=asDegrees,
                )
                for childPlug in childPlugs
            }

        return [
            valueFromPlug(
                childPlug,
                context=context,
                faultTolerant=faultTolerant,
                flattenComplexData=flattenComplexData,
                returnNoneOnMsgPlug=returnNoneOnMsgPlug,
                asDegrees=asDegrees,
            )
            for childPlug in childPlugs
        ]

    if plug.attribute().hasFn(om2.MFn.kMessageAttribute) and returnNoneOnMsgPlug:
        return None

    valAndTypes = valueAndTypesFromPlug(
        plug,
        context=context,
        faultTolerant=faultTolerant,
        flattenComplexData=flattenComplexData,
        asDegrees=asDegrees,
    )

    if isinstance(valAndTypes, tuple) and len(valAndTypes) == 3:
        val, _, _ = valAndTypes
        return val

    return None


def __num_as_float(t):
    """Internal use only, solely meant for code compression
    """
    return t in (om2.MFnNumericData.kFloat, om2.MFnNumericData.kDouble)


def __num_as_int(t):
    """Internal use only, solely meant for code compression
    """
    # in order of likelyhood/speed centric
    return (
        t == om2.MFnNumericData.kInt
        or (om2.MFnNumericData.kByte <= t <= om2.MFnNumericData.kShort)
        or t == om2.MFnNumericData.kLong
        or t == om2.MFnNumericData.kInt64
        or t == om2.MFnNumericData.kAddr
    )


def nodeDotAttrFromPlug(plug):
    """Return nodeName.attribute str representation of the plug.

    Notes:
        plug.partialName() will not give you a unique nodeName.attribute if the
            node is duplicatly named.

    Args:
        plug (om2.MPlug): A Maya MPlug

    Returns:
        str: the nodePartialPathName.attribute
    """
    if not plug or plug.isNull:
        return None

    node = plug.node()
    if node.hasFn(om2.MFn.kDagNode):
        nodename = om2.MFnDagNode(node).partialPathName()
    else:
        nodename = om2.MFnDependencyNode(node).name()

    attrName = plug.partialName(includeNodeName=False, useFullAttributePath=True)
    return f"{nodename}.{attrName}"


def valueAndTypesFromPlug(
    plug,
    context=om2.MDGContext.kNormal,
    exclusionPredicate=lambda x: False,
    inclusionPredicate=lambda x: True,
    faultTolerant=True,
    flattenComplexData=True,
    asDegrees=False,
):
    """Retrieves the value, attribute functor type, and attribute type per functor for any given plug.

    Args:
        plug (om2.MPlug): A maya type plug of any description

        context (om2.MDGContext, optional): The maya context to retrieve the plug at. This isn't always applicable,
            and w indicate so in the switches when it's not, but it's always accepted
            When a context isn't passed the default is kNormal, which is current
            context at current time.

        exclusionPredicate (function, optional): Predicated on the attribute functor internal to the function
            this enables us to filter by an internal which preceeds the plug check stages, enabling things
            such as early filtering of hidden attributes or factory ones etc.

        inclusionPredicate (function, optional): Predicated on the attribute functor internal to the function
            this enables us to filter by an internal which preceeds the plug check stages, enabling things
            such as early filtering by specific attribute functor calls before choosing to opt in.

        faultTolerant (bool, optional): Whether to raise on errors or proceed silently.

        flattenComplexData (bool, optional): Whether to convert MMatrix to list of doubles.

        asDegrees (bool, optional): For an angle unit attribute we return the value in degrees
            or in radians.

    Returns:
        tuple | None: This will return None if it doesn't raise but is unable to read.
                        E.G. a predicate is off value or the plug is a compound.
                        If something of note is found it's returned
                        as a triplet of value, fnType, attrType, with value being potentially an MPlug

    Todo:
        Escalate faultTolerant to have levels for maya failures vs finer grained failures
    """
    t = None  # subtype that should be shadowed in most sub-scopes
    if not plugIsValid(plug):
        if faultTolerant:
            return None, 0, 0
        raise _exceptions.PlugMayaInvalidException(
            plug,
            "valueAndTypesFromPlug() failure in non fault tolerant mode, plug is most likely not value initialised",
        )

    attrType, fn = attributeTypeAndFnFromPlug(plug)
    if attrType == om2.MFn.kCompoundAttribute:
        if faultTolerant:
            return None, 0, 0
        raise _exceptions.PlugMayaInvalidException(
            plug,
            "valueAndTypesFromPlug() failure, nonFactory or nonUniformly typed compound type attribute",
        )

    logger.debug("Found attribute type %s", attrType)
    try:
        if exclusionPredicate(fn) or not inclusionPredicate(fn):
            return None, 0, 0
    except Exception as e:
        #        Yes, except all, but we want to catch every possible predicate error and indicate the predicate failed
        #          since it's all one should care about as they can very easily debug those predicates in isolation,
        #          and should in fact have ensured they didn't ever fail before using them
        raise _exceptions.PlugAttributePredicateError(plug) from e

    if plug.isArray:
        count = plug.evaluateNumElements()
        retVal = [None] * count
        # @note: Wwhile it might seem logical to return the types once, and only the data
        #         as an array, which is what the old beast utils one did, it's worth
        #         noting that there exists a rare case with typed attributes where
        #         you can have an array of mixed types, therefore to retain
        #         a universal signature and to make each granular
        #         return identical regardless of whether it comes from an array or not
        #         we choose to return an array of triples instead of a triplet with one
        #         array of values in it
        for i in range(count):
            retVal[i] = valueAndTypesFromPlug(
                plug.elementByLogicalIndex(i),
                context,
                faultTolerant=faultTolerant,
                flattenComplexData=flattenComplexData,
                asDegrees=asDegrees,
            )
        return retVal

    # ----------- NUMERIC -----------
    contextWarnMsg = "%s requested with non normal context, for Maya this info can't be provided, providing normal context instead for plug %s"
    if attrType == om2.MFn.kNumericAttribute:
        t = fn.numericType()
        if t == om2.MFnNumericData.kBoolean:
            return plug.asBool(), attrType, t

        if __num_as_float(t):
            return plug.asFloat(), attrType, t

        if __num_as_int(t):
            # @note this exception is necessary because
            #        maya has plenty factory plugs that are in and failing on geometry
            #        usually edges or faces
            try:
                return plug.asInt(), attrType, t
            except RuntimeError as e:
                if fn.hidden:
                    return None, attrType, t

                raise RuntimeError(
                    "maya error trying to retrieve flawed int plug that's not hidden"
                ) from e

        #        From this point on context is spottily supported, or not supported at all in Maya
        #          as well as crashy, so we don't forward it any longer
        if context != om2.MDGContext.kNormal:
            # @TODO: raise custom error if not fault tolerant
            logger.warning(contextWarnMsg, "aggregate numeric attribute", plug.name())

        dataHandle = plug.asMDataHandle()
        val = None
        if t == om2.MFnNumericData.k2Short:
            val = dataHandle.asShort2()
        elif t == om2.MFnNumericData.k3Short:
            val = dataHandle.asShort3()
        elif t == om2.MFnNumericData.k2Int:  # same as long
            val = dataHandle.asInt2()
        elif t == om2.MFnNumericData.k3Int:  # same as long
            val = dataHandle.asInt3()
        elif t == om2.MFnNumericData.k2Float:
            val = dataHandle.asFloat2()
        elif t == om2.MFnNumericData.k3Float:
            val = dataHandle.asFloat3()
        elif t == om2.MFnNumericData.k2Double:
            val = dataHandle.asDouble2()
        elif t == om2.MFnNumericData.k3Double:
            val = dataHandle.asDouble3()
        elif t == om2.MFnNumericData.k4Double:
            val = [None, None, None, None]
            childCount = plug.numChildren()
            #           Nullify exists to maintain consistency with all other cases where val should be None when
            #             unsupported or unrecognised. Because we need to form val before the loop we also need
            #             to ensure that it's restored to plain None were the range to be 0 for some reason,
            #             or we would be returning a deceiving structure and potentially lead to nasty and
            #             silent later failure in caller's code
            nullify = True
            for i in range(childCount):
                nullify = False
                currChildPlug = plug.child(i)
                val[i] = currChildPlug.asFloat()
            if nullify:
                val = None

        if val is None and not faultTolerant:
            raise _exceptions.PlugUnhandledTypeException(
                plug, attrType, t, "this seems to be an unhandled numeric attribute"
            )

        return val, attrType, t

    # ------------ UNIT -------------
    if attrType == om2.MFn.kUnitAttribute:
        t = fn.unitType()
        if t == om2.MFnUnitAttribute.kAngle:
            if not asDegrees:
                return plug.asMAngle().asRadians(), attrType, t

            return plug.asMAngle().asDegrees(), attrType, t

        if t == om2.MFnUnitAttribute.kDistance:
            return plug.asDouble(), attrType, t
        if t == om2.MFnUnitAttribute.kTime:
            return plug.asMTime().value, attrType, t

    # ----------- MATRIX ------------
    if attrType == om2.MFn.kMatrixAttribute:
        attrData = om2.MFnMatrixData(plug.asMObject()).matrix()
        if flattenComplexData:
            return [attrData[i] for i in range(len(attrData))], attrType, fn.kDouble
        return attrData, attrType, fn.kDouble

    if attrType == om2.MFn.kFloatMatrixAttribute:
        attrData = om2.MFnMatrixData(plug.asMObject()).matrix()
        if flattenComplexData:
            return [attrData[i] for i in range(len(attrData))], attrType, fn.kFloat
        return attrData, attrType, fn.kFloat

    # ------------ ENUM -------------
    if attrType == om2.MFn.kEnumAttribute:
        return plug.asShort(), attrType, 1

    # ----------- TYPED -------------
    if attrType == om2.MFn.kTypedAttribute:
        t = fn.attrType()
        logger.debug("Found typed attribute %s", t)
        if t == om2.MFnData.kString:  # string
            return plug.asString(), attrType, t
        if t == om2.MFnData.kStringArray:  # string array
            if context != om2.MDGContext.kNormal:
                # @TODO: raise custom error if not fault tolerant
                logger.warning(
                    contextWarnMsg, "typed attribute of type stringArray", plug.name()
                )
            dataHandle = plug.asMDataHandle()
            dataMob = dataHandle.data()
            if dataMob.isNull():
                # @TODO: should we maybe return None or something like that? Tricky
                #        empty list does make it more functional
                return [], attrType, t
            fnData = om2.MFnStringArrayData(dataHandle.data())
            return fnData.array(), attrType, t

        if t == om2.MFnData.kFloatArray:  # float array
            if context != om2.MDGContext.kNormal:
                # @TODO: raise custom error if not fault tolerant
                logger.warning(
                    contextWarnMsg, "typed attribute of type floatArray", plug.name()
                )

            # om2 has no way to get a floatArray value as MFnFloatArrayData is still missing in om2 ...
            # We have to use cmds here:
            attrPath = nodeDotAttrFromPlug(plug)
            return cmds.getAttr(attrPath), attrType, t

        if t == om2.MFnData.kIntArray:  # int array
            if context != om2.MDGContext.kNormal:
                logger.warning(
                    contextWarnMsg, "typed attribute of type intArray", plug.name()
                )
            dataHandle = plug.asMDataHandle()
            dataMob = dataHandle.data()
            if dataMob.isNull():
                # @TODO: should we maybe return None or something like that? Tricky
                #        empty list does make it more functional
                return [], attrType, t
            fnData = om2.MFnIntArrayData(dataHandle.data())
            arrayData = fnData.array()
            if flattenComplexData:
                return list(arrayData), attrType, t
            return arrayData, attrType, t
        if t == om2.MFnData.kDoubleArray:  # double array
            if context != om2.MDGContext.kNormal:
                # @TODO: raise custom error if not fault tolerant
                logger.warning(
                    contextWarnMsg, "typed attribute of type doubleArray", plug.name()
                )
            dataHandle = plug.asMDataHandle()
            dataMob = dataHandle.data()
            if dataMob.isNull():
                # @TODO: should we maybe return None or something like that? Tricky
                #        empty list does make it more functional
                return [], attrType, t
            fnData = om2.MFnDoubleArrayData(dataHandle.data())
            arrayData = fnData.array()
            if flattenComplexData:
                return list(arrayData), attrType, t
            return arrayData, attrType, t
        if t == om2.MFnData.kMatrix:  # matrix as list
            mtx = om2.MFnMatrixData(plug.asMObject()).matrix()
            if flattenComplexData:
                return list(mtx), attrType, t
            return mtx, attrType, t
        if t == om2.MFnData.kVectorArray:  # vector array
            #           This is an absolutely terrifying attribute.
            #           For performance reasons it will handle things around by reference.
            if context != om2.MDGContext.kNormal:
                # @TODO: raise custom error if not fault tolerant
                logger.warning(
                    contextWarnMsg, "typed attribute of type vectorArray", plug.name()
                )
            dataHandle = plug.asMDataHandle()
            dataMob = dataHandle.data()
            if dataMob.isNull():
                # @TODO: should we maybe return None or something like that? Tricky
                #        empty list does make it more functional
                return [], attrType, t
            fnData = om2.MFnVectorArrayData(dataHandle.data())
            #           There is a really tough decision being made here.
            #           Naturally the functor's data method returns a live reference to the MVectorArray
            #             that describe the data, which is supremely dangerous, but sensible given
            #             the cases such attributes are normally used in.
            #           A separate function will be provided to get this attribute as a live point array,
            #             and in here we choose to instead return a plain list of lists
            liveMayaArray = fnData.array()
            return [[p.x, p.y, p.z] for p in liveMayaArray], attrType, t
        if t == om2.MFnData.kPointArray:  # point array
            #           For performance reasons it will handle things around by reference.
            if context != om2.MDGContext.kNormal:
                # @TODO: raise custom error if not fault tolerant
                logger.warning(
                    contextWarnMsg, "typed attribute of type pointArray", plug.name()
                )
            dataHandle = plug.asMDataHandle()
            dataMob = dataHandle.data()
            if dataMob.isNull():
                # @TODO: should we maybe return None or something like that? Tricky
                #        empty list does make it more functional
                return [], attrType, t
            fnData = om2.MFnPointArrayData(dataHandle.data())
            #           There is a really tough decision being made here.
            #           Naturally the functor's data method returns a live reference to the MPointArray
            #             that describe the data, which is supremely dangerous, but sensible given
            #             the cases such attributes are normally used in.
            #           A separate function will be provided to get this attribute as a live point array,
            #             and in here we choose to instead return a plain list of lists
            liveMayaArray = fnData.array()
            return [[p.x, p.y, p.z, p.w] for p in liveMayaArray], attrType, t

        # ------ invalid ------
        if t == om2.MFnData.kInvalid:
            if faultTolerant:
                return None, attrType, t
            # @todo: replace with custom exception as well as re-implement
            #         once fault tolerance becomes a scaling argument instead
            #         of a boolean.
            raise RuntimeError("attempted to fetch invalid data type")

        # ------ everything else ------
        # unhandled types such as lattice, geo sources etc.
        return om2.MPlug().copy(plug), attrType, 1

    # ----------- MESSAGE -----------
    if attrType == om2.MFn.kMessageAttribute:
        # @todo: Do we want to return the plug itself when it's actually a message?
        #        The only real use for a message is its connections usually,
        #         which means this would make good sense, but this might affect use as serialisation
        #
        return om2.MPlug().copy(plug), attrType, 1

    # ----------- GENERIC -----------
    if attrType == om2.MFn.kGenericAttribute:
        # For the unitConversion.input/unitConversion.output plug, it is generic attribute.
        # So here we have to use cmds...
        value = cmds.getAttr(plug.partialName(includeNodeName=True))
        return value, attrType, -1

    raise _exceptions.PlugUnhandledTypeException(plug, attrType, t)


@_plugLockElision
def setValueOnPlug(
    plug,
    value,
    elideLock=False,
    exclusionPredicate=lambda x: False,
    inclusionPredicate=lambda x: True,
    faultTolerant=True,
    _wasLocked=False,
    modifier=None,
    doIt=True,
    asDegrees=False,
):
    """Set plug value using a modifier.

    Args:
        plug (om2.MPlug): The plug to set to the specified value contained in the following argument.

        value (any): the value to set the plug to

        elideLock (bool, optional): Whether we unlock the plug (only) during value setting.

        exclusionPredicate (function, optional): See valueAndTypesFromPlug

        inclusionPredicate (function, optional): See valueAndTypesFromPlug

        faultTolerant (bool, optional): Whether to raise on errors or proceed silently

        _wasLocked (bool, optional): internal use only, this is required for plugLock eliding
            functions to play nice with elision conditions, since the decorator
            will always run first and unlock the plug, and therefore has to be
            able to signal the wrapped function of the previous state of the plug
            for both the check AND restoration of the lock before an eventual exception

        modifier (om2.MDGModifier, optional): to support modifier for undo/redo purpose.

        doIt (bool, optional): True means modifier.doIt() will be called immediately to apply the plug value change.
            False enable you to defer and call modifier.doIt() later in one go.

        asDegrees (bool, optional): When it is an angle unit attribute, if this is True than we take the 
            value as degrees, otherwise as radians. This flag has no effect
            when it is not an angle unit attribute.

    Returns: 
        None if for whatever reason the operation is invalid or has effected no change
        Otherwise it will return the original value (so it can be stored for undo support).
        Normally the pattern would be None as invalid op, False for no change,
        and True for change affected, but given the previous value for a boolean
        attribute could reasonably be False as a value we have to use None for both
        invalid as well as ineffective, and rely on the user to invoke the call
        as non fault tolerant and catching specific exceptions for no-change

    Todo: 
        In support of the last note in the return description we need fine grained exceptions
        to enable this function to act in a ternary fashion
    """
    logger.debug("setValueOnPlug(plug=%s, value=%s, doIt=%s)", plug, value, doIt)
    if not plugIsValid(plug):
        if faultTolerant:
            return None
        raise _exceptions.PlugMayaInvalidException(
            plug,
            "invalid plug found before trying to set value on it from setValueOnPlug",
        )

    if not elideLock and _wasLocked:
        if faultTolerant:
            return None

        raise _exceptions.PlugLockedForEditError(plug)

    attrType, fn = attributeTypeAndFnFromPlug(plug)
    if exclusionPredicate(fn) or not inclusionPredicate(fn):
        return None

    if not modifier:
        modifier = om2.MDGModifier()
        doIt = True

    if (plug.isArray or plug.isCompound) and isinstance(
        value, (list, tuple, om2.MVector, om2.MFloatArray, om2.MDoubleArray)
    ):
        if plug.isArray:
            count = len(value)
        else:
            count = plug.numChildren()
            if count < len(value):
                if faultTolerant:
                    return None
                raise RuntimeError(
                    "value is a sequence of length different than the length of the array / compound children length of the plug it's trying to be set on"
                )

        for i in range(count):
            if plug.isArray:
                if value[i] is None:
                    continue

                childPlug = plug.elementByLogicalIndex(i)
            else:
                childPlug = plug.child(i)

            setValueOnPlug(
                childPlug,
                value[i],
                elideLock,
                exclusionPredicate,
                inclusionPredicate,
                faultTolerant,
                modifier=modifier,
                doIt=False,
            )

        if doIt:
            modifier.doIt()

        # @todo: return original values list
        return []

    if plug.isArray and isinstance(value, dict):
        for index, elemVal in value.items():
            if not isinstance(index, int):
                try:
                    index = int(index)
                except ValueError as e:
                    if faultTolerant:
                        return None

                    raise RuntimeError("Non numerical array index") from e

            childPlug = plug.elementByLogicalIndex(index)
            setValueOnPlug(
                childPlug,
                elemVal,
                elideLock,
                exclusionPredicate,
                inclusionPredicate,
                faultTolerant,
                modifier=modifier,
                doIt=False,
            )

        if doIt:
            modifier.doIt()

        return []

    if plug.isArray:
        if faultTolerant:
            return None

        raise RuntimeError("Unable to set scalar value on array plug")

    if plug.isCompound and isinstance(value, dict):
        depFn = om2.MFnDependencyNode(plug.node())
        childPlugMap = {}
        for i in range(plug.numChildren()):
            childPlug = plug.child(i)
            alias = depFn.plugsAlias(childPlug)
            if alias:
                childPlugMap[alias] = childPlug

            attrFn = om2.MFnAttribute(childPlug.attribute())
            childPlugMap[attrFn.shortName] = childPlug
            childPlugMap[attrFn.name] = childPlug
            childPlugMap[i] = childPlug
            childPlugMap[str(i)] = childPlug

        for key, childValue in value.items():
            if key not in childPlugMap:
                if faultTolerant:
                    return None

                raise RuntimeError(f"Child plug {key} not found in plug {plug.name}")

            setValueOnPlug(
                childPlugMap[key],
                childValue,
                elideLock,
                exclusionPredicate,
                inclusionPredicate,
                faultTolerant,
                modifier=modifier,
                doIt=False,
            )

        if doIt:
            modifier.doIt()

        return []

    def _setValueWith(setter, previousValue, targetValue, extraConversion=lambda x: x):
        if previousValue is None or previousValue != targetValue:
            setter(plug, extraConversion(targetValue))
            if doIt:
                modifier.doIt()
            return previousValue

        logger.debug("Current value for %s already set to %s", plug, targetValue)
        if faultTolerant:
            return previousValue

        return None

    # ----------- NUMERIC -----------
    if attrType == om2.MFn.kNumericAttribute:
        t = fn.numericType()
        # For numeric value, we still do explicit coversion below, in case some rig updates
        # end in attribute type changes, which will cause an unnecessary exception here.
        if t == om2.MFnNumericData.kBoolean:
            prevVal = plug.asBool()
            return _setValueWith(modifier.newPlugValueBool, prevVal, bool(value))
        if __num_as_float(t):
            prevVal = plug.asFloat()
            return _setValueWith(modifier.newPlugValueFloat, prevVal, float(value))
        if __num_as_int(t):
            prevVal = plug.asInt()
            return _setValueWith(modifier.newPlugValueInt, prevVal, int(value))
        if t <= om2.MFnNumericData.kInvalid or t >= om2.MFnNumericData.kLast:
            if faultTolerant:
                return None

            raise RuntimeError("invalid data type")
        # @TODO impelement set for multiples

    # ------------ UNIT -------------
    if attrType == om2.MFn.kUnitAttribute:
        t = fn.unitType()
        if t == om2.MFnUnitAttribute.kAngle:
            if not asDegrees:
                prevVal = plug.asMAngle().asRadians()
                conversion = lambda x: om2.MAngle(x, om2.MAngle.kRadians)
            else:
                prevVal = plug.asMAngle().asDegrees()
                conversion = lambda x: om2.MAngle(x, om2.MAngle.kDegrees)

            return _setValueWith(
                modifier.newPlugValueMAngle, prevVal, value, conversion
            )

        if t == om2.MFnUnitAttribute.kDistance:
            prevVal = plug.asDouble()
            return _setValueWith(modifier.newPlugValueDouble, prevVal, value)

        if t == om2.MFnUnitAttribute.kTime:
            prevVal = plug.asMTime().value
            return _setValueWith(modifier.newPlugValueMTime, prevVal, value, om2.MTime)

        return None

    # ----------- MATRIX ------------
    if attrType == om2.MFn.kMatrixAttribute:
        if hasattr(value, "__iter__"):
            mtxVal = om2.MMatrix(value)
        elif isinstance(value, (om2.MMatrix, om2.MFloatMatrix)):
            mtxVal = om2.MMatrix(value)
        else:
            if faultTolerant:
                # @todo: log warning or something?!
                return None
            raise TypeError("unsupported value type passed to setValueOnPlug")

        prevVal = om2.MFnMatrixData(plug.asMObject()).matrix()
        conversion = lambda x: om2.MFnMatrixData().create(x)
        return _setValueWith(modifier.newPlugValue, prevVal, mtxVal, conversion)

    # ------------ ENUM -------------
    if attrType == om2.MFn.kEnumAttribute:
        prevVal = plug.asShort()
        if isinstance(value, str):
            # Find the index from the string value
            validNames = plugEnumNames(plug)
            if value in validNames:
                value = validNames.index(value)
            else:
                raise ValueError(
                    f"Invalid enum name '{value}' for plug {plug}, valid enum names are {validNames}."
                )

        return _setValueWith(modifier.newPlugValueShort, prevVal, value)

    # ----------- TYPED -------------
    if attrType == om2.MFn.kTypedAttribute:
        t = fn.attrType()
        if t == om2.MFnData.kString:
            prevVal = plug.asString()
            return _setValueWith(modifier.newPlugValueString, prevVal, value)
        if t == om2.MFnData.kMatrix:
            if hasattr(value, "__iter__"):
                mtxVal = om2.MMatrix(value)
            elif isinstance(value, (om2.MMatrix, om2.MFloatMatrix)):
                mtxVal = om2.MMatrix(value)
            else:
                if faultTolerant:
                    # @todo: log warning or something?!
                    return None

                raise TypeError("unsupported value type passed to setValueOnPlug")

            prevVal = plug.asMDataHandle().asMatrix()
            conversion = lambda x: om2.MFnMatrixData().create(x)
            return _setValueWith(modifier.newPlugValue, prevVal, mtxVal, conversion)
            # @todo return as list for alignment with rest of methods?

        # ----- array cases -----
        fnData = None
        if t == om2.MFnData.kStringArray:
            fnData = om2.MFnStringArrayData()
        elif t == om2.MFnData.kIntArray:
            fnData = om2.MFnIntArrayData()
        elif t == om2.MFnData.kDoubleArray:
            fnData = om2.MFnIntArrayData()
        elif t == om2.MFnData.kVectorArray:
            fnData = om2.MFnVectorArrayData()
        elif t == om2.MFnData.kPointArray:
            fnData = om2.MFnPointArrayData()
        elif t == om2.MFnData.kMatrixArray:
            fnData = om2.MFnMatrixArrayData()

        # @todo: implement value diffing like for all other cases
        attrData = fnData.create(value) if fnData is not None else None
        if _setValueWith(modifier.newPlugValue, None, attrData):
            return []  # @todo: implement proper  populated list return for array types

        # ----- maya invalid -----
        if t == om2.MFnData.kInvalid:
            if faultTolerant:
                return None
            raise RuntimeError(
                "invalid plug type, like, literally kInvalid!"
            )  # @todo: better message and error

    # @todo: Message and generic remain unaddressed for now.
    #        Generic can be tricky and require graph inspection to implement properly.
    #        Message is kind of unlikely to have a meaningful implementation that
    #         doesn't simply become some confusing ulterior connect-plug
    return None
