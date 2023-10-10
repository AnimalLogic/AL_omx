# Copyright (C) Animal Logic Pty Ltd. All rights reserved.

import unittest
from maya import cmds
from maya.api import OpenMaya as om2
from AL.maya2.omx.utils import _modifiers


class MModifierTestCase(unittest.TestCase):
    app = "maya"

    def setUp(self):
        cmds.file(new=True, f=True)

    def tearDown(self):
        cmds.file(new=True, f=True)

    def test_defaultCreateNode(self):
        cmds.undoInfo(state=True)
        parentName = cmds.polyCube()[0]
        sel = om2.MSelectionList()
        sel.add(parentName)
        parentNode = sel.getDependNode(0)

        modifier = _modifiers.MModifier()

        # Test the default mix mode:
        blinn = modifier.createDGNode("blinn")
        transform1 = modifier.createNode("transform", parentNode)
        transform2 = modifier.createDagNode("transform", parentNode)
        modifier.doIt()

        blinnFn = om2.MFnDependencyNode(blinn)
        blinnNodeName = blinnFn.name()

        transform1Fn = om2.MFnDagNode(transform1)
        transform1Name = transform1Fn.partialPathName()

        transform2Fn = om2.MFnDagNode(transform2)
        transform2Name = transform2Fn.partialPathName()

        self.assertTrue(cmds.objExists(blinnNodeName))
        self.assertTrue(cmds.objExists(transform1Name))
        self.assertTrue(cmds.objExists(transform2Name))

        modifier.undoIt()

        self.assertFalse(cmds.objExists(blinnNodeName))
        self.assertFalse(cmds.objExists(transform1Name))
        self.assertFalse(cmds.objExists(transform2Name))

        modifier.redoIt()

        self.assertTrue(cmds.objExists(blinnNodeName))
        self.assertTrue(cmds.objExists(transform2Name))

    def test_DGModeCreateNode(self):
        parentName = cmds.polyCube()[0]
        sel = om2.MSelectionList()
        sel.add(parentName)
        parentNode = sel.getDependNode(0)

        modifier = _modifiers.MModifier()

        # Test the DG mode:
        with _modifiers.ToDGModifier(modifier) as dgmodifier:
            blinn1 = dgmodifier.createDGNode("blinn")
            blinn2 = dgmodifier.createNode("blinn")
            transform1 = modifier.createDagNode("transform", parentNode)
            dgmodifier.doIt()

            blinn1Fn = om2.MFnDependencyNode(blinn1)
            blinn1NodeName = blinn1Fn.name()

            blinn2Fn = om2.MFnDependencyNode(blinn2)
            blinn2NodeName = blinn2Fn.name()

            transform1Fn = om2.MFnDagNode(transform1)
            transform1Name = transform1Fn.partialPathName()

            self.assertTrue(cmds.objExists(blinn1NodeName))
            self.assertTrue(cmds.objExists(blinn2NodeName))
            self.assertTrue(cmds.objExists(transform1Name))

            dgmodifier.undoIt()

            self.assertFalse(cmds.objExists(blinn1NodeName))
            self.assertFalse(cmds.objExists(blinn2NodeName))
            self.assertFalse(cmds.objExists(transform1Name))

            dgmodifier.redoIt()

            self.assertTrue(cmds.objExists(blinn1NodeName))
            self.assertTrue(cmds.objExists(blinn2NodeName))
            self.assertTrue(cmds.objExists(transform1Name))

            # Test the Dag mode:
            with _modifiers.ToDagModifier(modifier) as dagmodifier:
                transformNew = dagmodifier.createNode("transform", parentNode)
                dagmodifier.doIt()

                transformNewFn = om2.MFnDagNode(transformNew)
                transformNewName = transformNewFn.partialPathName()
                self.assertTrue(cmds.objExists(transformNewName))

        # Outside DG mode, we can create DAG node:
        transform = modifier.createNode("transform", parentNode)
        modifier.doIt()

        transformFn = om2.MFnDagNode(transform)
        transformName = transformFn.partialPathName()

        self.assertTrue(cmds.objExists(blinn1NodeName))
        self.assertTrue(cmds.objExists(blinn2NodeName))
        self.assertTrue(cmds.objExists(transformName))
        modifier.undoIt()

        self.assertFalse(cmds.objExists(blinn1NodeName))
        self.assertFalse(cmds.objExists(blinn2NodeName))
        self.assertFalse(cmds.objExists(transformName))

        modifier.redoIt()

        self.assertTrue(cmds.objExists(blinn1NodeName))
        self.assertTrue(cmds.objExists(blinn2NodeName))
        self.assertTrue(cmds.objExists(transformName))
