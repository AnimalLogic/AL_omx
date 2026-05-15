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
import logging

from AL.omx.utils._stubs import cmds
from AL.omx.utils._stubs import om2
from AL import omx
from AL.omx import _xmodifier

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
        mtx = omx.createDGNode("decomposeMatrix", "myMtx")
        transform.translate.connectFrom(mtx.outputTranslate)

        self.assertEqual(
            cmds.listConnections("myTransform.translate", plugs=True),
            ["myMtx.outputTranslate"],
        )

    def testPlugMethods(self):
        transform = omx.createDagNode("transform", nodeName="myTransform")
        upstream = omx.createDGNode("decomposeMatrix", "upstreamDG")
        transform.translate.connectFrom(upstream.outputTranslate)

        self.assertIsInstance(upstream.outputTranslate.child(0), omx.XPlug)
        self.assertIsInstance(transform.translate.source(), omx.XPlug)
        self.assertIsInstance(upstream.outputTranslate.destinations()[0], omx.XPlug)

    def _checkJournal(self, modifier, expectedJournal):
        transform = omx.createDagNode("transform", nodeName="myTransform")
        upstream = omx.createDGNode("decomposeMatrix", "upstreamMtx")
        transform.translate.connectFrom(upstream.outputTranslate)
        modifier.doIt(keepJournal=True)
        self.assertEqual(modifier.journal(), expectedJournal)

    def testMofifierJournal(self):
        fullJournal = [
            "mod.createDagNode({'manageTransformIfNeeded': 'True', 'nodeName': 'myTransform', 'parent': None, 'returnAllCreated': 'False', 'typeName': 'transform'})",
            "mod.createDGNode({'nodeName': 'upstreamMtx', 'typeName': 'decomposeMatrix'})",
            "mod.connect({'args': '(XPlug(\"upstreamMtx.outputTranslate\"), XPlug(\"myTransform.translate\"))', 'kwargs': '{}'})",
        ]
        # check when journal is forced on:
        with omx.newModifierContext() as mod:
            with omx.JournalContext():
                self.assertTrue(omx.isJournalOn())
                self._checkJournal(mod, fullJournal)

        # check when journal is forced off:
        with omx.newModifierContext() as mod:
            with omx.JournalContext():
                self.assertTrue(omx.isJournalOn())
                with omx.JournalContext(state=False):
                    self.assertFalse(omx.isJournalOn())
                    self._checkJournal(mod, [])

        # check when journal is decided by logging level:
        oldLevel = _xmodifier.logger.level
        cmds.file(new=True, f=True)  # create new file so node name don't change.
        for level in (logging.DEBUG, logging.INFO):
            _xmodifier.logger.setLevel(level)
            isInDebug = _xmodifier.logger.isEnabledFor(logging.DEBUG)
            expectedJournal = fullJournal if isInDebug else []
            with omx.newModifierContext() as mod:
                with omx.JournalContext(state=None):
                    self.assertEqual(omx.isJournalOn(), isInDebug)
                    self._checkJournal(mod, expectedJournal)

        _xmodifier.logger.setLevel(oldLevel)

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
        timeNode = omx.createDGNode("time", "myDG")

        self.assertEqual(str(transform1), "myTransform1")
        self.assertEqual(repr(transform1), 'XNode("myTransform1")')
        self.assertEqual(str(child1), "myTransform1|child")
        self.assertEqual(str(child2), "myTransform2|child")
        self.assertEqual(repr(timeNode), 'XNode("myDG")')
        self.assertEqual(str(timeNode.outTime), "myDG.outTime")
        self.assertEqual(repr(timeNode.frozen), 'XPlug("myDG.frozen")')

    def testBestFn(self):
        transform = omx.createDagNode("transform", nodeName="myTransform1")
        fn = transform.bestFn()
        self.assertIsInstance(fn, om2.MFnTransform)
        timeNode = omx.createDGNode("time", "myDG")
        fn = timeNode.bestFn()
        self.assertIsInstance(fn, om2.MFnDependencyNode)

    def testDagFn(self):
        """Make sure when we get Maya functor from XNode, we get a best working function set with
        a correct MDagPath attached.
        """
        points = [[i * 0.1] * 3 for i in range(4)]
        testPoint = om2.MPoint(0.0, 0.0, 0.0)
        curveTransformName = cmds.curve(d=3, p=points, k=[0, 0, 0, 1, 1, 1])
        groupName = cmds.group()
        transformNode = omx.XNode(curveTransformName)
        fn = transformNode.bestFn()
        self.assertIsInstance(fn, om2.MFnTransform)
        child = fn.child(0)

        # for xnode constructed using om2.MObject:
        curveNode = omx.XNode(child)
        expectedDagPath = (
            curveNode.basicFn().dagPath()
        )  # this will error if we attach returned fn with MObject.
        self.assertTrue(
            curveNode.bestFn().closestPoint(testPoint, space=om2.MSpace.kWorld)
        )

        # still works for duplicated name with normal copy:
        cmds.duplicate(groupName, rr=True)
        self.assertTrue(
            curveNode.bestFn().closestPoint(testPoint, space=om2.MSpace.kWorld)
        )

        # still works for instanced copy:
        curveShapeName = str(curveNode)
        curveTransformName = str(transformNode)
        instancedTransformName = cmds.duplicate(
            curveTransformName, instanceLeaf=True, rr=True
        )[0]
        self.assertTrue(
            curveNode.bestFn().closestPoint(testPoint, space=om2.MSpace.kWorld)
        )

        # test with xnode reconstruction with instanced shape
        curveNode = omx.XNode(curveShapeName)
        self.assertEqual(curveNode.basicFn().dagPath(), expectedDagPath)
        self.assertTrue(
            curveNode.bestFn().closestPoint(testPoint, space=om2.MSpace.kWorld)
        )

        instancedCurveName = cmds.listRelatives(
            instancedTransformName, s=True, fullPath=True
        )[0]
        instancedCurveNode = omx.XNode(instancedCurveName)
        # the MDagPaths are different, but the MObject is the same.
        self.assertEqual(instancedCurveNode.object(), curveNode.object())
        instancedDagPath = instancedCurveNode.basicFn().dagPath()
        self.assertNotEqual(instancedDagPath, expectedDagPath)
        # but the function still working:
        self.assertTrue(
            curveNode.bestFn().closestPoint(testPoint, space=om2.MSpace.kWorld)
        )

        # construct using MDagPath should also work
        originalCurveNode = omx.XNode(expectedDagPath)
        self.assertEqual(originalCurveNode.basicFn().dagPath(), expectedDagPath)
        self.assertTrue(
            originalCurveNode.bestFn().closestPoint(testPoint, space=om2.MSpace.kWorld)
        )

        # the only limitation is, if you now construct a XNode using an instanced MObject,
        # just as shown in the commented code below, XNode will construct MFn using MObject,
        # which means some call on these DAG MFn returned by XNode.bestFn()/basicFn()
        # won't work:
        # testCurveNode = omx.XNode(instancedCurveNode.object())

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
            mod.createNode("time", nodeName="myTime")

        self.assertTrue(cmds.objExists("loc1"))
        self.assertTrue(cmds.objExists("loc1|loc1Shape"))
        self.assertTrue(cmds.objExists("loc1|transform1"))
        self.assertTrue(cmds.objExists("loc1|transform2"))
        self.assertTrue(cmds.objExists("myTime"))

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


class XNodePlugIterationCase(unittest.TestCase):
    app = "maya"

    def setUp(self):
        cmds.file(new=True, f=True)
        transform = cmds.group(em=True, name="testTransform")
        self.transformNode = omx.XNode(transform)
        self.transformNode.ry.isLocked = True
        self.transformNode.sy.connectTo(self.transformNode.sz)

    def tearDown(self):
        cmds.file(new=True, f=True)

    def testIterXPlugsByType(self):
        # No type filter:
        allPlugs = list(self.transformNode.iterXPlugs())
        totalLen = len(allPlugs)
        self.assertTrue(totalLen > 40)

        # Filter to numeric plugs
        numericPlugs = list(
            self.transformNode.iterXPlugs(attrType=omx.XAttrType.NUMERIC)
        )
        numericLen = len(numericPlugs)
        self.assertTrue(20 < numericLen < totalLen)

        # Filter to unit plugs
        unitPlugs = list(self.transformNode.iterXPlugs(attrType=omx.XAttrType.UNIT))
        unitLen = len(unitPlugs)
        self.assertTrue(15 < unitLen < totalLen)

        # Test angle plugs:
        radianPlugs = list(self.transformNode.iterXPlugs(attrType=omx.XAttrType.ANGLE))
        radianLen = len(radianPlugs)
        self.assertTrue(12 <= radianLen < totalLen)
        for radianPlug in radianPlugs:
            self.assertTrue(radianPlug in unitPlugs)
        self.assertTrue(self.transformNode.rotateX in radianPlugs)

        # Test typed plugs:
        typedPlugs = list(self.transformNode.iterXPlugs(attrType=omx.XAttrType.TYPED))
        typedLen = len(typedPlugs)
        self.assertTrue(15 < typedLen < totalLen)
        self.assertTrue(self.transformNode.wm in typedPlugs)

        # Test message plugs:
        messagePlugs = list(
            self.transformNode.iterXPlugs(attrType=omx.XAttrType.MESSAGE)
        )
        messageLen = len(messagePlugs)
        self.assertTrue(messageLen >= 5)
        self.assertTrue(self.transformNode.message in messagePlugs)

        # Test Enum plugs:
        enumPlugs = list(self.transformNode.iterXPlugs(attrType=omx.XAttrType.ENUM))
        enumLen = len(enumPlugs)
        self.assertTrue(enumLen >= 10)
        self.assertTrue(self.transformNode.nodeState in enumPlugs)

        # Test multiple types:
        enumOrMessagePlugs = list(
            self.transformNode.iterXPlugs(
                attrType=omx.XAttrType.ENUM | omx.XAttrType.MESSAGE
            )
        )
        self.assertEqual(len(enumOrMessagePlugs), enumLen + messageLen)
        for plug in enumOrMessagePlugs:
            self.assertTrue(plug in enumPlugs or plug in messagePlugs)

    def testIterXPlugsByState(self):
        keyablePlugs = list(
            self.transformNode.iterXPlugs(states=omx.XPlugState.KEYABLE)
        )
        self.assertEqual(len(keyablePlugs), 10)
        self.assertTrue(self.transformNode.tx in keyablePlugs)
        self.assertTrue(self.transformNode.ry in keyablePlugs)
        self.assertTrue(self.transformNode.sz in keyablePlugs)
        self.assertTrue(self.transformNode.v in keyablePlugs)

        lockedPlugs = list(self.transformNode.iterXPlugs(states=omx.XPlugState.LOCKED))
        self.assertEqual(len(lockedPlugs), 1)
        self.assertTrue(self.transformNode.ry in lockedPlugs)

        connectedPlugs = list(
            self.transformNode.iterXPlugs(states=omx.XPlugState.SOURCE_DEST)
        )
        sourcePlugs = list(self.transformNode.iterXPlugs(states=omx.XPlugState.SOURCE))
        destinationPlugs = list(
            self.transformNode.iterXPlugs(states=omx.XPlugState.DESTINATION)
        )
        self.assertEqual(len(connectedPlugs), len(destinationPlugs) + len(sourcePlugs))
        self.assertTrue(self.transformNode.sy in connectedPlugs)
        self.assertTrue(self.transformNode.sz in connectedPlugs)
        self.assertTrue(self.transformNode.sy in sourcePlugs)
        self.assertTrue(self.transformNode.sz in destinationPlugs)

    def testIterXPlugsByMultipleStates(self):
        # Get all keyable and settable plugs
        self.transformNode.tx.isKeyable = False
        self.transformNode.tx.isChannelBox = True

        # omx.XPlugState.KEYABLE|omx.XPlugState.CHANNELBOX means omx.XPlugState.VISIBLE,
        # but here we just demonstrate the support of bitwise OR for state filtering.
        keyableSettablePlugs = list(
            self.transformNode.iterXPlugs(
                states=(
                    omx.XPlugState.SETTABLE,
                    omx.XPlugState.KEYABLE | omx.XPlugState.CHANNELBOX,
                )
            )
        )
        self.assertEqual(len(keyableSettablePlugs), 8)
        self.assertTrue(self.transformNode.tx in keyableSettablePlugs)
        self.assertFalse(self.transformNode.ry in keyableSettablePlugs)
        self.assertFalse(self.transformNode.sz in keyableSettablePlugs)

        # Get all connected and keyable plugs
        connectedKeyablePlugs = list(
            self.transformNode.iterXPlugs(
                states=(omx.XPlugState.DESTINATION, omx.XPlugState.KEYABLE)
            )
        )
        self.assertEqual(connectedKeyablePlugs, [self.transformNode.sz])

        # Get all locked and keyable plugs
        lockedKeyablePlugs = list(
            self.transformNode.iterXPlugs(
                states=(omx.XPlugState.LOCKED, omx.XPlugState.KEYABLE)
            )
        )
        self.assertEqual(lockedKeyablePlugs, [self.transformNode.ry])

    def testIterXPlugsByTypeAndState(self):
        # Get all keyable angle plugs
        rotatePlugs = list(
            self.transformNode.iterXPlugs(
                attrType=omx.XAttrType.ANGLE,
                states=omx.XPlugState.KEYABLE,
            )
        )
        self.assertEqual(len(rotatePlugs), 3)
        self.assertTrue(self.transformNode.rx in rotatePlugs)
        self.assertTrue(self.transformNode.ry in rotatePlugs)
        self.assertTrue(self.transformNode.rz in rotatePlugs)

        # Get all settable and visible plugs:
        settableVisiblePlugs = list(
            self.transformNode.iterXPlugs(
                states=omx.XPlugState.VISIBLE,
                predicate=lambda p: omx.XPlugState.SETTABLE.matches(p),
            )
        )
        self.assertTrue(self.transformNode.tx in settableVisiblePlugs)
        self.assertFalse(self.transformNode.ry in settableVisiblePlugs)
        self.assertFalse(self.transformNode.sz in settableVisiblePlugs)

        # Get all unsettable but visible plugs:
        unsettableVisiblePlugs = list(
            self.transformNode.iterXPlugs(
                states=omx.XPlugState.VISIBLE,
                predicate=lambda p: omx.XPlugState.UNSETTABLE.matches(p),
            )
        )
        self.assertFalse(self.transformNode.tx in unsettableVisiblePlugs)
        self.assertTrue(self.transformNode.ry in unsettableVisiblePlugs)
        self.assertTrue(self.transformNode.sz in unsettableVisiblePlugs)

        # Get all translate plugs:
        translatePlugs = list(
            self.transformNode.iterXPlugs(
                attrType=omx.XAttrType.DISTANCE,
                states=omx.XPlugState.VISIBLE,
            )
        )
        self.assertTrue(len(translatePlugs) == 3)
        self.assertTrue(self.transformNode.tx in translatePlugs)
        self.assertTrue(self.transformNode.ty in translatePlugs)
        self.assertTrue(self.transformNode.tz in translatePlugs)

    def testIterDynamicXPlugs(self):
        # Get Dynamic plugs:
        self.assertFalse(
            list(self.transformNode.iterXPlugs(states=omx.XPlugState.DYNAMIC))
        )
        # Now add dynamic attr and test again
        attrFn = om2.MFnNumericAttribute()
        dynAttrName = "dynamicAttr"
        attrMOb = attrFn.create(dynAttrName, dynAttrName, om2.MFnNumericData.kFloat)
        mod = omx.currentModifier()
        mod.addAttribute(self.transformNode, attrMOb)
        omx.doIt()
        dynamicPlugs = list(
            self.transformNode.iterXPlugs(states=omx.XPlugState.DYNAMIC)
        )
        self.assertTrue(len(dynamicPlugs) == 1)
        self.assertTrue(str(dynamicPlugs[0]) == f"{self.transformNode}.{dynAttrName}")
