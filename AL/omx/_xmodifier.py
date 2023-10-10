# Copyright (C) Animal Logic Pty Ltd. All rights reserved.

import inspect
import contextlib
import warnings
import sys
import logging
from functools import wraps

from maya import cmds
from maya.api import OpenMaya as om2
from maya.api import OpenMayaAnim as om2anim

from AL.maya2.omx import _xnode
from AL.maya2.omx.utils import _nodes
from AL.maya2.omx.utils import _modifiers

logger = logging.getLogger(__name__)


_CURRENT_MODIFIER_LIST = []


class NodeCreationLog:
    """Helper class to enable/disable and manage tracked nodes.

    Log entries are done in a First In Last Out approach to allow for nested tracking
    when a parent that wants to track nodes calls a child that also wants to track nodes.
    """

    def __init__(self):
        self._log = []
        self._isActive = False

    def beginNewLog(self):
        """Adds a new list to the node creation log.
        """
        self._log.append([])
        self._isActive = True

    def clearLogEntry(self, clearAll=False):
        """Remove all or the last list of tracked nodes in the log.

        Args:
            clearAll (bool): If true, remove the entire log.
        """
        if clearAll:
            self._log = []
        self._log.pop()
        self._isActive = len(self._log) >= 1

    def trackedNodes(self, queryAll=False):
        """The nodes that have been tracked in the creation log.

        Args:
            queryAll (bool): If true, get the entire log, otherwise just the last key in the log.

        Returns:
            list[:class:`om2.MObjectHandle`]: The list of created nodes.
        """
        if not self._log:
            logger.warning("No tracked nodes in the creation log.")
            return []

        if queryAll:
            return [node for trackedNodes in self._log for node in trackedNodes]
        return self._log[-1]

    def trackNode(self, node):
        """Add a node to the last active key in the tracking log.

        Args:
            node (:class:`omx.XNode`): The node to track.
        """
        if not self.isActive():
            return
        mobHandle = object.__getattribute__(node, "_mobHandle")
        self._log[-1].append(mobHandle)

    def isActive(self):
        """Check if the log is currently in use.

        Returns:
            bool: The active status of the log.
        """
        return self._isActive


_NODE_CREATION_LOG = NodeCreationLog()


def startTrackingNodes():
    """Start a new entry in the node creation log to track any nodes created with createNode/createDagNode/createDGNode calls.
    """
    _NODE_CREATION_LOG.beginNewLog()


def endTrackingNodes(endAll=False):
    """Stop and clear the last (or all) active log(s) of tracked nodes.

    Args:
        endAll (bool): If true, ends all active tracking.
    Returns:
        list[:class:`om2.MObjectHandle`]: The list of created nodes that had been tracked.
    """
    if not _NODE_CREATION_LOG.isActive():
        logger.debug("No active omx._xmodifier creation log to end.")
        return []

    createdNodes = _NODE_CREATION_LOG.trackedNodes(endAll)
    _NODE_CREATION_LOG.clearLogEntry(endAll)
    return createdNodes


def queryTrackedNodes(queryAll=False):
    """The mobject handles to the nodes that have been created since tracking has been started.

    Args:
        queryAll (bool): If true, return the entire list of handles, otherwise just the handles
                         since startTrackingNodes has last been called.

    Returns:
        list[:class:`om2.MObjectHandle`]: The list of created nodes.
    """
    if not _NODE_CREATION_LOG.isActive():
        logger.info("No active creation log to query.")
        return []

    return _NODE_CREATION_LOG.trackedNodes(queryAll)


class TrackCreatedNodes:
    """
    A Python Context Decorator to temporarily track nodes that have been created with omx

    Example usage:

    @TrackCreatedNodes()
    def methodToCreateNodes():
        # Create nodes
        nodesCreated = omx.queryTrackedNodes()

    OR

    def methodToCreateNodes():
        with TrackCreatedNodes() as tracker:
            # Create nodes
            nodesCreated = tracker.trackedNodes()
    """

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kw):
            with self:
                return func(*args, **kw)

        return wrapper

    def __enter__(self):
        startTrackingNodes()
        return self

    def __exit__(self, *_, **__):
        endTrackingNodes()

    def trackedNodes(self, queryAll=False):
        """Get the om2.MObjectHandle(s) created that are tracked.

        Args:
            queryAll (bool): Whether return all batches of om2.MObjectHandles or just the last
                batch.

        Returns:
            list[:class:`om2.MObjectHandle`]: Created nodes.
        """
        return queryTrackedNodes(queryAll)


class XModifierLog:
    __slots__ = ["method", "values"]

    def __init__(self, method, values):
        self.method = method
        self.values = values

    def __str__(self):
        return f"{self.method}({self.values})"


def _modifierMethod(method):
    @wraps(method)
    def wrapper(*args, **kwargs):
        self = args[0]

        # Add journal entry, convert all MObjects to MObjectHandles
        values = inspect.getcallargs(method, *args, **kwargs)
        del values["self"]
        for k, v in values.items():
            if isinstance(v, om2.MObject):
                values[k] = om2.MObjectHandle(v)
        self._journal.append(XModifierLog(method.__name__, values))  # NOQA
        self._clean = False  # NOQA

        # Process args to convert any XNode to MObject
        newArgs = []
        for arg in args:
            if isinstance(arg, _xnode.XNode):
                arg = arg.object()
            newArgs.append(arg)
        for k, v in kwargs.items():
            if isinstance(v, _xnode.XNode):
                kwargs[k] = v.object()

        logger.debug("Calling %s(%s, %s)", method, newArgs, kwargs)
        res = method(*newArgs, **kwargs)

        if self._immediate:  # NOQA
            self.doIt()

        return res

    return wrapper


class XModifier:
    """ A wrapper around _modifiers.MModifier that supports :class:`_xnode.XNode` instances directly

    When created in immediate mode, every time any modifier method is run on this object the doIt method is also run from within a
    dynamic AL_OMXCommand instance to allow undoing.
    Immediate mode will always be much slower than non-immediate mode, and is only there to allow simple experimentation from the maya script editor.
    """

    def __init__(self, immediate=False):
        """Creates a new XModifier instance.

        Args:
            immediate (bool, optional): Specifies if this XModifier should behave in immediate mode. Defaults to False.
        """
        self._immediate = immediate
        self._reset()

    def _reset(self):
        self._modifier = _modifiers.MModifier()
        self._journal = []
        self._clean = True

    def journal(self):
        """Returns the current list of operations to run

        Returns:
            list(str): A list of strings describing the operations to run.
        """
        journal = []
        for record in self._journal:
            values = {}
            for k, v in record.values.items():
                if isinstance(v, om2.MObjectHandle):
                    mob = v.object()
                    if mob == om2.MObject.kNullObj:
                        values[k] = None
                    elif mob.hasFn(om2.MFn.kDependencyNode):
                        values[k] = str(_xnode.XNode(mob))
                    else:
                        values[k] = 'MObject("unknown")'
                else:
                    values[k] = str(v)

            valuesStr = ", ".join(
                [f"{repr(k)}: {repr(v)}" for k, v in sorted(values.items())]
            )
            journal.append(f"mod.{record.method}({{{valuesStr}}})")

        return journal

    def _reallyDoIt(self, keepJournal=False):
        logger.debug("%r._reallyDoIt() called", self)
        try:
            if self._immediate:
                # this will call the self._modifier.doIt() method directly!
                cmds.AL_OMXCommand()
            else:
                DoItModifierWrapper(self, self._modifier).doIt()
        finally:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Just called doIt on:\n%s", "\n".join(self.journal()))
            if not keepJournal:
                self._journal = []

    def isClean(self):
        """Returns True if the modifier has nothing to do.

        isClean() will also return True if the modifier has already been used by a Command.

        Returns:
            bool: anything to do with this modifier?
        """
        return self._clean

    def doIt(self, keepJournal=False):
        """Executes the modifier in Maya. In immediate mode this will actually execute doIt from within a dynamic maya command to allow undo to function.

        Executes the modifier's operations. If doIt() is called multiple times
        in a row, without any intervening calls to undoIt(), then only the
        operations which were added since the previous doIt() call will be
        executed. If undoIt() has been called then the next call to doIt() will
        do all operations.

        Args:
            keepJournal (bool, optional): Retains the journal for further inspection. Defaults to False.
        """
        logger.debug("%r.doIt() called", self)
        if self._immediate and self not in _CURRENT_MODIFIER_LIST:
            # This can happen if something is keeping an instance of an XModifier and calling doIt in immediate mode...
            _CURRENT_MODIFIER_LIST.append(self)
        self._reallyDoIt(keepJournal=keepJournal)
        if self._immediate:
            # Create a new modifier to ensure modifiers are not shared across command instances
            self._reset()

    def undoIt(self, keepJournal=False):
        """Undo the modifier operation in Maya. In immediate mode this function does nothing, as you should already be able to undo it in Maya.

        Notes:
            It is only used in the scenario that a user creates a modifier manually by calling omx.newModifier()
        Args:
            keepJournal (bool, optional): Retains the journal for further inspection. Defaults to False.
        """
        logger.debug("%r.undoIt() called", self)
        try:
            if self._immediate:
                # Immediate mode hands undo/redo controls to Maya:
                warnings.warn(
                    "In the immediate mode, Maya takes care of the undo/redo.",
                    RuntimeWarning,
                )
            else:
                DoItModifierWrapper(self, self._modifier).undoIt()
        finally:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Just called undoIt on:\n%s", "\n".join(self.journal()))
            if not keepJournal:
                self._journal = []

    @_modifierMethod
    def addAttribute(self, node, attribute):
        """Adds an attribute to a node.

        Adds an operation to the modifier to add a new dynamic attribute to the
        given dependency node. If the attribute is a compound its children will
        be added as well, so only the parent needs to be added using this method.

        Args:
            node (:class:`_xnode.XNode` | :class:`om2.MObject`): the node to add an attribute to
            attribute (:class:`om2.MObject`): the attribute MObject

        Returns:
            :class:`XModifier`: A reference to self
        """
        if isinstance(node, _xnode.XNode):
            node = node.object()
        self._modifier.addAttribute(node, attribute)
        return self

    @_modifierMethod
    def addExtensionAttribute(self, nodeClass, attribute):
        """Adds an extension attribute to a node class

        Adds an operation to the modifier to add a new extension attribute to
        the given node class. If the attribute is a compound its children will be
        added as well, so only the parent needs to be added using this method.

        Args:
            nodeClass (:class:`om2.MNodeClass`): The node class
            attribute (:class:`om2.MObject`): The attribute MObject to add

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.addExtensionAttribute(nodeClass, attribute)
        return self

    @_modifierMethod
    def commandToExecute(self, command):
        """Adds an operation to the modifier to execute a MEL command.

        The command should be fully undoable otherwise unexpected results may occur. If
        the command contains no undoable portions whatsoever, the call to
        doIt() may fail, but only after executing the command. It is best to
        use multiple commandToExecute() calls rather than batching multiple
        commands into a single call to commandToExecute(). They will still be
        undone together, as a single undo action by the user, but Maya will
        better be able to recover if one of the commands fails.

        Args:
            command (str): The command string

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.commandToExecute(command)
        return self

    @_modifierMethod
    def connect(self, *args, **kwargs):
        """Connects two plugs.

        Adds an operation to the modifier that connects two plugs in the
        dependency graph. It is the user's responsibility to ensure that the
        source and destination attributes are of compatible types. For instance,
        if the source attribute is a nurbs surface then the destination must
        also be a nurbs surface.
        Plugs can either be specified with node and attribute MObjects or with
        MPlugs.

        Note:
            Arguments v1: If any plug is an array plug, it will expect another is also an
            array plug with matched data type, and it will try to connect at array level:

            source (:class:`XPlug` | :class:`om2.MPlug`): The source plug
            dest (:class:`XPlug` | :class:`om2.MPlug`): The destination plug

            Arguments v2: If any plug is an array plug, it will try to connect at the next available
            element level:

            sourceNode (:class:`MObject`): The source MObject
            sourceAttr (:class:`MObject`): The source attribute MObject
            destNode (:class:`MObject`): The destination MObject
            destAttr (:class:`MObject`): The destination attribute MObject

        Returns:
            :class:`XModifier`: A reference to self
        """
        return self._modifier.connect(*args, **kwargs)

    @_modifierMethod
    def createDGNode(self, typeName, nodeName=""):
        """Creates a DG node

        Args:
            typeName (str): the type of the object to create, e.g. "transform"
            nodeName (str, optional): the node name, if non empty will be used in a modifier.renameObject call. Defaults to "".

        Returns:
            :class:`_xnode.XNode`: An _xnode.XNode instance around the created MObject.
        """
        mob = self._modifier.createDGNode(typeName)
        if nodeName:
            # Call parent method directly to avoid an entry in the journal
            self._modifier.renameNode(mob, nodeName)

        # To get a valid MObjectHandle in XNode the creation needs to happen right away
        self._modifier.doIt()
        node = _xnode.XNode(mob)
        _NODE_CREATION_LOG.trackNode(node)
        return node

    @_modifierMethod
    def createDagNode(
        self,
        typeName,
        parent=om2.MObject.kNullObj,
        nodeName="",
        manageTransformIfNeeded=True,
        returnAllCreated=False,
    ):
        """Creates a DAG node

        Adds an operation to the modifier to create a DAG node of the specified type. If a parent DAG node is provided the new node will be parented under it.
        If no parent is provided and the new DAG node is a transform type then it will be parented under the world. In both of these cases the method returns
        the new DAG node.

        If no parent is provided and the new DAG node is not a transform type then a transform node will be created and the child parented under that.
        The new transform will be parented under the world and it is the transform node which will be returned by the method, not the child.

        None of the newly created nodes will be added to the DAG until the modifier's doIt() method is called.

        Notes:
            If you try to use createDagNode() to create an empty NURBSCurve or Mesh, calling bestFn() on the returned
            `XNode` will give you MFnNurbsCurve or MFnMesh but these are invalid to work with. You will end up getting a 
            misleading "Object does not exist." error as Maya doesn't like an empty NURBSCurve or Mesh.

        Raises:
            :class:`TypeError` if the node type does not exist or if the parent is not a transform type.

        Args:
            typeName (str): the type of the object to create, e.g. "transform"
            parent (:class:`om2.MObject` | :class:`_xnode.XNode`, optional): An optional parent for the DAG node to create
            nodeName (str, optional): the node name, if non empty will be used in a modifier.renameObject call. Defaults to "".
            returnAllCreated (bool, optional): If True, it will return all newly created nodes, potentially including any new parent transforms and the shape of the type.
        Returns:
            :class:`_xnode.XNode` | list: An _xnode.XNode instance around the created MObject, or the list of all created nodes, if returnAllCreated is True.
        """
        if parent is None:
            parent = om2.MObject.kNullObj
        if parent != om2.MObject.kNullObj:
            if isinstance(parent, om2.MObject):
                xparent = _xnode.XNode(parent)
            elif isinstance(parent, _xnode.XNode):
                xparent = parent
            else:
                xparent = _xnode.XNode(parent)
            if not xparent.object().hasFn(om2.MFn.kTransform):
                parent = xparent.bestFn().parent(0)

        mob = self._modifier.createDagNode(typeName, parent=parent)
        allCreated = [] if returnAllCreated else None
        if parent == om2.MObject.kNullObj or parent is None:
            self._modifier.doIt()
            trn = mob
            if manageTransformIfNeeded:
                # Special case where Maya automatically creates and returns the parent transform instead of the newly created child.
                trnFn = om2.MFnDagNode(trn)
                if trnFn.childCount():
                    mob = trnFn.child(0)
                    availableName = _nodes.closestAvailableNodeName(typeName + "1")
                    self._modifier.renameNode(trn, availableName)

            if returnAllCreated:
                allCreated.append(_xnode.XNode(trn))

        if nodeName:
            # Call parent method directly to avoid an entry in the journal
            self._modifier.renameNode(mob, nodeName)

        # To get a valid MObjectHandle in XNode the creation needs to happen right away
        self._modifier.doIt()
        node = _xnode.XNode(mob)
        _NODE_CREATION_LOG.trackNode(node)
        if returnAllCreated:
            allCreated.append(node)
            return allCreated

        return node

    @_modifierMethod
    def createNode(self, typeName, *args, **kwargs):
        """Convenience method to be able to use an XModifier when a MDagModifier or MDGModifier is expected.

        Args:
            typeName (str): the type of the object to create, e.g. "transform"

        Returns:
            :py:class:`om2.MObject`: The created MObject
        """
        # if any parent keyword is specified, we want to create a dag node for sure. Otherwise, we check the node type.
        if kwargs.get("parent") or "dagNode" in cmds.nodeType(
            typeName, inherited=True, isTypeName=True
        ):
            return self.createDagNode(typeName, *args, **kwargs).object()
        return self.createDGNode(typeName, *args, **kwargs).object()

    @_modifierMethod
    def deleteNode(self, node):
        """Deletes the node

        Adds an operation to the modifer which deletes the specified node from
        the Dependency Graph. If the modifier already contains other operations
        on the same node (e.g. a disconnect) then they should be committed by
        calling the modifier's doIt() before the deleteNode operation is added.

        Args:
            node (:class:`XNode` | :class:`om2.MObject`): The object to delete.

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.deleteNode(node)
        return self

    @_modifierMethod
    def disconnect(self, *args, **kwargs):
        """Disconnects two plugs

        Adds an operation to the modifier that breaks a connection between two
        plugs in the dependency graph.
        Plugs can either be specified with node and attribute MObjects or with
        MPlugs.

        Note:
            Arguments v1: It works for all the scenarios, including disconnecting
            two array plugs at array level.

            source (:class:`XPlug` | :class:`om2.MPlug`): The source plug
            dest (:class:`XPlug` | :class:`om2.MPlug`): The destination plug

            Arguments v2: Unlike the connect() version, it does not work on array
            attributes.

            sourceNode (:class:`MObject`): The source MObject
            sourceAttr (:class:`MObject`): The source attribute MObject
            destNode (:class:`MObject`): The destination MObject
            destAttr (:class:`MObject`): The destination attribute MObject

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.disconnect(*args, **kwargs)
        return self

    @_modifierMethod
    def linkExtensionAttributeToPlugin(self, plugin, attribute):
        """ Links an extension attribute to a plugin

        The plugin can call this method to indicate that the extension attribute
        defines part of the plugin, regardless of the node type to which it
        attaches itself. This requirement is used when the plugin is checked to
        see if it is in use or if is able to be unloaded or if it is required as
        part of a stored file. For compound attributes only the topmost parent
        attribute may be passed in and all of its children will be included,
        recursively. Thus it's not possible to link a child attribute to a
        plugin by itself. Note that the link is established immediately and is
        not affected by the modifier's doIt() or undoIt() methods.

        Args:
            plugin (:class:`om2.MObject`): The plugin
            attribute (:class:`om2.MObject`): The attribute

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.linkExtensionAttributeToPlugin(plugin, attribute)
        return self

    @_modifierMethod
    def newPlugValue(self, plug, value):
        """Sets a new plug value.

        Adds an operation to the modifier to set the value of a plug, where
        value is an MObject data wrapper, such as created by the various
        MFn*Data classes.

        Args:
            plug (:class:`XPlug` | :class:`om2.MPlug`): The plug
            value (:class:`om2.MObject`): The value

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.newPlugValue(plug, value)
        return self

    @_modifierMethod
    def newPlugValueBool(self, plug, value):
        """Adds an operation to the modifier to set a value onto a bool plug.

        Args:
            plug (:class:`XPlug` | :class:`om2.MPlug`): The plug
            value (bool): The value

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.newPlugValueBool(plug, value)
        return self

    @_modifierMethod
    def newPlugValueChar(self, plug, value):
        """Adds an operation to the modifier to set a value onto a char (single byte signed integer) plug.

        Args:
            plug (:class:`XPlug` | :class:`om2.MPlug`): The plug
            value (int): The value

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.newPlugValueChar(plug, value)
        return self

    @_modifierMethod
    def newPlugValueDouble(self, plug, value):
        """Adds an operation to the modifier to set a value onto a double-precision float plug.

        Args:
            plug (:class:`XPlug` | :class:`om2.MPlug`): The plug
            value (float): The value

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.newPlugValueDouble(plug, value)
        return self

    @_modifierMethod
    def newPlugValueFloat(self, plug, value):
        """Adds an operation to the modifier to set a value onto a single-precision float plug.

        Args:
            plug (:class:`XPlug` | :class:`om2.MPlug`): The plug
            value (float): The value

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.newPlugValueFloat(plug, value)
        return self

    @_modifierMethod
    def newPlugValueInt(self, plug, value):
        """Adds an operation to the modifier to set a value onto an int plug.

        Args:
            plug (:class:`XPlug` | :class:`om2.MPlug`): The plug
            value (int): The value

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.newPlugValueInt(plug, value)
        return self

    @_modifierMethod
    def newPlugValueMAngle(self, plug, value):
        """Adds an operation to the modifier to set a value onto an angle plug.

        Args:
            plug (:class:`XPlug` | :class:`om2.MPlug`): The plug
            value (:class:`om2.MAngle`): The value

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.newPlugValueMAngle(plug, value)
        return self

    @_modifierMethod
    def newPlugValueMDistance(self, plug, value):
        """Adds an operation to the modifier to set a value onto a distance plug.

        Args:
            plug (:class:`XPlug` | :class:`om2.MPlug`): The plug
            value (:class:`om2.MDistance`): The value

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.newPlugValueMDistance(plug, value)
        return self

    @_modifierMethod
    def newPlugValueMTime(self, plug, value):
        """Adds an operation to the modifier to set a value onto a time plug.

        Args:
            plug (:class:`XPlug` | :class:`om2.MPlug`): The plug
            value (:class:`om2.MTime`): The value

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.newPlugValueMTime(plug, value)
        return self

    @_modifierMethod
    def newPlugValueShort(self, plug, value):
        """Adds an operation to the modifier to set a value onto a short integer plug.

        Args:
            plug (:class:`XPlug` | :class:`om2.MPlug`): The plug
            value (int): The value

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.newPlugValueShort(plug, value)
        return self

    @_modifierMethod
    def newPlugValueString(self, plug, value):
        """Adds an operation to the modifier to set a value onto a string plug.

        Args:
            plug (:class:`XPlug` | :class:`om2.MPlug`): The plug
            value (str): The value

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.newPlugValueString(plug, value)
        return self

    @_modifierMethod
    def pythonCommandToExecute(self, callable_):
        """ Adds an operation to execute a python command

        Adds an operation to the modifier to execute a Python command, which
        can be passed as either a Python callable or a string containing the
        text of the Python code to be executed. The command should be fully
        undoable otherwise unexpected results may occur. If the command
        contains no undoable portions whatsoever, the call to doIt() may fail,
        but only after executing the command. It is best to use multiple calls
        rather than batching multiple commands into a single call to
        pythonCommandToExecute(). They will still be undone together, as a
        single undo action by the user, but Maya will better be able to
        recover if one of the commands fails.

        Args:
            callable_ (callable | str): The command to execute

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.pythonCommandToExecute(callable_)
        return self

    @_modifierMethod
    def removeAttribute(self, node, attribute):
        """Removes a dynamic attribute.

        Adds an operation to the modifier to remove a dynamic attribute from the
        given dependency node. If the attribute is a compound its children will
        be removed as well, so only the parent needs to be removed using this
        method. The attribute MObject passed in will be set to kNullObj. There
        should be no function sets attached to the attribute at the time of the
        call as their behaviour may become unpredictable.

        Args:
            node (:class:`_xnode.XNode` | :class:`om2.MObject`): the node to remove the attribute from
            attribute (:class:`om2.MObject`): the attribute MObject

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.removeAttribute(node, attribute)
        return self

    @_modifierMethod
    def removeExtensionAttribute(self, nodeClass, attribute):
        """Removes an extension attribute.

        Adds an operation to the modifier to remove an extension attribute from
        the given node class. If the attribute is a compound its children will
        be removed as well, so only the parent needs to be removed using this
        method. The attribute MObject passed in will be set to kNullObj. There
        should be no function sets attached to the attribute at the time of the
        call as their behaviour may become unpredictable.

        Args:
            nodeClass (:class:`om2.MNodeClass`): The node class
            attribute (:class:`om2.MObject`): The attribute MObject to add

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.removeExtensionAttribute(nodeClass, attribute)
        return self

    @_modifierMethod
    def removeExtensionAttributeIfUnset(self, nodeClass, attribute):
        """Removes an extension attribute.

        Adds an operation to the modifier to remove an extension attribute from
        the given node class, but only if there are no nodes in the graph with
        non-default values for this attribute. If the attribute is a compound
        its children will be removed as well, so only the parent needs to be
        removed using this method. The attribute MObject passed in will be set
        to kNullObj. There should be no function sets attached to the attribute
        at the time of the call as their behaviour may become unpredictable.

        Args:
            nodeClass (:class:`om2.MNodeClass`): The node class
            attribute (:class:`om2.MObject`): The attribute MObject to add

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.removeExtensionAttributeIfUnset(nodeClass, attribute)
        return self

    @_modifierMethod
    def removeMultiInstance(self, plug, breakConnections):
        """Adds an operation to the modifier to remove an element of a multi (array) plug.

        Args:
            plug (:class:`XPlug` | :class:`om2.MPlug`): The plug
            breakConnections (bool): breaks the connections

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.removeMultiInstance(plug, breakConnections)
        return self

    @_modifierMethod
    def renameAttribute(self, node, attribute, newShortName, newLongName):
        """Adds an operation to the modifer that renames a dynamic attribute on the given dependency node.

        Args:
            node (:class:`_xnode.XNode` | :class:`om2.MObject`): the node to rename the attribute on
            attribute (:class:`om2.MObject`): the attribute MObject
            newShortName (str): The new short name
            newLongName (str): The new long name

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.renameAttribute(node, attribute, newShortName, newLongName)
        return self

    @_modifierMethod
    def renameNode(self, node, newName):
        """Adds an operation to the modifer to rename a node.

        Args:
            node (:class:`_xnode.XNode` | :class:`om2.MObject`): the node to rename
            newName (str): the new name

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.renameNode(node, newName)
        return self

    @_modifierMethod
    def setNodeLockState(self, node, newState):
        """Adds an operation to the modifier to set the lockState of a node.

        Args:
            node (:class:`_xnode.XNode` | :class:`om2.MObject`): the node to lock
            newState (bool): the lock state

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.setNodeLockState(node, newState)
        return self

    @_modifierMethod
    def unlinkExtensionAttributeFromPlugin(self, plugin, attribute):
        """Unlinks an extension attribute from a plugin.

        The plugin can call this method to indicate that it no longer requires
        an extension attribute for its operation. This requirement is used when
        the plugin is checked to see if it is in use or if is able to be unloaded
        or if it is required as part of a stored file. For compound attributes
        only the topmost parent attribute may be passed in and all of its
        children will be unlinked, recursively. Thus it's not possible to unlink
        a child attribute from a plugin by itself. Note that the link is broken
        immediately and is not affected by the modifier's doIt() or undoIt()
        methods.

        Args:
            plugin (:class:`om2.MObject`): The plugin
            attribute (:class:`om2.MObject`): The attribute MObject to add

        Returns:
            :class:`XModifier`: A reference to self
        """
        self._modifier.unlinkExtensionAttributeFromPlugin(plugin, attribute)
        return self

    @_modifierMethod
    def reparentNode(self, node, newParent=None, absolute=False):
        """Adds an operation to the modifier to reparent a DAG node under a specified parent.

        Raises TypeError if the node is not a DAG node or the parent is not a transform type.

        If no parent is provided then the DAG node will be reparented under the world, so long as it is a transform type.
        If it is not a transform type then the doIt() will raise a RuntimeError.

        Args:
            node (:class:`om2.MObject` | :class:`_xnode.XNode`): The Dag node to reparent
            newParent (:class:`om2.MObject` | :class:`_xnode.XNode`, optional): The new parent. Defaults to None.
            absolute (bool): Whether or not we try to maintain the world transform of the node.
                If the node has some transform channels locked, it will try to fill the unlocked channels with debug
                message.

        Returns:
            :class:`XModifier`: A reference to self
        """
        if not node.hasFn(om2.MFn.kDagNode):
            raise TypeError(
                "The XModifier.reparentNode() received non-Dag node to reparent."
            )

        nodeX = _xnode.XNode(node)
        nodeFn = nodeX.basicFn()

        if newParent is None or newParent == om2.MObject.kNullObj:
            # If asked to reparent to world but it already is:
            if not nodeFn.parentCount():
                return self

            newParent = None
        else:
            parentNodeX = _xnode.XNode(newParent)
            # Avoid reparenting to itself:
            if nodeX == parentNodeX:
                raise RuntimeError(
                    "The XModifier.reparentNode() cannot reparent node to itself."
                )

            if not parentNodeX.hasFn(om2.MFn.kDagNode):
                raise TypeError(
                    "The XModifier.reparentNode() received non-Dag node to reparent to."
                )

            # Avoid reparenting if it is already under the parent:
            for i in range(nodeFn.parentCount()):
                if _xnode.XNode(nodeFn.parent(i)) == parentNodeX:
                    return self

            # Avoid reparenting parent to a child
            if newParent:
                for path in om2.MDagPath.getAllPathsTo(newParent):
                    while path.length() > 0:
                        if _xnode.XNode(path.pop().node()) == node:
                            raise RuntimeError(
                                "The XModifier.reparentNode() cannot reparent node to one of its children."
                            )

        if not absolute:
            newParent = om2.MObject() if not newParent else newParent
            self._modifier.reparentNode(node, newParent)
            return self

        # We use a cheap version here as the matrix multiplication won't work easily with custom rotate pivot
        # and scale pivot, plus some corner cases like joint axis...
        nodePath = om2.MFnDagNode(node).partialPathName()
        newParentPath = ""
        if newParent and om2.MObjectHandle(newParent).isValid():
            newParentPath = om2.MFnDagNode(newParent).partialPathName()

        flag = "-w" if not newParentPath else ""
        cmdStr = f"parent -a {flag} {nodePath} {newParentPath}"
        self._modifier.commandToExecute(cmdStr)
        return self


class DoItModifierWrapper:
    def __init__(self, xmod, mmod):
        self._xmod = xmod
        self._mmod = mmod

    def doIt(self):
        try:
            self._mmod.doIt()
        except Exception as e:
            _, exc_value, _ = sys.exc_info()
            j = self._xmod.journal()
            if not j:
                logger.error("Failed to call doIt: %s", exc_value)
            if len(j) == 1:
                logger.error("Failed to call doIt on %s: %s", j[0], exc_value)
            else:
                logger.error(
                    "Failed to run doIt on operations: %s\n%s", exc_value, "\n".join(j)
                )
            journal = ", ".join(j)
            raise Exception(f"{exc_value} when calling {journal}") from e

    def undoIt(self):
        try:
            self._mmod.undoIt()
        except Exception as e:
            _, exc_value, _ = sys.exc_info()
            j = self._xmod.journal()
            if not j:
                logger.error("Failed to call undoIt: %s", exc_value)
            elif len(j) == 1:
                logger.error("Failed to call undoIt on %s: %s", j[0], exc_value)
            else:
                logger.error(
                    "Failed to run undoIt on operations: %s\n%s",
                    exc_value,
                    "\n".join(j),
                )
            journal = ", ".join(j)
            raise Exception(f"{exc_value} when calling {journal}") from e

    def redoIt(self):
        self.doIt()


def getAndClearModifierStack():
    global _CURRENT_MODIFIER_LIST
    existingMods = []
    for xmod in _CURRENT_MODIFIER_LIST:
        if isinstance(xmod, XModifier):
            if xmod.isClean():
                continue
            mmod = xmod._modifier  # NOQA
        else:
            mmod = None
        logger.debug("Retrieving mod %r from list for execution", mmod)
        existingMods.append(DoItModifierWrapper(xmod, mmod))
    _CURRENT_MODIFIER_LIST = []
    return existingMods


def currentModifier():
    """Returns the last XModifier from the current modifier list. If the current list is empty it creates and returns a new immediate XModifier.

    Returns:
        :class:`XModifier`: A XModifier instance ready to use.
    """
    if not _CURRENT_MODIFIER_LIST:
        mod = XModifier(immediate=True)
        logger.debug("Added modifier %r to list", mod)
        _CURRENT_MODIFIER_LIST.append(mod)
    else:
        mod = _CURRENT_MODIFIER_LIST[-1]
    return mod


def newModifier():
    """Creates a new non-immediate XModifier, adds it to the current list of modifiers and returns it.

    Returns:
        :class:`XModifier`: The newly created XModifier
    """
    mod = XModifier(immediate=False)
    logger.debug("Added modifier %r to list", mod)
    _CURRENT_MODIFIER_LIST.append(mod)
    return mod


def newAnimCurveModifier():
    """Creates a new MAnimCurveChange object, adds it to the current list of modifiers and returns it.

    Returns:
        :class:`om2anim.MAnimCurveChange`: The newly created MAnimCurveChange
    """
    mod = om2anim.MAnimCurveChange()
    logger.debug("Added modifier %r to list", mod)
    _CURRENT_MODIFIER_LIST.append(mod)
    return mod


def hasCurrentModifier():
    """Check if there is any omx modifier ready for an edit.

    Returns:
        bool: True if there is, False otherwise.
    """
    return bool(_CURRENT_MODIFIER_LIST)


def executeModifiersWithUndo():
    """Execute modifier actions with undo support.

    Notes:
        This will push a AL_OMXCommand mpx undoable command in the Maya undo queue.
    """
    if _CURRENT_MODIFIER_LIST:
        cmds.AL_OMXCommand()


@contextlib.contextmanager
def newModifierContext():
    """Create a new xModifier for the context, and call xModifier.doIt() on context exit.

    Notes:
        Any edits done within the python context, they are using the new xModifier.
    """
    if _CURRENT_MODIFIER_LIST:
        # execute any previous doIt upon entering new context
        for mod in _CURRENT_MODIFIER_LIST:
            mod.doIt()
    mod = XModifier(immediate=False)
    logger.debug("Added modifier %r to list", mod)
    _CURRENT_MODIFIER_LIST.append(mod)
    yield mod
    mod.doIt()


@contextlib.contextmanager
def commandModifierContext(command):
    """A Python Context Manager to be used within ALCommand doIt method.

    This modifier ensures a non-immediate XModifier is added to the current list of modifiers, and called doIt on exit.

    Notes:
        This is a util only for AL internal use.

    Args:
        command (:py:class:`AL.libs.command.command.Command`): The command instance
    """
    command._managedByXModifer = True  # NOQA

    # For all nested commands, we make sure they are using the same modifier as the outer-most
    # command, so the undo / redo is linear.
    nested = _CURRENT_MODIFIER_LIST and getattr(
        _CURRENT_MODIFIER_LIST[-1], "_inOperation", False
    )
    if nested:
        # This command is nested in other commands, it should reuse the modifier to the outer-most
        # command, which should already have _inOperation state set to True:
        mod = _CURRENT_MODIFIER_LIST[-1]
        logger.debug(
            "Possible nested commands found, the outmost XModifier %r will be reused.",
            mod,
        )

        # Call do it before sub command, allowing any exception to raise:
        mod.doIt()
        yield mod
        # Call do it after sub command, allowing any exception to raise:
        mod.doIt()
    else:
        mod = XModifier(immediate=False)
        logger.debug("Added modifier %r to list", mod)
        _CURRENT_MODIFIER_LIST.append(mod)
        mod._inOperation = True  # pylint: disable=protected-access
        yield mod
        mod._inOperation = False  # pylint: disable=protected-access
        try:
            mod.doIt()
        finally:
            command._modifiers = getAndClearModifierStack()  # NOQA


def createDagNode(
    typeName, parent=om2.MObject.kNullObj, nodeName="", returnAllCreated=False
):
    """Creates a DAG Node within the current active XModifier

    Note: 
        We automatically work around a limitation of the Maya MDagModifier here, where Maya would return the shape's parent 
        transform MObject. Instead we return an `XNode` for the newly created Shape node if the type is of Shape.

    Args:
        typeName (str): The type of the DAG node to create
        parent (:class:`XNode` | :class:`om2.MObject` | :class:`om2.MFnDagNode` | str, optional): The parent of the DAG node to create.
            Defaults to om2.MObject.kNullObj.
        nodeName (str, optional): The name of the node to create (used to call mod.renameNode after creation). Defaults to "".
        returnAllCreated (bool, optional): If True, it will return any newly created nodes, including potential new parent transform 
            and the shape of the type.

    Returns:
        :class:`XNode`: The created XNode
    """
    return currentModifier().createDagNode(
        typeName, parent=parent, nodeName=nodeName, returnAllCreated=returnAllCreated
    )


def createDGNode(typeName, nodeName=""):
    """Creates a DG Node within the current active XModifier

    Args:
        typeName (str): The node type name
        nodeName (str, optional): The node name (to be used in mod.renameNode after creation). Defaults to "".

    Returns:
        :class:`XNode`: The created XNode
    """
    return currentModifier().createDGNode(typeName, nodeName=nodeName)


def doIt():
    """Runs doIt on all current modifiers
    """
    for mod in _CURRENT_MODIFIER_LIST[:]:
        mod.doIt()


def ensureModifierStackIsClear(_):
    """Check if the modifier stack is empty, clear it with a warning if not. This is mainly used
    in some scene events like after new scene or before scene open, to make sure we have a clean start.
    """
    global _CURRENT_MODIFIER_LIST
    if _CURRENT_MODIFIER_LIST:
        warnings.warn(
            f"xmodifier list is not empty when it should! {_CURRENT_MODIFIER_LIST}",
            RuntimeWarning,
        )
        _CURRENT_MODIFIER_LIST = []
