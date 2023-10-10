# Copyright (C) Animal Logic Pty Ltd. All rights reserved.

import unittest
import logging
from maya import cmds
from maya.api import OpenMaya as om2
from AL.maya2 import omx
from AL.maya2.omx.utils import _contexts as omu_contexts
from AL.maya2.omx.tests.utils import common

logger = logging.getLogger(__name__)


class XPlugCase(unittest.TestCase):
    app = "maya"

    def setUp(self):
        common.runTestsWithUndoEnabled(self)
        cmds.file(new=True, f=True)

    def testArrayElementXPlugAccess(self):
        trn = omx.createDagNode("transform", nodeName="myTrn")
        wmPlug = trn.worldMatrix
        self.assertTrue(wmPlug[0])
        self.assertFalse(wmPlug[0].isNull)
        self.assertEqual(str(wmPlug[0]), "myTrn.worldMatrix[0]")
        wmPlug[0].set(om2.MMatrix())
        self.assertTrue(0 in wmPlug)
        self.assertFalse(1 in wmPlug)

    def testCompoundChildXPlugAccess(self):
        trn = omx.createDagNode("transform", nodeName="myTrn")
        self.assertTrue(trn.t and not trn.t.isNull)
        self.assertTrue(trn.tx and not trn.tx.isNull)
        plug = trn.t["tx"]
        self.assertTrue(plug and not plug.isNull)
        plug = trn.t["translateX"]
        self.assertTrue(plug and not plug.isNull)
        with self.assertRaises(AttributeError):
            plug = trn.t["rnd"]

        self.assertTrue("tx" in trn.t)
        self.assertTrue("translateX" in trn.translate)
        self.assertTrue("translateZ" in trn.t)
        self.assertFalse("rnd" in trn.t)

    def testMultipleCompoundChildXPlugAccess(self):
        """Test XPlug accessibility for child compound attribute with multiple compound peer attributes.
        """
        trn = omx.createDagNode("transform", nodeName="myTrn")

        compoundAttrFn = om2.MFnCompoundAttribute()
        compoundAttr = compoundAttrFn.create("testCompound", "tstc")

        childCompoundAAttrFn = om2.MFnCompoundAttribute()
        childCompoundAAttr = childCompoundAAttrFn.create("compoundChildA", "cca")

        childCompoundBAttrFn = om2.MFnCompoundAttribute()
        childCompoundBAttr = childCompoundBAttrFn.create("compoundChildB", "ccb")

        descendantAAttrFn = om2.MFnNumericAttribute()
        descendantAAttrX = descendantAAttrFn.create(
            "descendantX", "ccdx", om2.MFnNumericData.kBoolean
        )
        descendantAAttrY = descendantAAttrFn.create(
            "descendantY", "ccdy", om2.MFnNumericData.kBoolean
        )

        childCompoundAAttrFn.addChild(descendantAAttrX)
        childCompoundAAttrFn.addChild(descendantAAttrY)

        descendantBAttrFn = om2.MFnNumericAttribute()
        descendantBAttrX = descendantBAttrFn.create(
            "descendantU", "ccdu", om2.MFnNumericData.kBoolean
        )
        descendantBAttrY = descendantBAttrFn.create(
            "descendantV", "ccdv", om2.MFnNumericData.kBoolean
        )

        childCompoundBAttrFn.addChild(descendantBAttrX)
        childCompoundBAttrFn.addChild(descendantBAttrY)

        compoundAttrFn.addChild(childCompoundAAttr)
        compoundAttrFn.addChild(childCompoundBAttr)
        trn.bestFn().addAttribute(compoundAttr)

        plug = trn.testCompound["compoundChildA"]
        self.assertTrue(plug and not plug.isNull)

        plug = trn.testCompound["descendantX"]
        self.assertTrue(plug and not plug.isNull)

        plug = trn.testCompound["compoundChildB"]
        self.assertTrue(plug and not plug.isNull)

        plug = trn.testCompound["descendantU"]
        self.assertTrue(plug and not plug.isNull)

    def testComplexCompoundChildXPlugAccess(self):
        trn = omx.createDagNode("transform", nodeName="myTrn")

        # Test obj.compound.compound.attr
        compoundAttrFn = om2.MFnCompoundAttribute()
        compoundAttr = compoundAttrFn.create("testCompound", "tstc")
        compoundAttrFn.array = True

        childCompoundAttrFn = om2.MFnCompoundAttribute()
        childCompoundAttr = childCompoundAttrFn.create("compoundChild", "ccc")

        descendantCompoundAttrFn = om2.MFnCompoundAttribute()
        descendantCompoundAttr = descendantCompoundAttrFn.create(
            "compoundDescendant", "ccd"
        )

        descendantAttrFn = om2.MFnNumericAttribute()
        descendantAttrX = descendantAttrFn.create(
            "descendantX", "ccdx", om2.MFnNumericData.kBoolean
        )
        descendantAttrY = descendantAttrFn.create(
            "descendantY", "ccdy", om2.MFnNumericData.kBoolean
        )

        descendantCompoundAttrFn.addChild(descendantAttrX)
        descendantCompoundAttrFn.addChild(descendantAttrY)
        childCompoundAttrFn.addChild(descendantCompoundAttr)
        compoundAttrFn.addChild(childCompoundAttr)
        trn.bestFn().addAttribute(compoundAttr)

        xplug = trn.testCompound[0]
        self.assertTrue("compoundChild" in xplug)
        self.assertTrue("compoundDescendant" in xplug)
        self.assertTrue("descendantX" in xplug)
        self.assertTrue("descendantY" in xplug)

        self.assertTrue(xplug["compoundChild"] and not xplug["compoundChild"].isNull)
        self.assertTrue(
            xplug["compoundDescendant"] and not xplug["compoundDescendant"].isNull
        )
        self.assertTrue(xplug["descendantX"] and not xplug["descendantX"].isNull)
        self.assertTrue(xplug["descendantY"] and not xplug["descendantY"].isNull)
        self.assertTrue(
            xplug["compoundChild"]["compoundDescendant"]
            and not xplug["compoundChild"]["compoundDescendant"].isNull
        )
        self.assertTrue(
            xplug["compoundChild"]["compoundDescendant"]["descendantX"]
            and not xplug["compoundChild"]["compoundDescendant"]["descendantX"].isNull
        )

    def testStrings(self):
        trn1 = omx.createDagNode("transform", nodeName="myTrn1")
        trn2 = omx.createDagNode("transform", nodeName="myTrn2")
        child1 = omx.createDagNode("transform", nodeName="child", parent=trn1)
        child2 = omx.createDagNode("transform", nodeName="child", parent=trn2)

        self.assertEqual(str(trn1.translateX), "myTrn1.translateX")
        self.assertEqual(str(child1.translateX), "myTrn1|child.translateX")
        self.assertEqual(str(child2.translateX), "myTrn2|child.translateX")

        timeNode = omx.XNode("time1")
        self.assertEqual(str(timeNode.outTime), "time1.outTime")

    def testSetLocked(self):
        trn = omx.createDagNode("transform", nodeName="myTrn1")
        tx = trn.tx
        self.assertFalse(tx.isLocked)
        tx.setLocked(True)
        self.assertTrue(tx.isLocked)
        for _ in range(10):
            cmds.undo()
            self.assertFalse(tx.isLocked)
            cmds.redo()
            self.assertTrue(tx.isLocked)

    def testSetKeyable(self):
        trn = omx.createDagNode("transform", nodeName="myTrn1")
        tx = trn.tx
        self.assertTrue(tx.isKeyable)
        tx.setKeyable(False)
        self.assertFalse(tx.isKeyable)
        for _ in range(10):
            cmds.undo()
            self.assertTrue(tx.isKeyable)
            cmds.redo()
            self.assertFalse(tx.isKeyable)

    def testSetChannelBox(self):
        trn = omx.createDagNode("transform", nodeName="myTrn1")
        tx = trn.tx
        # Note: the keyable attribute will show in channelBox regardless of isChannelBox state.
        # You only see isChannelBox effect on UI for nonkeyable attributes.
        self.assertFalse(tx.isChannelBox)
        tx.setChannelBox(True)
        self.assertTrue(tx.isChannelBox)
        for _ in range(10):
            cmds.undo()
            self.assertFalse(tx.isChannelBox)
            cmds.redo()
            self.assertTrue(tx.isChannelBox)

    def testConnection(self):
        trn = omx.createDagNode("transform", nodeName="myTrn1")
        self._testConnection(trn)
        trn.tx.isLocked = True
        trn.ty.isLocked = True
        self._testConnection(trn)

    def _testConnection(self, node):
        self.assertFalse(node.ty.isDestination)
        node.tx.connectTo(node.ty)
        self.assertTrue(node.ty.isDestination)
        node.ty.disconnectFromSource()
        self.assertFalse(node.ty.isDestination)
        node.ty.connectFrom(node.tx)
        self.assertTrue(node.ty.isDestination)
        node.ty.disconnectFromSource()
        self.assertFalse(node.ty.isDestination)

    def testArrayOfCompoundChildPlug(self):
        """Make sure the child plug can be accessed without a type error from an array of compound plugs.
        e.g. 'blendshapeNode.inputTarget[0].baseWeights'
        """
        cubeA = cmds.polyCube()[0]
        cubeB = cmds.polyCube()[0]
        blendShapeMayaDeformer = "testBlendshape"
        blendShapeMayaDeformer = cmds.blendShape(
            cubeA, cubeB, n=blendShapeMayaDeformer
        )[0]
        bsNode = omx.XNode(blendShapeMayaDeformer)
        self.assertTrue(bsNode.isValid())
        arrayPlug = bsNode.inputTarget[0]["baseWeights"]
        self.assertFalse(arrayPlug.isNull)

    def testEnumNames(self):
        node = omx.createDagNode("transform")

        # For enum with no names, it should be an empty list:
        cmds.addAttr(str(node), ln="testAttrNoName", at="enum", k=1)
        self.assertEqual(node.testAttrNoName.enumNames(), tuple())

        # Typical use:
        cmds.addAttr(
            str(node), ln="testAttrWithNames", at="enum", en="Green:Blue:Yellow", k=1
        )
        self.assertEqual(
            node.testAttrWithNames.enumNames(), ("Green", "Blue", "Yellow")
        )

        # For non-enum attribute, it should return None:
        cmds.addAttr(str(node), ln="testOtherName", k=1)
        self.assertTrue(node.testOtherName.enumNames() is None)

    def testSetEnumByName(self):
        node = omx.createDagNode("transform")
        cmds.addAttr(str(node), ln="testAttr", at="enum", en="Green:Blue:Yellow", k=1)
        node.testAttr.set(0)
        self.assertEqual(node.testAttr.get(), 0)
        node.testAttr.set("Blue")
        self.assertEqual(node.testAttr.get(), 1)
        node.testAttr.set("Yellow")
        self.assertEqual(node.testAttr.get(), 2)

        # We require strict match of enum name when setting enum attr by enum name:
        self.assertRaises(ValueError, node.testAttr.set, "blue")
        self.assertRaises(ValueError, node.testAttr.set, "")
        self.assertRaises(ValueError, node.testAttr.set, " Blue")

    def testNextAvailable(self):
        nodeA = omx.createDagNode("transform")
        nodeB = omx.createDagNode("transform")

        nodeA.borderConnections[0].connectFrom(nodeB.message)

        nextPlug = nodeA.borderConnections.nextAvailable()
        self.assertEqual(nextPlug.logicalIndex(), 1)

    def testSetPlugAngleValue(self):
        node = omx.createDagNode("transform")
        degreePlug = node.rx
        normalPlug = node.tx
        data = (
            (10.0, 0.17453292519943295, True),
            (10.0, 572.957795, False),
            (10.0, 572.957795, None),
            (30.0, 0.5235987755982988, True),
            (30.0, 1718.873385, False),
            (30.0, 1718.873385, None),
        )
        for inputValue, valueInDiffUnit, asDegrees in data:
            if asDegrees is None:
                degreePlug.set(inputValue)
                self.assertAlmostEqual(degreePlug.get(), inputValue, 4)

                normalPlug.set(inputValue)
                self.assertAlmostEqual(degreePlug.get(), inputValue, 4)
                continue

            # for angle plug, asDegrees flag should make a difference.
            degreePlug.set(inputValue, asDegrees=asDegrees)
            self.assertAlmostEqual(degreePlug.get(asDegrees=asDegrees), inputValue, 4)
            self.assertAlmostEqual(
                degreePlug.get(asDegrees=not asDegrees), valueInDiffUnit, 4
            )

            # for non-angle plug, asDegrees flag does not make a difference.
            normalPlug.set(inputValue, asDegrees=asDegrees)
            self.assertAlmostEqual(normalPlug.get(asDegrees=asDegrees), inputValue, 4)
            self.assertAlmostEqual(
                normalPlug.get(asDegrees=not asDegrees), inputValue, 4
            )
