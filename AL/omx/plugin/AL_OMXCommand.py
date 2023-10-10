# Copyright (C) Animal Logic Pty Ltd. All rights reserved.

# This module should be discoverable by Maya plugin loader.
# To-do: come up with a easier way for generic user to install the plugin file for opensourcing.

from AL.maya2 import om2
from AL.maya2.omx import _xcommand, _xmodifier


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    return True


__CALLBACK_ID_LIST = []


def installCallbacks():
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
