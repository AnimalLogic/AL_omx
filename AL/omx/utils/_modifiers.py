# Copyright (C) Animal Logic Pty Ltd. All rights reserved.
import logging
import warnings

from maya import cmds
from maya.api import OpenMaya as om2
from maya.api import OpenMayaAnim as om2anim

logger = logging.getLogger(__name__)


class MModifier(om2.MDagModifier):
    """A `MDagModifier` that implements the ability to create a DG node.
    
    This way we don't need both an MDGModifier and a MDAGModifier which messes up the Undo/Redo.
    """

    def __init__(self):
        om2.MDagModifier.__init__(self)

        # for self._dgMode:
        # If True, then MModifier behaves like an MDGModifier, except it has ability to use reparentNode.
        #     MModifier.createNode()       -> Create and return a DG node.
        #     MModifier.createDGNode()     -> Create and return a DG node.
        #     MModifier.createDagNode()     -> Create and return a DAG node.

        # If False, then it will behave like an MDGModifier, except it has ability to create DG nodes.
        #     MModifier.createNode()       -> Create and return a DAG node.
        #     MModifier.createDGNode()     -> Create and return a DG node.
        #     MModifier.createDagNode()     -> Create and return a DAG node.
        self._dgMode = False

    def createDGNode(self, typeName):
        """Create a DG node of the type.

        Args:
            typeName (str): The Maya node type name.

        Returns:
            om2.MObject: The DG node created.
        """
        logger.debug("Creating DG node of type %s using MModifier.", typeName)
        mob = om2.MDGModifier.createNode(self, typeName)
        return mob

    def createDagNode(self, typeName, parent=om2.MObject.kNullObj):
        """Create a DAG node of type typeName.

        Args:
            typeName (str): The Maya node type name.
            parent (om2.MObject): The parent MObject. 

        Returns:
            om2.MObject: The DAG node created.
        """
        logger.debug(
            "Creating DAG node of type %s, parent %s  using MModifier.",
            typeName,
            parent,
        )
        mob = om2.MDagModifier.createNode(self, typeName, parent=parent)
        return mob

    def redoIt(self):
        """Actually perform the action in the modifier.
        """
        om2.MDagModifier.doIt(self)

    def createNode(self, *args, **kwargs):
        """Create Dag or DG node based on the internal mode state.

        Returns:
            om2.MObject: The DAG/DG node created.
        """
        warnings.warn(
            "Please use MModifier.createDGNode() or MModifier.createDagNode() over MModifier.createNode() to make it clear.",
            DeprecationWarning,
        )
        if self._dgMode:
            return self.createDGNode(*args, **kwargs)
        return self.createDagNode(*args, **kwargs)


class ToDGModifier:
    """A python context to use an MModifer in DGmode, which means MModifier.createNode() will create a DG node.
    """

    def __init__(self, mmodifer):
        self._mmodifer = mmodifer
        self._oldDGMode = mmodifer._dgMode

    def __enter__(self):
        self._mmodifer._dgMode = True
        return self._mmodifer

    def __exit__(self, *_, **__):
        self._mmodifer._dgMode = self._oldDGMode


class ToDagModifier:
    """A python context to use an MModifer in DGmode, which means MModifier.createNode() will create a DAG node.
    """

    def __init__(self, mmodifer):
        self._mmodifer = mmodifer
        self._oldDGMode = mmodifer._dgMode

    def __enter__(self):
        self._mmodifer._dgMode = False
        return self._mmodifer

    def __exit__(self, *_, **__):
        self._mmodifer._dgMode = self._oldDGMode
