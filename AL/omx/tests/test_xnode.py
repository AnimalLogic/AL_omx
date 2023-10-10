# Copyright (C) Animal Logic Pty Ltd. All rights reserved.

import unittest
import logging
from maya import cmds
from maya.api import OpenMaya as om2
from AL.maya2 import omx

logger = logging.getLogger(__name__)


class XNodeCase(unittest.TestCase):
    app = "maya"

    def setUp(self):
        cmds.file(new=True, f=True)

    def testImmediateModifier(self):
        omx.createDagNode("transform", nodeName="myTransform")
        self.assertTrue(cmds.objExists("myTransform"))

    def testTransform(self):
        transform = omx.createDagNode("transform", nodeName="myTransform")

        with self.assertRaises(AttributeError):
            willfail = transform.iDoNotExist  # NOQA

        mtx2 = om2.MMatrix()
        self.assertEqual(transform.worldMatrix.get()[0], mtx2)

        cmds.setAttr("myTransform.translateX", 5.0)
        mtx2 = om2.MMatrix()
        mtx2[12] = 5.0

        self.assertEqual(transform.worldMatrix[0].get(), mtx2)

    def testConstructors(self):
        transform = omx.createDagNode("transform", nodeName="myTransform")
        self.assertIsInstance(transform.worldMatrix, om2.MPlug)

        transform2 = omx.XNode(transform)
        self.assertIsInstance(transform2.worldMatrix, om2.MPlug)

        transform3 = omx.XNode(om2.MFnDependencyNode(transform.object()))
        self.assertIsInstance(transform3.worldMatrix, om2.MPlug)

        transform4 = omx.XNode("myTransform")
        self.assertIsInstance(transform4.worldMatrix, om2.MPlug)

        with self.assertRaises(RuntimeError):
            willfail = omx.XNode("invalidNode")  # NOQA

        transform5 = omx.createDagNode(
            "transform", nodeName="myTransform5", parent=transform
        )
        self.assertIsInstance(transform5.worldMatrix, om2.MPlug)
        self.assertTrue(cmds.objExists("myTransform|myTransform5"))

        dag = omx.XNode(transform.bestFn().getPath())
        self.assertIsInstance(dag.worldMatrix, om2.MPlug)

    def testArrayPlugs(self):
        transform = omx.createDagNode("transform", nodeName="myTransform")

        self.assertIsInstance(transform.worldMatrix, omx.XPlug)
        self.assertTrue(transform.worldMatrix.isArray)
        self.assertIsInstance(transform.worldMatrix[0], omx.XPlug)

        self.assertFalse(transform.translateX.isArray)
        with self.assertRaises(TypeError):
            willfail = transform.translateX[0]  # NOQA

    def testConnectPlugs(self):
        transform1 = omx.createDagNode("transform", nodeName="myTransform1")
        transform2 = omx.createDagNode("transform", nodeName="myTransform2")

        transform2.translate.connectFrom(transform1.translate)

        self.assertEqual(
            cmds.listConnections("myTransform2.translate", plugs=True, source=True),
            ["myTransform1.translate"],
        )

        transform2.rotate.connectFrom(transform1.rotate)

        self.assertEqual(
            cmds.listConnections("myTransform2.rotate", plugs=True, source=True),
            ["myTransform1.rotate"],
        )

        transform1.scale.connectTo(transform2.scale)

        self.assertEqual(
            cmds.listConnections("myTransform2.scale", plugs=True, source=True),
            ["myTransform1.scale"],
        )

        transform1.translate.connectTo(transform2.scale, force=True)

        self.assertEqual(
            cmds.listConnections("myTransform2.scale", plugs=True, source=True),
            ["myTransform1.translate"],
        )

        transform2.scale.connectFrom(transform1.scale, force=True)

        self.assertEqual(
            cmds.listConnections("myTransform2.scale", plugs=True, source=True),
            ["myTransform1.scale"],
        )

        transform2.scale.disconnectFromSource()

        self.assertEqual(transform2.scale.isConnected, False)

    def testCustomNode(self):
        transform = omx.createDagNode("transform", nodeName="myTransform")
        rep = omx.createDGNode("AL_rig_reparentSingle", "myReparent")
        transform.translate.connectFrom(rep.translate)

        self.assertEqual(
            cmds.listConnections("myTransform.translate", plugs=True),
            ["myReparent.translate"],
        )

    def testPlugMethods(self):
        transform = omx.createDagNode("transform", nodeName="myTransform")
        rep = omx.createDGNode("AL_rig_reparentSingle", "myReparent")
        transform.translate.connectFrom(rep.translate)

        self.assertIsInstance(rep.outSRT.child(0), omx.XPlug)
        self.assertIsInstance(transform.translate.source(), omx.XPlug)
        self.assertIsInstance(rep.translate.destinations()[0], omx.XPlug)

    def testMofifierJournal(self):
        with omx.newModifierContext() as mod:
            transform = omx.createDagNode("transform", nodeName="myTransform")
            rep = omx.createDGNode("AL_rig_reparentSingle", "myReparent")
            transform.translate.connectFrom(rep.translate)
            mod.doIt(keepJournal=True)
            self.assertEqual(
                mod.journal(),
                [
                    "mod.createDagNode({'manageTransformIfNeeded': 'True', 'nodeName': 'myTransform', 'parent': None, 'returnAllCreated': 'False', 'typeName': 'transform'})",
                    "mod.createDGNode({'nodeName': 'myReparent', 'typeName': 'AL_rig_reparentSingle'})",
                    "mod.connect({'args': '(XPlug(\"myReparent.translate\"), XPlug(\"myTransform.translate\"))', 'kwargs': '{}'})",
                ],
            )

    def testDynamicAttrs(self):
        transform1 = omx.createDagNode("transform", nodeName="myTransform1")
        transform2 = omx.createDagNode("transform", nodeName="myTransform2")
        attrFn = om2.MFnNumericAttribute()
        attrMOb = attrFn.create("shortName", "longName", om2.MFnNumericData.kFloat)
        mod = omx.currentModifier()
        mod.addAttribute(transform1, attrMOb)

        self.assertEqual(transform1.shortName.asFloat(), 0.0)
        cmds.setAttr("myTransform1.longName", 2.5)

        self.assertEqual(transform1.longName.asFloat(), 2.5)

        # checking one more time to see if the cache is all good!
        cmds.setAttr("myTransform1.longName", 3.0)
        self.assertEqual(transform1.longName.asFloat(), 3.0)

        # checking another transform to validate no bleeding of attribute cache
        with self.assertRaises(AttributeError):
            willfail = transform2.longName  # NOQA

        self.assertFalse(hasattr(transform1, "idonotexist"))
        self.assertTrue(hasattr(transform1, "longName"))

    def testGetPlugValues(self):
        transform = omx.createDagNode("transform", nodeName="myTransform")

        cmds.setAttr("myTransform.translateX", 5.0)

        self.assertEqual(transform.translateX.get(), 5.0)
        mtx = transform.worldMatrix[0].get()
        self.assertIsInstance(mtx, om2.MMatrix)
        mtx2 = om2.MMatrix()
        mtx2[12] = 5.0
        self.assertEqual(mtx, mtx2)

    def testSetPlugValues(self):
        transform = omx.createDagNode("transform", nodeName="myTransform")

        transform.translateX.set(5.0)

        self.assertEqual(transform.translateX.get(), 5.0)
        mtx = transform.worldMatrix[0].get()
        mtx2 = om2.MMatrix()
        mtx2[12] = 5.0
        self.assertEqual(mtx, mtx2)

        transform.translateX.set(3.0)

        self.assertEqual(transform.translateX.get(), 3.0)

    def testStrings(self):
        transform1 = omx.createDagNode("transform", nodeName="myTransform1")
        transform2 = omx.createDagNode(
            "transform", nodeName="myTransform2", parent=transform1
        )
        child1 = omx.createDagNode("transform", nodeName="child", parent=transform1)
        child2 = omx.createDagNode("transform", nodeName="child", parent=transform2)
        rep = omx.createDGNode("AL_rig_reparentSingle", "myReparent")

        self.assertEqual(str(transform1), "myTransform1")
        self.assertEqual(repr(transform1), 'XNode("myTransform1")')
        self.assertEqual(str(child1), "myTransform1|child")
        self.assertEqual(str(child2), "myTransform2|child")
        self.assertEqual(repr(rep), 'XNode("myReparent")')
        self.assertEqual(str(rep.translate), "myReparent.translate")
        self.assertEqual(repr(rep.translate), 'XPlug("myReparent.translate")')

    def testBestFn(self):
        transform = omx.createDagNode("transform", nodeName="myTransform1")
        fn = transform.bestFn()
        self.assertIsInstance(fn, om2.MFnTransform)
        rep = omx.createDGNode("AL_rig_reparentSingle", "myReparent")
        fn = rep.bestFn()
        self.assertIsInstance(fn, om2.MFnDependencyNode)

    def testUndoContext(self):
        transform1 = omx.createDagNode("transform", nodeName="myTransform1")
        self.assertTrue(cmds.objExists("myTransform1"))

        cmds.undo()
        self.assertFalse(cmds.objExists("myTransform1"))

        cmds.redo()
        self.assertTrue(cmds.objExists("myTransform1"))

        with omx.newModifierContext() as mod:
            transform2 = mod.createDagNode(
                "transform", nodeName="myTransform2", parent=transform1
            )
            self.assertTrue(cmds.objExists("myTransform2"))
            mod.createDagNode("transform", nodeName="myTransform3", parent=transform2)
            self.assertTrue(cmds.objExists("myTransform2|myTransform3"))
            transform2.translate.connectFrom(transform1.translate)
            self.assertEqual(
                cmds.listConnections("myTransform2.translate", plugs=True, source=True),
                None,
            )

        omx._xmodifier.executeModifiersWithUndo()  # pylint: disable=protected-access
        self.assertEqual(
            cmds.listConnections("myTransform2.translate", plugs=True, source=True),
            ["myTransform1.translate"],
        )

        cmds.undo()
        self.assertFalse(cmds.objExists("myTransform2|myTransform3"))
        self.assertFalse(cmds.objExists("myTransform2"))

        with omx.newModifierContext() as mod:
            transform2 = mod.createDagNode(
                "transform", nodeName="myTransform2", parent=transform1
            )
            self.assertTrue(cmds.objExists("myTransform2"))
            transform2.translate.connectFrom(transform1.translate)
            self.assertEqual(
                cmds.listConnections("myTransform2.translate", plugs=True, source=True),
                None,
            )
            omx.doIt()
            self.assertEqual(
                cmds.listConnections("myTransform2.translate", plugs=True, source=True),
                ["myTransform1.translate"],
            )

    class FakeCommand:
        def __init__(self):
            self._modifiers = []

    def testCommandContext(self):
        cmd = self.FakeCommand()
        with omx.commandModifierContext(cmd):
            self.assertTrue(cmd._managedByXModifer)  # NOQA

            transform1 = omx.createDagNode("transform", nodeName="myTransform1")
            self.assertTrue(
                cmds.objExists("myTransform1"),
                msg="Objects created in the root have to be created right away",
            )
            transform2 = omx.createDagNode(
                "transform", nodeName="myTransform2", parent=transform1
            )
            self.assertTrue(cmds.objExists("myTransform2"), msg="Creation is immediate")

            transform2.translate.connectFrom(transform1.translate)
            self.assertEqual(
                cmds.listConnections("myTransform2.translate", plugs=True, source=True),
                None,
            )

        self.assertEqual(
            cmds.listConnections("myTransform2.translate", plugs=True, source=True),
            ["myTransform1.translate"],
        )
        self.assertEqual(len(cmd._modifiers), 1)  # NOQA

    def testCommandContextSameModifier(self):
        cmd1 = self.FakeCommand()
        cmd2 = self.FakeCommand()
        with omx.commandModifierContext(cmd1) as modifier:
            with omx.commandModifierContext(cmd2) as modifier1:
                self.assertTrue(modifier1 is modifier)

    def testNestedContexts(self):
        loc1 = omx.createDagNode("transform", nodeName="loc1")
        self.assertTrue(cmds.objExists("loc1"))
        with omx.newModifierContext():
            loc2 = loc1.createDagNode("transform", "loc2")
            self.assertTrue(cmds.objExists("loc2"))
            loc2.translate.connectFrom(loc1.translate)
            self.assertEqual(
                cmds.listConnections("loc2.translate", plugs=True, source=True), None
            )
            with omx.newModifierContext():
                self.assertTrue(
                    cmds.objExists("loc1|loc2"),
                    msg="previous modifier's doIt should be called when entering a new context",
                )
                self.assertEqual(
                    cmds.listConnections("loc2.translate", plugs=True, source=True),
                    ["loc1.translate"],
                )
                loc2.createDagNode("transform", "loc3")
                self.assertTrue(cmds.objExists("loc3"))
            self.assertTrue(cmds.objExists("loc1|loc2|loc3"))

    def testCreateTransformIfNeeded(self):
        loc1 = omx.createDagNode("locator", nodeName="loc1")
        self.assertTrue(cmds.objExists("loc1"))
        self.assertTrue(cmds.objExists("locator1|loc1"))

        loc2 = loc1.createDagNode("transform", "loc2")
        loc2.createDagNode("locator", "loc2Shape")
        self.assertTrue(cmds.objExists("locator1|loc2"))
        self.assertTrue(cmds.objExists("loc2|loc2Shape"))

        loc3 = loc2.createDagNode("transform", "loc3")
        loc3.createDagNode("locator", "loc3Shape")
        self.assertTrue(cmds.objExists("locator1|loc2|loc3"))
        self.assertTrue(cmds.objExists("loc3|loc3Shape"))

    def testCreateNode(self):
        with omx.newModifierContext() as mod:
            loc1 = mod.createNode("transform", nodeName="loc1")
            mod.createNode("locator", nodeName="loc1Shape", parent=loc1)
            mod.createNode("transform", parent=loc1)
            mod.createNode("transform", parent=loc1)
            mod.createNode("AL_rig_reparentSingle", nodeName="rep1")

        self.assertTrue(cmds.objExists("loc1"))
        self.assertTrue(cmds.objExists("loc1|loc1Shape"))
        self.assertTrue(cmds.objExists("loc1|transform1"))
        self.assertTrue(cmds.objExists("loc1|transform2"))
        self.assertTrue(cmds.objExists("rep1"))

    def testCoumpoundPlug(self):
        cond = omx.createDGNode("condition", nodeName="cond")
        cond.colorIfTrue.set([1, 1, 1])
        omx.doIt()
        self.assertEqual(cmds.getAttr("cond.colorIfTrueR"), 1.0)
        self.assertEqual(cmds.getAttr("cond.colorIfTrueG"), 1.0)
        self.assertEqual(cmds.getAttr("cond.colorIfTrueB"), 1.0)

    def testCreateDagNodeName(self):
        omx.createDagNode("locator", nodeName="testLocator")
        self.assertTrue(cmds.objExists("testLocator"))
        self.assertTrue(cmds.objExists("locator1|testLocator"))

        omx.createDagNode("locator", nodeName="testLocator")
        self.assertTrue(cmds.objExists("locator2|testLocator"))

    def testCreateDagNodeNoName(self):
        omx.createDagNode("locator")
        self.assertTrue(cmds.objExists("locator1"))
        self.assertTrue(cmds.objExists("locator1|locatorShape1"))

        omx.createDagNode("transform")
        self.assertTrue(cmds.objExists("transform1"))

    def testReparentNode(self):
        t1 = omx.createDagNode("transform", nodeName="testTransform1")
        t2 = omx.createDagNode("transform", nodeName="testTransform2")
        self.assertTrue(cmds.objExists("testTransform1"))
        self.assertTrue(cmds.objExists("testTransform2"))

        mod = omx.XModifier()
        # Reparent works with node and newParent as XNodes
        mod.reparentNode(t2, newParent=t1)
        mod.doIt()
        self.assertTrue(cmds.objExists("testTransform1|testTransform2"))
        # Also works with node and newParent as MObjects
        t3 = omx.createDagNode("transform", nodeName="testTransform3")
        mod.reparentNode(t2.object(), newParent=t3.object())
        mod.doIt()
        self.assertTrue(cmds.objExists("testTransform3|testTransform2"))

    def testDeleteNode(self):
        loc1 = omx.createDagNode("transform", nodeName="loc1")
        omx.createDagNode("locator", nodeName="loc1Shape", parent=loc1)
        self.assertTrue(cmds.objExists("loc1"))
        self.assertTrue(cmds.objExists("loc1|loc1Shape"))
        loc2 = omx.createDagNode("transform", nodeName="loc2")
        omx.createDagNode("locator", nodeName="loc2Shape", parent=loc2)
        self.assertTrue(cmds.objExists("loc2"))
        self.assertTrue(cmds.objExists("loc2|loc2Shape"))

        mod = omx.XModifier()
        # deleteNode works with node as XNode and MObject
        mod.deleteNode(loc1)
        mod.deleteNode(loc2.object())
        mod.doIt()
        self.assertFalse(cmds.objExists("loc1"))
        self.assertFalse(cmds.objExists("loc1|loc1Shape"))
        self.assertFalse(cmds.objExists("loc2"))
        self.assertFalse(cmds.objExists("loc2|loc2Shape"))

    def testCompare(self):
        transform1 = omx.createDagNode("transform", nodeName="myTransform1")
        transform2 = omx.createDagNode("transform", nodeName="myTransform2")
        self.assertTrue(transform1 == omx.XNode("myTransform1"))
        self.assertTrue(transform2 == omx.XNode("myTransform2"))
        self.assertFalse(transform1 == transform2)
        self.assertTrue(transform1 == transform1.object())
        fn = transform1.bestFn()
        fn.setName("newName")
        self.assertTrue(transform1 == omx.XNode("newName"))

    def testMObjectMethodAccess(self):
        transform1 = omx.createDagNode("transform", nodeName="myTransform1")
        self.assertEqual(transform1.apiType(), om2.MFn.kTransform)
        self.assertTrue(transform1.hasFn(om2.MFn.kDagNode))
        self.assertFalse(transform1.isNull())
        self.assertEqual(transform1.apiTypeStr, "kTransform")

    def testDeletedXNode(self):
        transform1 = omx.createDagNode("transform", nodeName="myTransform1")
        self.assertTrue(transform1.isValid())
        self.assertTrue(transform1.isAlive())
        cmds.delete("myTransform1")
        self.assertTrue(transform1.isAlive())
        self.assertFalse(transform1.isValid())
        with self.assertRaises(RuntimeError):
            transform1.translateX.connect(transform1.translateY)
        self.assertEqual(str(transform1), ":myTransform1(invalid)")

    def testHashability(self):
        transform1 = omx.createDagNode("transform", nodeName="myTransform1")
        transform2 = omx.createDagNode("transform", nodeName="myTransform2")
        d = {transform1: "foo", transform2: "bar"}
        self.assertTrue(omx.XNode("myTransform1") in d)
        self.assertEqual(d[omx.XNode("myTransform2")], "bar")

    def testDeleteXNodeWithinCommand(self):
        cmds.CreatePolygonCube()

        class FakeCommand:
            def __init__(self):
                self._modifiers = []

        cmd = FakeCommand()
        with omx.commandModifierContext(cmd) as mod:
            target = omx.XNode("pCube1")
            mod.deleteNode(target)
            mod.doIt()
            fakeLog = str(target)
            self.assertEqual(fakeLog, ":pCube1(invalid)")
