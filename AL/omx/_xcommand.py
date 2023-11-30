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

import os
import logging

from AL.omx.utils._stubs import cmds
from AL.omx.utils._stubs import om2
from AL.omx import _xmodifier

logger = logging.getLogger(__name__)


class XCommand(om2.MPxCommand):
    """An internal dynamic command plugin class called by createAL_Command, it is an undoable 
    MPxCommand omx uses to support undo/redo in Maya.

    Notes:
        You don't need to ever touch this command or manually call it. It is completely for
        internal use only.
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

        # to ensure plugin is loadable outside AL:
        pluginDirEnvName = "MAYA_PLUG_IN_PATH"
        pluginDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "plugin")
        plugInDirs = os.environ.get(pluginDirEnvName, "").split(";")
        if pluginDir not in plugInDirs:
            plugInDirs.append(pluginDir)
            os.environ[pluginDirEnvName] = ";".join(plugInDirs)

        cmds.loadPlugin(cls.PLUGIN_CMD_NAME, quiet=True)
        cls._CMD_PLUGIN_LOADED = True
