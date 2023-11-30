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

import functools

from AL.omx.utils._stubs import cmds


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
