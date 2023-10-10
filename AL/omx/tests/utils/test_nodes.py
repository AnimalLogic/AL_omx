# Copyright (C) Animal Logic Pty Ltd. All rights reserved.

import unittest
from maya import cmds
from maya.api import OpenMaya as om2
from AL.maya2.omx.utils import _nodes
from AL.maya2.omx.tests.utils import common


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
