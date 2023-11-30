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

import unittest

from AL.omx.utils._stubs import cmds
from AL.omx.utils._stubs import om2
from AL.omx.utils import _modifiers


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

            # Test the DAG mode:
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
