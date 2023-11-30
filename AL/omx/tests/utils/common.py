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


from AL.omx.utils._stubs import cmds
from AL.omx.utils import _contexts


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
