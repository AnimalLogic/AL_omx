# Copyright (C) Animal Logic Pty Ltd. All rights reserved.

import unittest
import logging
from maya import cmds
from maya.api import OpenMaya as om2
from AL.maya2 import omx

logger = logging.getLogger(__name__)


class XModifierCase(unittest.TestCase):
    app = "maya"

    def setUp(self):
        cmds.file(new=True, f=True)

    def _buildReparentCase(self):
        oldParent = omx.createDagNode("transform", nodeName="oldParent")
        newParent = omx.createDagNode("transform", nodeName="newParent")
        child = omx.createDagNode("transform", nodeName="child", parent=oldParent)
        oldParentFn = oldParent.bestFn()
        oldParentFn.translateBy(om2.MVector(3.2, 5.9, 1.21), om2.MSpace.kTransform)
        oldParentFn.rotateBy(om2.MEulerRotation(1.6, 0.5, 3.9), om2.MSpace.kTransform)
        oldParentFn.scaleBy([1.0, 2.0, 3.0])
        oldParentFn.shearBy([0.1, 0.0, 0.2])

        childFn = child.bestFn()
        childFn.translateBy(om2.MVector(0.2, 0.0, 0.5), om2.MSpace.kTransform)
        childFn.rotateBy(om2.MEulerRotation(0, 0.5, 0.9), om2.MSpace.kTransform)
        childFn.scaleBy([1.0, 1.0, 0.5])

        return (oldParent, newParent, child)

    def testReparentNodeRelatively(self):
        _, newParent, child = self._buildReparentCase()
        mod = omx.newModifier()

        oldWorldMatrix = child.worldMatrix[0].get()
        oldt = child.t.get()
        oldr = child.r.get()
        olds = child.s.get()
        oldsr = child.sh.get()

        mod.reparentNode(child, newParent, False)
        mod.doIt()
        self.assertNotEqual(child.worldMatrix[0].get(), oldWorldMatrix)
        self.assertEqual(child.t.get(), oldt)
        self.assertEqual(child.r.get(), oldr)
        self.assertEqual(child.s.get(), olds)
        self.assertEqual(child.sh.get(), oldsr)

        mod.reparentNode(child, None, False)
        mod.doIt()
        self.assertNotEqual(child.worldMatrix[0].get(), oldWorldMatrix)
        self.assertEqual(child.t.get(), oldt)
        self.assertEqual(child.r.get(), oldr)
        self.assertEqual(child.s.get(), olds)
        self.assertEqual(child.sh.get(), oldsr)

    def testReparentNodeAbsolutely(self):
        _, newParent, child = self._buildReparentCase()
        mod = omx.newModifier()
        oldWorldMatrix = child.worldMatrix[0].get()

        mod.reparentNode(child, newParent, True)
        self.assertEqual(child.worldMatrix[0].get(), oldWorldMatrix)

        mod.reparentNode(child, None, True)
        self.assertEqual(child.worldMatrix[0].get(), oldWorldMatrix)

    def testReparentNodeCornerCases(self):
        oldParent, _, child = self._buildReparentCase()
        mod = omx.newModifier()
        # Make sure we raise Exception when user tries to reparent node to itself:
        self.assertRaises(RuntimeError, mod.reparentNode, child, child)

        # We should do nothing when it's already reparented to the node.
        self.assertEqual(omx.XNode(child.bestFn().parent(0)), oldParent)
        mod.reparentNode(child, oldParent)
        self.assertEqual(omx.XNode(child.bestFn().parent(0)), oldParent)

        # We should do nothing when the user tries to parent the node to world but it's already at world.
        mod.reparentNode(child, None)
        mod.reparentNode(child, None)

        # Error when trying to reparent a node to one of its child nodes
        self.assertRaises(RuntimeError, mod.reparentNode, oldParent, child)

    def testReparentNodeInputs(self):
        oldParent, newParent, child = self._buildReparentCase()
        mod = omx.newModifier()

        # We raise when user inputs non-dag node to reparent:
        self.assertRaises(TypeError, mod.reparentNode, omx.XNode("time1"))

        # We raise when user inputs non-dag node to reparent to:
        self.assertRaises(TypeError, mod.reparentNode, child, omx.XNode("time1"))

        # We support mobj as inputs:
        mod.reparentNode(child.object(), newParent.object(), False)

        # We support XNode as inputs:
        mod.reparentNode(child, oldParent, False)

        # Mixed:
        mod.reparentNode(child, newParent.object(), False)
        mod.reparentNode(child.object(), newParent, False)

    def testReparentNurbsCurves(self):
        t = omx.createDagNode("transform")
        shape = omx.createDagNode("nurbsCurve", nodeName="nurbsCurveShape")
        omx.currentModifier().reparentNode(shape, t)
        self.assertEqual(t, shape.basicFn().parent(0))

    def _addArrayAttr(self, xnode, attrName):
        fnAttr = om2.MFnNumericAttribute()
        attrObj = fnAttr.create(attrName, attrName, om2.MFnNumericData.kFloat)
        fnAttr.array = True
        xnode.bestFn().addAttribute(attrObj)

    def _setupConnectionTests(self):
        srcNode = omx.createDagNode("transform", nodeName="src")
        dstNode = omx.createDagNode("transform", nodeName="dst")
        self._addArrayAttr(srcNode, "testArrayAttr")
        self._addArrayAttr(dstNode, "testArrayAttr")

        values = [0, 1.0, 2.0]
        srcNode.testArrayAttr.set(values)
        self.assertFalse(dstNode.testArrayAttr.get())
        return (srcNode, dstNode, values)

    def test_arrayLevelConnection(self):
        srcNode, dstNode, oldValues = self._setupConnectionTests()
        mod = omx.newModifier()

        # Array level connection:
        mod.connect(srcNode.testArrayAttr, dstNode.testArrayAttr)
        mod.doIt()
        self.assertEqual(dstNode.testArrayAttr.get(), oldValues)
        mod.disconnect(srcNode.testArrayAttr, dstNode.testArrayAttr)
        mod.doIt()

        newValues = [3.0, 4.0, 5.0]
        srcNode.testArrayAttr.set(newValues)
        self.assertEqual(dstNode.testArrayAttr.get(), oldValues)

    def test_elementLevelAutoConnection(self):
        srcNode, dstNode, values = self._setupConnectionTests()
        mod = omx.newModifier()

        # Element level connection:
        mod.connect(
            srcNode.object(),
            srcNode.testArrayAttr.attribute(),
            dstNode.object(),
            dstNode.testArrayAttr.attribute(),
        )
        mod.doIt()
        self.assertEqual(dstNode.testArrayAttr.get(), values[:1])
        self.assertEqual(
            list(dstNode.testArrayAttr.getExistingArrayAttributeIndices()), [0]
        )
        mod.disconnect(srcNode.testArrayAttr[0], dstNode.testArrayAttr[0])
        mod.doIt()

    def test_nodeTrackingWithAPI(self):
        class CreationTracker:
            def __init__(self):
                omx._xmodifier.startTrackingNodes()
                self.created = []

            def addDagNodes(self, numNodes):
                for _ in range(numNodes):
                    self.created.append(
                        om2.MObjectHandle(omx.createDagNode("transform").object())
                    )

            def addDGNodes(self, numNodes):
                for _ in range(numNodes):
                    self.created.append(
                        om2.MObjectHandle(omx.createDGNode("blinn").object())
                    )

            def numCreated(self):
                return len(omx.queryTrackedNodes())

            def validResults(self):
                return self.created == omx.queryTrackedNodes()

            def __del__(self):
                omx._xmodifier.endTrackingNodes()

        # No tracking should be occuring yet
        omx.createDagNode("transform")
        omx.createDGNode("blinn")
        self.assertEqual(len(omx.queryTrackedNodes(queryAll=True)), 0)

        layer1 = CreationTracker()
        layer1.addDagNodes(2)
        layer1.addDGNodes(1)
        self.assertTrue(layer1.validResults())
        self.assertEqual(layer1.numCreated(), 3)
        self.assertEqual(len(omx.queryTrackedNodes(queryAll=True)), 3)

        layer2 = CreationTracker()
        layer2.addDagNodes(2)
        layer2.addDGNodes(1)
        self.assertTrue(layer2.validResults())
        self.assertEqual(layer2.numCreated(), 3)
        self.assertEqual(len(omx.queryTrackedNodes(queryAll=True)), 6)

        layer3 = CreationTracker()
        layer3.addDagNodes(2)
        layer3.addDGNodes(1)
        self.assertTrue(layer3.validResults())
        self.assertEqual(layer3.numCreated(), 3)
        self.assertEqual(len(omx.queryTrackedNodes(queryAll=True)), 9)
        del layer3

        layer2.addDagNodes(1)
        layer2.addDGNodes(1)
        self.assertTrue(layer2.validResults())
        self.assertEqual(layer2.numCreated(), 5)
        self.assertEqual(len(omx.queryTrackedNodes(queryAll=True)), 8)
        del layer2

        layer1.addDagNodes(1)
        self.assertTrue(layer1.validResults())
        self.assertEqual(layer1.numCreated(), 4)
        self.assertEqual(len(omx.queryTrackedNodes(queryAll=True)), 4)
        del layer1

        # Tracking ended, no tracking should be occuring
        omx.createDagNode("transform")
        omx.createDGNode("blinn")
        self.assertEqual(len(omx.queryTrackedNodes(queryAll=True)), 0)

    def test_nodeTrackingWithContextManager(self):
        # No tracking should be occuring yet
        omx.createDagNode("transform")
        omx.createDGNode("blinn")
        self.assertEqual(len(omx.queryTrackedNodes(queryAll=True)), 0)

        with omx.TrackCreatedNodes() as outerNodeTracker:
            omx.createDagNode("transform")
            omx.createDGNode("blinn")
            self.assertEqual(len(outerNodeTracker.trackedNodes()), 2)
            self.assertEqual(len(omx.queryTrackedNodes(queryAll=True)), 2)

            with omx.TrackCreatedNodes() as innerNodeTracker:
                omx.createDagNode("transform")
                omx.createDGNode("blinn")
                self.assertEqual(len(innerNodeTracker.trackedNodes()), 2)
                self.assertEqual(len(innerNodeTracker.trackedNodes(queryAll=True)), 4)
                self.assertEqual(len(omx.queryTrackedNodes(queryAll=True)), 4)

            self.assertEqual(len(outerNodeTracker.trackedNodes(queryAll=True)), 2)

        self.assertEqual(len(omx.queryTrackedNodes(queryAll=True)), 0)

    def test_nodeTrackingWithDecorator(self):
        # No tracking should be occuring yet
        omx.createDagNode("transform")
        omx.createDGNode("blinn")
        self.assertEqual(len(omx.queryTrackedNodes(queryAll=True)), 0)

        @omx.TrackCreatedNodes()
        def methodThatCreatesThings(nodesCreatedSoFar, numIterations):
            numIterations += 1

            omx.createDagNode("transform")
            omx.createDGNode("blinn")
            nodesCreatedSoFar += 2

            self.assertEqual(len(omx.queryTrackedNodes()), 2)
            self.assertEqual(
                len(omx.queryTrackedNodes(queryAll=True)), nodesCreatedSoFar
            )

            if numIterations <= 4:
                methodThatCreatesThings(nodesCreatedSoFar, numIterations)

            self.assertEqual(len(omx.queryTrackedNodes()), 2)
            self.assertEqual(
                len(omx.queryTrackedNodes(queryAll=True)), nodesCreatedSoFar
            )

        methodThatCreatesThings(0, 0)

        # All decorators have exited, should be no more tracking
        omx.createDagNode("transform")
        omx.createDGNode("blinn")
        self.assertEqual(len(omx.queryTrackedNodes(queryAll=True)), 0)

    def test_creationWithAllReturns(self):
        """Make sure user is able to get all the newly created nodes for omx.createDagNode()
        """
        nodeResult = omx.createDagNode("locator", returnAllCreated=False)
        self.assertTrue(isinstance(nodeResult, omx.XNode))
        self.assertEqual(nodeResult.basicFn().typeName, "locator")
        allResult = omx.createDagNode("locator", returnAllCreated=True)
        self.assertTrue(isinstance(allResult, list))
        self.assertEqual(len(allResult), 2)
        self.assertEqual(allResult[0].basicFn().typeName, "transform")
        self.assertEqual(allResult[1].basicFn().typeName, "locator")
