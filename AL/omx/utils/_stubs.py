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

"""This is a middle layer to import modules from Maya. If we fail we will
fallback to stub mode. 
"""

cmds = None
om2 = None
om2anim = None


def isInsideMaya():
    """Return if we are currently running inside the Autodesk Maya environment.

    Returns:
        bool: True if inside, False otherwise.
    """
    global cmds
    return hasattr(cmds, "loadPlugin") and type(cmds).__name__ == "module"


def _importStandardMayaModules():
    global cmds
    global om2
    global om2anim

    try:
        import maya.cmds as m_cmds
        import maya.api.OpenMaya as m_om2
        import maya.api.OpenMayaAnim as m_om2anim

        cmds = m_cmds
        om2 = m_om2
        om2anim = m_om2anim

        return isInsideMaya()

    except:
        return False


def _importStandaloneMayaModules():
    try:
        import maya.standalone

        maya.standalone.initialize("Python")
        return _importStandardMayaModules()

    except:
        return False


def _useDummyMayaModules():
    # the import has to be here as some Maya version errors when importing it.
    from unittest.mock import MagicMock

    class _OpenMaya(MagicMock):
        """A dummy stub object for maya.api.OpenMaya to silence the module import error when 
        importing AL.omx outside the Autodesk Maya environment; mainly for API document 
        generation purpose.
        """

        class MPxCommand:
            """A dummy for MPxCommand inheritance to avoid python import error.
            """

            pass

        class MPlug:
            """A dummy for MPlug inheritance to avoid python import error.
            """

            pass

        class MDagModifier:
            """A dummy for MDagModifier inheritance to avoid python import error.
            """

            pass

    global cmds
    global om2
    global om2anim
    cmds = MagicMock()
    om2 = _OpenMaya()
    om2anim = MagicMock()
    print(
        "Run AL_omx in dummy mode, all the Maya related features including tests won't work."
    )


# initialize maya modules:
_importStandardMayaModules() or _importStandaloneMayaModules() or _useDummyMayaModules()
