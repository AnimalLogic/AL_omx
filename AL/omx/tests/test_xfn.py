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
from AL import omx


class XFnCase(unittest.TestCase):
    app = "maya"

    def setUp(self):
        cmds.file(new=True, f=True)
        self._parentName = "parent"
        self._nodeName = "myTransform"
        self._nodeName1 = "myTransform1"
        self._parentXnode = omx.createDagNode("transform", nodeName=self._parentName)
        self._dagXnode = omx.createDagNode(
            "transform", nodeName=self._nodeName, parent=self._parentXnode
        )
        self._dgXnode = omx.XNode("time1")
        self._dagXnode1 = omx.createDagNode(
            "transform", nodeName=self._nodeName1, parent=self._parentXnode
        )
        self._childrenXnodes = [self._dagXnode, self._dagXnode1]

    def testConstructors(self):
        mobj = self._dagXnode.object()
        mfn = self._dagXnode.basicFn()
        mfn1 = self._dagXnode.bestFn()
        testList = (self._nodeName, self._dagXnode, mobj, mfn, mfn1)
        # testing from direct construction:
        for obj in testList:
            xfn = omx.XFn(obj)
            self.assertEqual(self._dagXnode, xfn.object())

        # testing from XNode and other XFn:
        xfnFromNode = self._dagXnode.xFn()
        self.assertEqual(self._dagXnode, xfnFromNode.object())

        # testing from another XFn:
        xfn = omx.XFn(xfnFromNode)
        self.assertEqual(self._dagXnode, xfnFromNode.object())

    def testGetParent(self):
        xfn = self._dgXnode.xFn()
        self.assertRaises(RuntimeError, lambda: xfn.getParent(0))

        xfn = self._dagXnode.xFn()
        parent = xfn.getParent(0)
        self.assertTrue(parent and parent.isValid())
        self.assertEqual(str(parent), self._parentName)

        self.assertRaises(RuntimeError, lambda: xfn.getParent(-1))
        self.assertRaises(RuntimeError, lambda: xfn.getParent(1))

        cmds.delete(self._nodeName)
        self.assertRaises(RuntimeError, lambda: xfn.getParent(0))

    def testGetChild(self):
        xfn = self._dgXnode.xFn()
        self.assertRaises(RuntimeError, lambda: xfn.getChild(0))

        xfn = self._parentXnode.xFn()
        for i, childXNode in enumerate(self._childrenXnodes):
            child = xfn.getChild(i)
            self.assertTrue(child and child.isValid())
            self.assertEqual(child, childXNode)

        self.assertRaises(RuntimeError, lambda: xfn.getChild(-1))
        self.assertRaises(RuntimeError, lambda: xfn.getChild(2))

        cmds.delete(self._nodeName)
        cmds.delete(self._nodeName1)
        self.assertRaises(RuntimeError, lambda: xfn.getChild(0))

    def _createTransformWithShape(self):
        transform, _ = cmds.polyCube()
        return omx.XNode(transform)

    def testGetShape(self):
        xfn = self._dgXnode.xFn()
        self.assertRaises(RuntimeError, lambda: xfn.getShape(0))
        xfn = self._parentXnode.xFn()
        self.assertRaises(RuntimeError, lambda: xfn.getShape(0))

        transformXnode = self._createTransformWithShape()
        xfn = transformXnode.xFn()
        shape = xfn.getShape(0)
        self.assertTrue(shape)
        self.assertEqual(shape.xFn().getMFnClass(), om2.MFnMesh)
        self.assertRaises(RuntimeError, lambda: xfn.getShape(1))
        self.assertRaises(RuntimeError, lambda: xfn.getShape(-1))

    def testDagQueryMethods(self):
        xfn = self._dgXnode.xFn()
        self.assertFalse(xfn.hasDagNode())

        transformXnode = self._createTransformWithShape()
        xfn = transformXnode.xFn()
        self.assertTrue(xfn.hasDagNode())
        self.assertTrue(xfn.hasShapeAtIndex(0))
        self.assertFalse(xfn.hasShapeAtIndex(1))
        self.assertFalse(xfn.hasShapeAtIndex(-1))

        self.assertTrue(xfn.hasChildAtIndex(0))
        self.assertFalse(xfn.hasChildAtIndex(1))
        self.assertFalse(xfn.hasChildAtIndex(-1))
        self.assertFalse(xfn.hasParentAtIndex(0))

        shape = xfn.getShape(0)
        shapeFn = shape.xFn()
        self.assertTrue(shapeFn.hasDagNode())
        self.assertTrue(shapeFn.hasParentAtIndex(0))
        self.assertFalse(shapeFn.hasParentAtIndex(-1))
        self.assertFalse(shapeFn.hasParentAtIndex(1))

    def testIterChildren(self):
        xfn = self._dgXnode.xFn()
        self.assertRaises(RuntimeError, lambda: list(xfn.iterChildren()))

        xfn = self._parentXnode.xFn()
        children = list(xfn.iterChildren())
        self.assertEqual(children, self._childrenXnodes)

        predicate = lambda n: str(n) == self._nodeName1
        children = list(xfn.iterChildren(predicate=predicate))
        self.assertEqual(children, [self._dagXnode1])

        predicate = lambda n: str(n) == "invalid"
        self.assertFalse(list(xfn.iterChildren(predicate=predicate)))

    def testIterShapes(self):
        xfn = self._dgXnode.xFn()
        self.assertRaises(RuntimeError, lambda: list(xfn.iterShapes()))

        xfn = self._parentXnode.xFn()
        self.assertFalse(list(xfn.iterShapes()))

        transformXnode = self._createTransformWithShape()
        xfn = transformXnode.xFn()
        shapes = list(xfn.iterShapes())
        self.assertEqual(1, len(shapes))

        predicate = lambda n: str(n) == "invalid"
        self.assertFalse(list(xfn.iterShapes(predicate=predicate)))

    def testIterAncestors(self):
        xfn = self._dgXnode.xFn()
        self.assertRaises(RuntimeError, lambda: list(xfn.iterAncestors()))

        self._descendantXnode = omx.createDagNode(
            "transform", nodeName="descendant", parent=self._dagXnode
        )
        xfn = self._descendantXnode.xFn()
        ancestors = list(xfn.iterAncestors())
        self.assertEqual(ancestors, [self._dagXnode, self._parentXnode])

        predicate = lambda n: str(n) == self._parentName
        self.assertEqual(
            list(xfn.iterAncestors(predicate=predicate)), [self._parentXnode]
        )

    def testIterDescendants(self):
        xfn = self._dgXnode.xFn()
        self.assertRaises(RuntimeError, lambda: list(xfn.iterDescendants()))

        self._descendantXnode = omx.createDagNode(
            "transform", nodeName="descendant", parent=self._dagXnode
        )
        xfn = self._parentXnode.xFn()
        descendants = list(xfn.iterDescendants())
        self.assertEqual(
            descendants, [self._dagXnode, self._descendantXnode, self._dagXnode1]
        )

        predicate = lambda n: str(n) == str(self._dagXnode1)
        self.assertEqual(
            list(xfn.iterDescendants(predicate=predicate)), [self._dagXnode1]
        )

    def testGetPath(self):
        for node in (self._parentXnode, self._dagXnode, self._dgXnode, self._dagXnode1):
            path = node.xFn().getPath()
            self.assertEqual(path, str(node))

    def testGetFullPath(self):
        self.assertEqual(self._dgXnode.xFn().getFullPath(), str(self._dgXnode))
        self.assertEqual(
            self._dagXnode.xFn().getFullPath(), f"|{self._parentXnode}|{self._dagXnode}"
        )

    def testGetName(self):
        xfn = self._dgXnode.xFn()
        self.assertEqual(xfn.getName(), str(self._dgXnode))

        xfn = self._dagXnode.xFn()
        self.assertEqual(xfn.getName(), str(self._dagXnode))
        self.assertEqual(xfn.getName(namespaced=False), str(self._dagXnode))

        ns = "testNS"
        if not om2.MNamespace.namespaceExists(ns):
            om2.MNamespace.addNamespace(ns)

        unNamespacedName = str(self._dagXnode)
        namespaceName = f"{ns}:{unNamespacedName}"
        cmds.rename(self._dagXnode, namespaceName)
        self.assertEqual(xfn.getName(), namespaceName)
        self.assertEqual(xfn.getName(namespaced=False), unNamespacedName)

        self.assertEqual(xfn.getNamespace(), ns)

    def testMethodDelegation(self):
        transformXnode = self._createTransformWithShape()
        shape = transformXnode.xFn().getShape()
        shapeFn = shape.xFn()
        self.assertEqual(len(shapeFn.getPoints()), 8)

    def testDunderMethods(self):
        # Can compare:
        xfn1 = self._dgXnode.xFn()
        xfn2 = self._dgXnode.xFn()
        dagXfn = self._dagXnode.xFn()
        self.assertNotEqual(xfn1, dagXfn)

        # Can hash:
        d = {
            xfn1: self._dgXnode,
            dagXfn: self._dagXnode,
        }
        self.assertEqual(d[dagXfn], self._dagXnode)
        s = {xfn1, dagXfn}
        self.assertTrue(xfn1 in s)

        # Check repr:
        self.assertEqual(repr(xfn1), f"XFn[MFnDependencyNode]({self._dgXnode})")
        self.assertEqual(str(xfn1), f"XFn({self._dgXnode})")
        shape = self._createTransformWithShape().xFn().getShape()
        shapeFn = shape.xFn()
        self.assertEqual(repr(shapeFn), f"XFn[MFnMesh]({shape})")
        self.assertEqual(str(shapeFn), f"XFn({shape})")

    def testIterXPlugsByTypeAndState(self):
        # Make sure XFn.iterXPlugs() works. The majority of the tests are already covered in test_xnode.py,
        # here we just want to make sure the delegation from XFn to XNode works.
        self._dagXnode.ry.setLocked(True)
        self._dagXnode.sx.connectTo(self._dagXnode.sz)

        # Get all keyable angle plugs
        rotatePlugs = list(
            self._dagXnode.iterXPlugs(
                attrType=omx.XAttrType.ANGLE,
                states=omx.XPlugState.KEYABLE,
            )
        )
        self.assertEqual(len(rotatePlugs), 3)
        self.assertTrue(self._dagXnode.rx in rotatePlugs)
        self.assertTrue(self._dagXnode.ry in rotatePlugs)
        self.assertTrue(self._dagXnode.rz in rotatePlugs)

        # Get all settable and visible plugs:
        settableVisiblePlugs = list(
            self._dagXnode.iterXPlugs(
                states=(omx.XPlugState.VISIBLE, omx.XPlugState.SETTABLE),
            )
        )
        self.assertTrue(self._dagXnode.tx in settableVisiblePlugs)
        self.assertFalse(self._dagXnode.ry in settableVisiblePlugs)
        self.assertFalse(self._dagXnode.sz in settableVisiblePlugs)
