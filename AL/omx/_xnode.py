# Copyright (C) Animal Logic Pty Ltd. All rights reserved.

import logging
from maya.api import OpenMaya as om2

from AL.maya2.omx import _xplug
from AL.maya2.omx.utils import _nodes
from AL.maya2.omx.utils import _plugs

logger = logging.getLogger(__name__)


class XNode:
    """ Easy wrapper around om2 objects mainly to access plugs"

    Example:
        This shows how to use omx to connect 2 nodes::

            from AL.maya2 import omx

            trn = omx.createDagNode("transform", nodeName="myTrn")
            mtx = trn.worldMatrix[0].value()

            reparent = omx.createDGNode("AL_rig_reparentSingle")
            reparent.worldMatrix.connect(trn.worldMatrix[0])
    """

    _NODE_CLASS_CACHE = {}
    _ATTRIBUTE_CACHE = {}

    def __init__(self, thingToEasify):
        """ Creates a new XNode

        Args:
            thingToEasify (:py:class:`om2.MObject` | :py:class:`XNode` | :py:class:`om2.MFnBase` | string): A maya object to wrap

        Returns:
            :py:class:`omx.XNode`: An instance of a XNode object
        """
        if isinstance(thingToEasify, om2.MObject):
            mob = thingToEasify
        elif isinstance(thingToEasify, om2.MObjectHandle):
            mob = thingToEasify.object()
        elif isinstance(thingToEasify, XNode):
            mob = thingToEasify.object()
        elif isinstance(thingToEasify, om2.MFnBase):
            mob = thingToEasify.object()
        elif isinstance(thingToEasify, om2.MDagPath):
            mob = thingToEasify.node()
        elif isinstance(thingToEasify, str):
            mob = _nodes.findNode(thingToEasify)
            if mob is None:
                raise RuntimeError(f"Object {thingToEasify} is not valid!")

        else:
            raise RuntimeError(f"Cannot use {thingToEasify} with XNode!")

        if mob != om2.MObject.kNullObj and not mob.hasFn(om2.MFn.kDependencyNode):
            raise RuntimeError(
                "Cannot use XNode on an object that is not a DependencyNode!"
            )

        self._mobHandle = om2.MObjectHandle(mob)
        depNode = om2.MFnDependencyNode(mob)
        self._lastKnownName = depNode.absoluteName()
        self._mayaType = mayaType = depNode.typeName
        nodeCls = XNode._NODE_CLASS_CACHE.get(mayaType, None)
        if nodeCls is None:
            nodeCls = om2.MNodeClass(mayaType)
            XNode._NODE_CLASS_CACHE[mayaType] = nodeCls
            XNode._ATTRIBUTE_CACHE[mayaType] = {}

    def __getattribute__(self, name):
        # Normal attributes (such as methods) are handled here
        if hasattr(XNode, name):
            return object.__getattribute__(self, name)

        mob = object.__getattribute__(self, "object")()

        # We expose the MObject.apiTypeStr property here
        if name == "apiTypeStr":
            return mob.apiTypeStr

        if mob == om2.MObject.kNullObj:
            lastName = object.__getattribute__(self, "_lastKnownName")
            raise RuntimeError(f"XNode({lastName}) associated MObject is null!")
        mayaType = object.__getattribute__(self, "_mayaType")

        nodeClass = XNode._NODE_CLASS_CACHE[mayaType]
        attrs = XNode._ATTRIBUTE_CACHE[mayaType]
        attr = attrs.get(name, None)
        if attr is None:
            if not nodeClass.hasAttribute(name):
                plug = _plugs.findPlug(name, mob)
                if plug:
                    return _xplug.XPlug(plug)

                raise AttributeError(f"Node {mayaType} has no attribute called {name}")

            attr = nodeClass.attribute(name)
            attrs[name] = attr
        return _xplug.XPlug(mob, attr)

    def object(self):
        """Returns the associated MObject

        Returns:
            :py:class:`om2.MObject`: the associated MObject
        """
        mobHandle = object.__getattribute__(self, "_mobHandle")
        if not mobHandle.isAlive():
            lastName = object.__getattribute__(self, "_lastKnownName")
            raise RuntimeError(f"XNode({lastName}) is not alive!")

        if not mobHandle.isValid():
            lastName = object.__getattribute__(self, "_lastKnownName")
            raise RuntimeError(f"XNode({lastName}) is not valid!")

        mob = mobHandle.object()
        return mob

    def isAlive(self):
        """Returns the live state of the current MObject associated with this XNode.
        An object can still be 'alive' but not 'valid'
        (eg. a deleted object that resides in the undo queue).

        Returns:
            bool: the live state
        """
        return object.__getattribute__(self, "_mobHandle").isAlive()

    def isValid(self):
        """Returns the validity of the current MObject associated with this XNode.

        Returns:
            bool: the valid state
        """
        return object.__getattribute__(self, "_mobHandle").isValid()

    def isNull(self):
        """Tests whether there is an internal Maya object.

        Returns:
            bool: Returns True if the MObject is not referring to any Maya internal internal object (i.e. it is equivalent to kNullObj).
        """
        return self.object().isNull()

    def apiType(self):
        """Returns the function set type for the object.

        Returns:
            `om2.MFn`: Returns a constant indicating the type of the internal Maya object. If the MObject is null MFn.kInvalid will be returned.
        """
        return self.object().apiType()

    def hasFn(self, fn):
        """Tests whether object is compatible with the specified function set.

        Args:
            fn (`om2.MFn`): MFn type constant

        Returns:
            bool: Returns True if the internal Maya object supports the specified function set specified by fn.
        """
        return self.object().hasFn(fn)

    def createDagNode(self, typeName, nodeName=""):
        """Creates a child DAG node on the current node if possible.

        Adds an operation to the modifier to create a DAG node of the specified type. If a parent DAG node is provided the new node will be parented under it.
        If no parent is provided and the new DAG node is a transform type then it will be parented under the world. In both of these cases the method returns
        the new DAG node.

        If no parent is provided and the new DAG node is not a transform type then a transform node will be created and the child parented under that.
        The new transform will be parented under the world and it is the transform node which will be returned by the method, not the child.

        None of the newly created nodes will be added to the DAG until the modifier's doIt() method is called.

        Raises:
            :class:`TypeError` if the node type does not exist or if the parent is not a transform type.

        Args:
            typeName (string): the type of the object to create, e.g. "transform"
            nodeName (str, optional): the node name, if non empty will be used in a modifier.renameObject call. Defaults to "".

        Returns:
            :class:`xnode.XNode`: An xnode.XNode instance around the created MObject.
        """
        mob = self.object()
        if not mob.hasFn(om2.MFn.kDagNode):
            raise TypeError(
                f"Cannot create a DAG node {nodeName}[{typeName}] under this non-DAG node {self}"
            )

        from AL.maya2.omx import _xmodifier

        return _xmodifier.createDagNode(typeName, parent=mob, nodeName=nodeName)

    def bestFn(self):
        """Returns the best MFn function set for the associated MObject

        Raises:
            RuntimeError: if no MFn is found for the wrapped MObject

        Returns:
            om2.MFn*: the best MFn object for this MObject (usually a :class:`om2.MFnTransform` or a :class:`om2.MFnDependencyNode`)
        """
        mob = self.object()
        fnList = reversed(om2.MGlobal.getFunctionSetList(mob))
        for k in fnList:
            om2Type = getattr(om2, "MFn" + k[1:], None)
            if om2Type:
                return om2Type(mob)
        raise RuntimeError(f"No best Fn found for {self}")

    def basicFn(self):
        """Returns the basic MFnDAGNode or MFnDependencyNode for the associated MObject

        Notes:
            Usually you would use xnode.bestFn() to get the most useful function set. But for an empty NURBS curve
            or an empty mesh node, only xnode.basicFn() will work as expected.

        Returns:
            om2.MFnDagNode | om2.MFnDependencyNode: For a DAG node or a DG node respectively.
        """
        mob = self.object()
        if mob.hasFn(om2.MFn.kDagNode):
            return om2.MFnDagNode(mob)

        return om2.MFnDependencyNode(mob)

    def __str__(self):
        mobHandle = object.__getattribute__(self, "_mobHandle")
        if not mobHandle.isAlive():
            lastName = object.__getattribute__(self, "_lastKnownName")
            return f"{lastName}(dead)"

        if not mobHandle.isValid():
            lastName = object.__getattribute__(self, "_lastKnownName")
            return f"{lastName}(invalid)"

        mob = mobHandle.object()
        if mob.hasFn(om2.MFn.kDagNode):
            return om2.MFnDagNode(mob).partialPathName()

        if mob.hasFn(om2.MFn.kDependencyNode):
            return om2.MFnDependencyNode(mob).name()

        return "None"

    def __repr__(self):
        return f'XNode("{self}")'

    def __eq__(self, other):
        """Add support for XNode comparison.
        """
        if isinstance(other, XNode):
            return self.object().__eq__(other.object())

        if isinstance(other, om2.MObject):
            return self.object().__eq__(other)

        return False

    def __ne__(self, other):
        if isinstance(other, XNode):
            return self.object().__ne__(other.object())

        if isinstance(other, om2.MObject):
            return self.object().__ne__(other)

        return True

    def __hash__(self):
        return object.__getattribute__(self, "_mobHandle").hashCode()
