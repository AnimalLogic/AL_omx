# Copyright (C) Animal Logic Pty Ltd. All rights reserved.

import logging
from maya import cmds
from maya.api import OpenMaya as om2
from AL.maya2.omx import _xmodifier

logger = logging.getLogger(__name__)


class XCommand(om2.MPxCommand):

    """Dynamic command plugin called by createAL_Command
    """

    PLUGIN_CMD_NAME = "AL_OMXCommand"
    _CMD_PLUGIN_LOADED = False

    def __init__(self):
        om2.MPxCommand.__init__(self)
        logger.debug("%r() instanced created", self)
        self._modifiers = _xmodifier.getAndClearModifierStack()
        logger.debug(
            "%r() instanced created got %i modifiers", self, len(self._modifiers)
        )

    @staticmethod
    def creator():
        return XCommand()

    def isUndoable(self):
        return True

    def doIt(self, argList):  # NOQA
        logger.debug("%r.doIt() called with %i modifiers", self, len(self._modifiers))
        for mod in self._modifiers:
            mod.doIt()

    def redoIt(self):
        logger.debug("%r.redoIt() called", self)
        for mod in self._modifiers:
            mod.doIt()

    def undoIt(self):
        logger.debug("%r.undoIt() called", self)
        for mod in reversed(self._modifiers):
            mod.undoIt()

    @classmethod
    def ensureLoaded(cls):
        if cls._CMD_PLUGIN_LOADED:
            return
        cmds.loadPlugin(cls.PLUGIN_CMD_NAME, quiet=True)
        cls._CMD_PLUGIN_LOADED = True
