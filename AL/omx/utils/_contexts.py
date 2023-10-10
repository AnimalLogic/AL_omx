# Copyright (C) Animal Logic Pty Ltd. All rights reserved.

import functools
from maya import cmds


class UndoStateSwitcher:
    """A context to switch on/off the undo recording state.

    It is mainly for the unittest on the operation undoability, to make sure the undo
    is recorded.
    """

    def __init__(self, state=True):
        self._targetState = bool(state)
        self._oldState = True

    def __enter__(self):
        self._oldState = cmds.undoInfo(q=True, state=True)

        if self._targetState == self._oldState:
            return
        cmds.undoInfo(state=self._targetState)

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            with self:
                return func(*args, **kw)

        return wrapper

    def __exit__(self, *args, **kwargs):
        if self._targetState == self._oldState:
            return

        cmds.undoInfo(state=self._oldState)
