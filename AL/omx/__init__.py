# Copyright (C) Animal Logic Pty Ltd. All rights reserved.

"""
OMX is a thin wrapper around Maya OM2.

OMX's goal is to make OM2 more user-friendly but still retain the API's performance.

Main entry points are:
:py:func:`omx.createDagNode` and :py:func:`omx.createDGNode` which return instances of :py:class:`omx.XNode`

See :doc:`/topics/omx` for more information.

"""
from ._xplug import XPlug  # NOQA: F401
from ._xnode import XNode  # NOQA: F401
from ._xmodifier import (
    createDagNode,
    createDGNode,
    doIt,
    currentModifier,
    newModifierContext,
    newModifier,
    newAnimCurveModifier,
    commandModifierContext,
    XModifier,
    queryTrackedNodes,
    TrackCreatedNodes,
)  # NOQA: F401

try:
    from . import _xcommand as _

    _.XCommand.ensureLoaded()
except Exception as e:
    print(f"Loading AL_OMXCommand: {str(e)}: omx might not function as intended!")

__all__ = [
    "createDagNode",
    "createDGNode",
    "doIt",
    "currentModifier",
    "newModifierContext",
    "newModifier",
    "newAnimCurveModifier",
    "commandModifierContext",
    "XPlug",
    "XNode",
    "XModifier",
    "queryTrackedNodes",
    "TrackCreatedNodes",
]
