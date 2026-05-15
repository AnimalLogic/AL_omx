# Copyright © 2026 Netflix, Inc. All Rights Reserved.
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


import unittest

from AL.omx.utils._stubs import cmds
from AL.omx.utils._stubs import om2
from AL.omx.utils import _nodes
from AL.omx.tests.utils import common


class NodesNameCase(unittest.TestCase):
    app = "maya"

    def setUp(self):
        cmds.file(new=True, f=True)
        cmds.group(empty=True, name="myGrp")
        cmds.group(empty=True, name="myGrp1")
        cmds.group(empty=True, name="myGrp2")

    def test_partitionNameAndTrailingDigits(self):
        testDict = {
            "": (None, None),
            "123": (None, 123),
            "abcd": ("abcd", None),
            "abcd0": ("abcd", 0),
            "abcd23": ("abcd", 23),
            "abcd_3": ("abcd_", 3),
            "abcd_3_46": ("abcd_3_", 46),
            "ns:abcd_3_46": ("ns:abcd_3_", 46),
        }
        for inputName, outputData in testDict.items():
            self.assertEqual(
                outputData, _nodes.partitionNameAndTrailingDigits(inputName)
            )

    def test_closestAvailableNodeName(self):
        testDict = {
            "": None,
            "123": None,
            "abcd": "abcd",
            "myGrp": "myGrp3",
            "myGrp1": "myGrp3",
            "myGrp2": "myGrp3",
            "myGrp3": "myGrp3",
        }
        for inputName, availableName in testDict.items():
            self.assertEqual(availableName, _nodes.closestAvailableNodeName(inputName))


class NodesBasicsCase(unittest.TestCase):

    app = "maya"

    def setUp(self):
        cmds.file(new=True, f=True)
        common.setupSimplestScene()

    def tearDown(self):
        cmds.file(new=True, f=True)

    def test_findNode(self):
        cmds.polyCube()
        cmds.polyCube()
        cmds.namespace(add="testNs")
        cmds.rename("pCube2", ":testNs:pCube2")
        cmds.parent("pCube3", "testNs:pCube2")

        node = _nodes.findNode("pCube1")
        fnDag = om2.MFnDagNode(node)
        self.assertEqual(fnDag.fullPathName(), "|pCube1")

        # test shortname
        node = _nodes.findNode("pCube3")
        fnDag = om2.MFnDagNode(node)
        self.assertEqual(fnDag.fullPathName(), "|testNs:pCube2|pCube3")

        # test fullname with namespace
        node = _nodes.findNode("|testNs:pCube2|pCube3")
        fnDag = om2.MFnDagNode(node)
        self.assertEqual(fnDag.fullPathName(), "|testNs:pCube2|pCube3")

        # test invalid string
        node = _nodes.findNode("someInvalidName")
        self.assertEqual(node, None)

    def test_createSelectionList(self):
        cmds.polyCube()
        cmds.polyCube()
        cube2SelSet = _nodes.createSelectionList("pCube2")
        self.assertIsInstance(cube2SelSet, om2.MSelectionList)
        cube3MObj = cube2SelSet.getDependNode(0)
        cube3DagPath = om2.MDagPath.getAPathTo(cube3MObj)
        plug = om2.MFnDependencyNode(cube3MObj).findPlug("tx", True)
        self.assertIsInstance(
            _nodes.createSelectionList("pCube2", cube3MObj, cube3DagPath, plug),
            om2.MSelectionList,
        )

    def test_findDagPath(self):
        # dg nodes get no path:
        self.assertFalse(_nodes.findDagPath("time1"))

        # non-exist dag return None:
        self.assertFalse(_nodes.findDagPath("doesNotExist"))

        # existing dag should all works:
        cubeTransform = cmds.polyCube()[0]
        self.assertIsInstance(_nodes.findDagPath(cubeTransform), om2.MDagPath)

        cubeGrp = cmds.group(cubeTransform)
        cmds.duplicate(cubeGrp)
        cubeShape = cmds.listRelatives(
            f"{cubeGrp}|{cubeTransform}", s=True, fullPath=True
        )[0]
        self.assertIsInstance(_nodes.findDagPath(cubeShape), om2.MDagPath)
