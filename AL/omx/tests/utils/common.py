# Copyright (C) Animal Logic Pty Ltd. All rights reserved.

from maya import cmds
from AL.maya2.omx.utils import _contexts


def runTestsWithUndoEnabled(testcase):
    """A quick util to make sure all unittests in your testcase run with undo/redo recording enabled.

    """
    context = _contexts.UndoStateSwitcher(True)
    testcase.contextEnterValue = context.__enter__()
    testcase.addCleanup(context.__exit__)


def setupSimplestScene():
    """Create polyCube and select a bunch of nodes, and return the polyCube's parent transform node name.
    """
    transform, _ = cmds.polyCube(
        w=1, h=1, d=1, sx=1, sy=1, sz=1, ax=[0, 1, 0], cuv=4, ch=1
    )
    return transform
