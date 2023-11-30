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

# This module should be discoverable by Maya plugin loader.

from AL.omx.utils._stubs import om2
from AL.omx import _xcommand, _xmodifier


def maya_useNewAPI():
    """The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    return True


__CALLBACK_ID_LIST = []


def installCallbacks():
    """Install callbacks for events like after new Maya scene, before Maya scene open
    and Maya quit. This will be called when the omx plug-in is loaded.
    """
    __CALLBACK_ID_LIST.append(
        om2.MSceneMessage.addCallback(
            om2.MSceneMessage.kAfterNew, _xmodifier.ensureModifierStackIsClear, None
        )
    )
    __CALLBACK_ID_LIST.append(
        om2.MSceneMessage.addCallback(
            om2.MSceneMessage.kBeforeOpen, _xmodifier.ensureModifierStackIsClear, None
        )
    )
    __CALLBACK_ID_LIST.append(
        om2.MSceneMessage.addCallback(
            om2.MSceneMessage.kMayaExiting, _xmodifier.ensureModifierStackIsClear, None
        )
    )


def uninstallCallbacks():
    """Uninstall previously registered callbacks. This will be called when the omx plug-in is unloaded.
    """
    global __CALLBACK_ID_LIST
    for i in __CALLBACK_ID_LIST:
        om2.MMessage.removeCallback(i)
    __CALLBACK_ID_LIST = []


def initializePlugin(plugin):
    """Maya MPxPlugin hook to initialise the plug.
    """
    pluginFn = om2.MFnPlugin(plugin)
    pluginFn.registerCommand(
        _xcommand.XCommand.PLUGIN_CMD_NAME, _xcommand.XCommand.creator
    )
    installCallbacks()


def uninitializePlugin(plugin):
    """Maya MPxPlugin hook to uninitialise the plug.
    """
    pluginFn = om2.MFnPlugin(plugin)
    pluginFn.deregisterCommand(_xcommand.XCommand.PLUGIN_CMD_NAME)
    uninstallCallbacks()
