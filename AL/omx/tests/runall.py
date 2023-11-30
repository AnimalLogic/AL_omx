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

"""This is the module to run all the tests, you need to execute it within mayapy:

    mayapy -m AL.omx.tests.runall

"""

import os
from unittest import loader, suite
from unittest import runner

from AL.omx import tests as omxtests
from AL.omx.utils._stubs import isInsideMaya


class _MayaPyContext:
    def __enter__(self):
        self.standaloneMod = None
        try:
            from maya import standalone

            standalone.initialize("Python")
            standaloneMod = standalone
        except:
            print("Please Run this module with mayapy or Maya Interactive.")

    def __exit__(self, *_, **__):
        if not isInsideMaya():
            return

        if self.standaloneMod:
            self.standaloneMod.uninitialize()


def runAllOMXTests():
    with _MayaPyContext():
        if not isInsideMaya():
            print(
                "The AL_omx tests cannot be run outside Maya environment, you need to run this within Maya Interactive or with mayapy."
            )
            return 1

        topDir = os.path.dirname(omxtests.__file__)
        testItems = loader.defaultTestLoader.discover(
            "AL.omx.tests", top_level_dir=topDir
        )
        testRunner = runner.TextTestRunner()
        testRunner.run(testItems)


if __name__ == "__main__":
    runAllOMXTests()
