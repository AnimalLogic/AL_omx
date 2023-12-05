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


import logging
import unittest

from AL.omx.utils._stubs import cmds
from AL import omx
from AL.omx.utils import _contexts as omu_contexts

logger = logging.getLogger(__name__)


class XModifierUndoableCommandTestCase(unittest.TestCase):
    app = "maya"

    def setUp(self):
        """
        Notes:
            To make command undoable in your Maya test, you need to use ContextualCommandTester instead of CommandTester.
        """
        cmds.file(new=True, force=True)
        # Issue Maya's undo:
        self.group = cmds.group(em=True)

    def test_doitBehaviorOnNonImmediateMode(self):
        mod = omx.newModifier()
        transform1Node = mod.createDagNode("transform")
        transform1 = transform1Node.bestFn().name()

        # For node creation, it will still immediatly call doIt():
        self.assertTrue(cmds.objExists(transform1))

        # For other operation, you need to call doit.
        self.assertTrue(transform1Node.v.get())
        mod.newPlugValueBool(transform1Node.v, False)
        self.assertTrue(transform1Node.v.get())
        mod.doIt()
        self.assertFalse(transform1Node.v.get())
        mod.undoIt()
        self.assertFalse(cmds.objExists(transform1))

    def test_autoUndoRedoImmediateMode(self):
        # Create 3 transforms.
        # Iter 5x, adding/removing the transforms via calling undo and redo.
        with omu_contexts.UndoStateSwitcher(state=True):
            self.assertTrue(cmds.objExists(self.group))

            transform1 = (
                omx.currentModifier().createDagNode("transform").bestFn().name()
            )
            self.assertTrue(cmds.objExists(transform1))
            transform2 = (
                omx.currentModifier().createDagNode("transform").bestFn().name()
            )
            self.assertTrue(cmds.objExists(transform2))

            # Another maya undo:
            anotherGroup = cmds.group(em=True)
            for i in range(5):
                self.assertTrue(cmds.objExists(anotherGroup))
                cmds.undo()
                self.assertFalse(
                    cmds.objExists(anotherGroup), f"Undo failed on iteration {i}."
                )
                self.assertTrue(
                    cmds.objExists(transform2), f"Undo too much on iteration {i}."
                )
                cmds.undo()
                self.assertFalse(
                    cmds.objExists(transform2), f"Undo failed on iteration {i}."
                )
                self.assertTrue(
                    cmds.objExists(transform1), f"Undo too much on iteration {i}."
                )
                cmds.undo()
                self.assertFalse(
                    cmds.objExists(transform1), f"Undo failed on iteration {i}."
                )
                self.assertTrue(
                    cmds.objExists(self.group), f"Undo too much on iteration {i}."
                )
                cmds.undo()
                self.assertFalse(
                    cmds.objExists(self.group), f"Undo failed on iteration {i}."
                )

                cmds.redo()
                self.assertTrue(
                    cmds.objExists(self.group), f"Redo failed on iteration {i}."
                )
                self.assertFalse(
                    cmds.objExists(transform1), f"Redo too much on iteration {i}."
                )
                cmds.redo()
                self.assertTrue(
                    cmds.objExists(transform1), f"Redo failed on iteration {i}."
                )
                self.assertFalse(
                    cmds.objExists(transform2), f"Redo too much on iteration {i}."
                )
                cmds.redo()
                self.assertTrue(
                    cmds.objExists(transform2), f"Redo failed on iteration {i}."
                )
                self.assertFalse(
                    cmds.objExists(anotherGroup), f"Redo too much on iteration {i}."
                )
                cmds.redo()
                self.assertTrue(
                    cmds.objExists(anotherGroup), f"Redo failed on iteration {i}."
                )

    def test_manualUndoRedoImmediateMode(self):
        with omu_contexts.UndoStateSwitcher(state=True):
            self.assertTrue(cmds.objExists(self.group))

            mod = omx.currentModifier()
            transform1 = mod.createDagNode("transform").bestFn().name()
            self.assertTrue(cmds.objExists(transform1))
            mod.undoIt()  # <-- This undo now does nothing as it is totally in Maya's hand
            self.assertTrue(cmds.objExists(transform1))
            cmds.undo()
            self.assertFalse(cmds.objExists(transform1))
            self.assertTrue(cmds.objExists(self.group))
            cmds.undo()
            self.assertFalse(cmds.objExists(self.group))
            cmds.redo()
            self.assertTrue(cmds.objExists(self.group))
            self.assertFalse(cmds.objExists(transform1))
            cmds.redo()
            self.assertTrue(cmds.objExists(transform1))
