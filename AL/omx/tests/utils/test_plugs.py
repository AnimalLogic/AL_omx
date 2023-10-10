# Copyright (C) Animal Logic Pty Ltd. All rights reserved.

import unittest
from maya import cmds
from maya.api import OpenMaya as om2
from AL.maya2.omx.utils import _nodes
from AL.maya2.omx.utils import _plugs
from AL.maya2.omx.tests.utils import common


@_plugs._plugLockElision  # pylint: disable=protected-access
def _getPlugLockStateWithElision(plug, _wasLocked=False):
    return plug.isLocked


class PlugReadAndWriteOnNodeCase(unittest.TestCase):
    app = "maya"

    def setUp(self):
        cmds.file(new=True, f=True)
        common.setupSimplestScene()

    def test_findPlug(self):
        cmds.polyCube()
        cmds.namespace(add="testNs")
        cmds.rename("pCube2", ":testNs:pCube2")
        cube1 = _nodes.findNode("pCube1")
        cube2 = _nodes.findNode("testNs:pCube2")

        # list of tuples with: (expected result, name arg, nodeObj arg)
        testPlugs = [
            # test full path or with node object
            ("testNs:pCube2.translateX", "testNs:pCube2.tx", None),
            ("testNs:pCube2.translateX", "tx", cube2),
            ("pCube1.translateX", "pCube1.tx", None),
            ("pCube1.translateX", "tx", cube1),
            # short and long plug names
            ("pCube1.translateX", "pCube1.tx", None),
            ("pCube1.translateX", "pCube1.t.tx", None),
            ("pCube1.translateX", "pCube1.translateX", None),
            ("pCube1.translateX", "pCube1.translate.translateX", None),
            # (uninitialised) array plugs
            ("pCube1.worldMatrix[0]", "pCube1.worldMatrix[0]", None),
            ("pCube1.worldMatrix[5]", "pCube1.worldMatrix[5]", None),
            # (uninitialised) array of compounds
            (
                "pCube1.instObjGroups[0].objectGroups[1]",
                "pCube1.instObjGroups[0].objectGroups[1]",
                None,
            ),
            (
                "pCube1.instObjGroups[5].objectGroups[3].objectGroupId",
                "pCube1.instObjGroups[5].objectGroups[3].objectGroupId",
                None,
            ),
        ]

        for result, name, node in testPlugs:
            p = _plugs.findPlug(name, node=node)
            self.assertEqual(p.name(), result)

        # test with invalid input name
        p = _plugs.findPlug("invalidPlugName", node=cube1)
        self.assertEqual(p, None)

        # test with invalid node object
        cmds.delete("testNs:pCube2")
        p = _plugs.findPlug("tx", node=cube2)
        self.assertEqual(p, None)

        # test weird rotatePivot plug case (that fails with MSelectionList.getPlug())
        j = cmds.createNode("joint")
        p = _plugs.findPlug(f"{j}.rotatePivot")
        self.assertEqual(p.name(), j + ".rotatePivot")

        # test fallback when passing indexed plug to MFnDependencyNode.findPlug()
        cmds.circle()
        p = _plugs.findPlug("nurbsCircleShape1.controlPoints[0]")
        self.assertEqual(p.name(), "nurbsCircleShape1.controlPoints[0]")

    def test_plugFromNode(self):
        node = _nodes.findNode("pCube1")
        self.assertTrue(node)

        # Test getting array element attribute
        plug = _plugs.findPlug("worldMatrix[0]", node)
        self.assertTrue(plug and not plug.isNull)

        # Test getting compound attribute
        plug = _plugs.findPlug("boundingBoxMin", node)
        self.assertTrue(plug and not plug.isNull)

    def test_plugEnumNames(self):
        grp = cmds.group(em=True)

        # For enum with no names, it should be an empty list:
        cmds.addAttr(grp, ln="testAttrNoName", at="enum", k=1)
        plug = _plugs.findPlug(f"{grp}.testAttrNoName")
        self.assertTrue(plug)
        self.assertFalse(plug.isNull)
        self.assertEqual(_plugs.plugEnumNames(plug), tuple())

        # Typical use:
        cmds.addAttr(
            grp, ln="testAttrWithNames", at="enum", en="Green:Blue:Yellow", k=1
        )
        plug = _plugs.findPlug(f"{grp}.testAttrWithNames")
        self.assertTrue(plug)
        self.assertFalse(plug.isNull)
        self.assertEqual(_plugs.plugEnumNames(plug), ("Green", "Blue", "Yellow"))

        # For non-enum attribute, it should return None:
        cmds.addAttr(grp, ln="testOtherName", k=1)
        plug = _plugs.findPlug(f"{grp}.testOtherName")
        self.assertTrue(plug)
        self.assertFalse(plug.isNull)
        self.assertTrue(_plugs.plugEnumNames(plug) is None)

    def test_nodeDotAttrFromPlug(self):
        cmds.select("pCube1")
        cmds.group(name="group1")
        cmds.duplicate("group1")

        plug = _plugs.findPlug("group1|pCube1.tx")
        plugPath = plug.partialName(includeNodeName=False, useFullAttributePath=True)
        nodeDotAttr = _plugs.nodeDotAttrFromPlug(plug)
        self.assertEqual(nodeDotAttr, f"group1|pCube1.{plugPath}")

    def test_setNumericalPlugValueWithModifier(self):
        node = _nodes.findNode("pCube1")
        self.assertTrue(node)
        attrNames = ["tx", "rx", "sz"]
        for attrName in attrNames:
            initValue = 1
            plug = _plugs.findPlug(attrName, node)
            self.assertTrue(plug and not plug.isNull)
            _plugs.setValueOnPlug(plug, initValue)

            modifier = om2.MDGModifier()
            values = [-2, 4, 5, 2.5]
            # Test doit immediately:
            for v in values:
                _plugs.setValueOnPlug(plug, v, modifier=modifier, doIt=True)
                self.assertEqual(_plugs.valueFromPlug(plug), v)

                fnType, fn = _plugs.attributeTypeAndFnFromPlug(plug)
                self.assertEqual(fn.object(), plug.attribute())
                self.assertTrue(isinstance(fnType, int))

                value, fnType, attrType = _plugs.valueAndTypesFromPlug(plug)
                self.assertEqual(value, v)
                self.assertTrue(isinstance(fnType, int))
                self.assertTrue(isinstance(attrType, int))

            # Test undo:
            modifier.undoIt()
            self.assertEqual(_plugs.valueFromPlug(plug), initValue)

            # Test deferred doIt:
            for v in values:
                _plugs.setValueOnPlug(plug, v, modifier=modifier, doIt=False)

            self.assertEqual(_plugs.valueFromPlug(plug), initValue)
            modifier.doIt()
            self.assertEqual(_plugs.valueFromPlug(plug), values[-1])

            # Test undo:
            modifier.undoIt()
            self.assertEqual(_plugs.valueFromPlug(plug), initValue)

            # Test without modifier input:
            for v in values:
                _plugs.setValueOnPlug(plug, v)
                self.assertEqual(_plugs.valueFromPlug(plug), v)

            # No undo bro!
            modifier.undoIt()
            self.assertEqual(_plugs.valueFromPlug(plug), values[-1])

    def test_getGenericAttributeValue(self):
        # Test getting value from generic plug:
        convetNode = cmds.createNode("unitConversion")
        cmds.setAttr("pCube1.rx", 3.3)
        cmds.connectAttr("pCube1.rx", f"{convetNode}.input")
        attributes = ["input", "output"]
        for attr in attributes:
            plugPath = f"{convetNode}.{attr}"
            outputPlug = _plugs.findPlug(plugPath)
            value = _plugs.valueFromPlug(outputPlug)
            self.assertEqual(cmds.getAttr(plugPath), value)
            self.assertTrue(isinstance(value, float))

    def test_setArrayAttributeValueWithDict(self):
        cmds.createNode("blendShape", name="bs")
        bsWeightsPlug = _plugs.findPlug("bs.weight")
        self.assertIsNotNone(bsWeightsPlug)
        _plugs.setValueOnPlug(bsWeightsPlug, {0: 0.0, 1: 1.0, 2: 2.0, "3": 3.0})
        self.assertEqual(_plugs.valueFromPlug(bsWeightsPlug), [0.0, 1.0, 2.0, 3.0])

    def test_setNumericCompoundPlugValueWithModifier(self):
        node = _nodes.findNode("pCube1")
        self.assertTrue(node)
        plug = _plugs.findPlug("t", node)
        modifier = om2.MDGModifier()
        newValues = [0.5, 2, 3.1]
        initValues = _plugs.valueFromPlug(plug)
        self.assertNotEqual(newValues, initValues)
        _plugs.setValueOnPlug(plug, newValues, modifier=modifier, doIt=True)
        self.assertEqual(_plugs.valueFromPlug(plug), newValues)
        modifier.undoIt()
        self.assertEqual(_plugs.valueFromPlug(plug), initValues)

    def test_setNonNumericCompoundPlugValueWithModifier(self):
        node = _nodes.findNode("pCube1")
        self.assertTrue(node)
        plug = _plugs.findPlug("drawOverride", node)
        modifier = om2.MDGModifier()
        newValues = {
            "hideOnPlayback": False,
            "overrideColor": 0,
            "overrideColorRGB": [0.5, 0.5, 1.0],
            "overrideDisplayType": 0,
            "overrideEnabled": True,
            "overrideLevelOfDetail": 0,
            "overridePlayback": True,
            "overrideRGBColors": True,
            "overrideShading": True,
            "overrideTexturing": True,
            "overrideVisibility": True,
        }
        initValues = _plugs.valueFromPlug(plug)
        self.assertNotEqual(newValues, initValues)
        _plugs.setValueOnPlug(plug, newValues, modifier=modifier, doIt=True)
        self.assertEqual(_plugs.valueFromPlug(plug), newValues)
        modifier.undoIt()
        self.assertEqual(_plugs.valueFromPlug(plug), initValues)

    def test_getSimpleFloatArrayPlugValue(self):
        cube = cmds.polyCube()[0]
        attr = "testFloatArrayAttr"
        cmds.addAttr(cube, dt="floatArray", longName=attr)
        nodeDotAttr = f"{cube}.{attr}"
        expectedValues = [0, 1.5, 3.1]
        cmds.setAttr(nodeDotAttr, expectedValues, type="floatArray")
        plug = _plugs.findPlug(nodeDotAttr)
        self.assertFalse(plug.isNull)
        actualValue = _plugs.valueFromPlug(plug)
        self.assertTrue(actualValue)
        for i, v in enumerate(actualValue):
            self.assertAlmostEqual(v, expectedValues[i], 4)

    def test_setEnumAttributeByEnumName(self):
        grp = cmds.group(em=True)
        cmds.addAttr(grp, ln="testAttr", at="enum", en="Green:Blue:Yellow", k=1)
        attr = f"{grp}.testAttr"
        cmds.setAttr(attr, 0)
        plug = _plugs.findPlug(attr)
        self.assertFalse(plug.isNull)
        self.assertEqual(_plugs.valueFromPlug(plug), 0)
        _plugs.setValueOnPlug(plug, "Yellow")
        self.assertEqual(_plugs.valueFromPlug(plug), 2)
        _plugs.setValueOnPlug(plug, "Blue")
        self.assertEqual(_plugs.valueFromPlug(plug), 1)

        # Test Undo/Redo
        modifier = om2.MDGModifier()
        _plugs.setValueOnPlug(plug, "Green", modifier=modifier)
        self.assertEqual(_plugs.valueFromPlug(plug), 0)
        modifier.undoIt()
        self.assertEqual(_plugs.valueFromPlug(plug), 1)
        modifier.doIt()
        self.assertEqual(_plugs.valueFromPlug(plug), 0)

        # We require strict match of enum name when setting enum attr by enum name:
        self.assertRaises(ValueError, _plugs.setValueOnPlug, plug, "blue")
        self.assertRaises(ValueError, _plugs.setValueOnPlug, plug, "")
        self.assertRaises(ValueError, _plugs.setValueOnPlug, plug, " Blue")

    def test_createAttributeDummy(self):
        dummyMobj = _plugs.createAttributeDummy()
        self.assertTrue(om2.MObjectHandle(dummyMobj).isValid())
        plug = _plugs.findPlug("kMessage", dummyMobj)
        self.assertTrue(_plugs.plugIsValid(plug))

    def _prepareArrayAttribute(self):
        mobj = _nodes.findNode("pCube1")
        fnAttr = om2.MFnNumericAttribute()
        attr = fnAttr.create("arrayAttr", "arrayAttr", om2.MFnNumericData.kBoolean)
        fnAttr.array = True
        mfn_dep = om2.MFnDependencyNode(mobj)
        mfn_dep.addAttribute(attr)
        return om2.MPlug(mobj, attr)

    def test_getOrExtendMPlugArray(self):
        arrayPlug = self._prepareArrayAttribute()
        dummyMobj = _plugs.createAttributeDummy()

        # extend the array to get index 2:
        element2 = _plugs.getOrExtendMPlugArray(arrayPlug, 2, dummy=dummyMobj)
        self.assertTrue(element2)
        self.assertEqual(element2.logicalIndex(), 2)
        aCount = arrayPlug.evaluateNumElements()
        self.assertEqual(aCount, 3)

        # since we have enough elements, getting an existing index should not extend it:
        element1 = _plugs.getOrExtendMPlugArray(arrayPlug, 1)
        self.assertTrue(element1)
        self.assertEqual(element1.logicalIndex(), 1)
        aCount = arrayPlug.evaluateNumElements()
        self.assertEqual(aCount, 3)

        # extend the array to get index 3:
        element3 = _plugs.getOrExtendMPlugArray(arrayPlug, 3)
        self.assertTrue(element3)
        self.assertEqual(element3.logicalIndex(), 3)
        aCount = arrayPlug.evaluateNumElements()
        self.assertEqual(aCount, 4)

    def test_findSubplugByName(self):
        mobj = _nodes.findNode("pCube1")
        tPlug = _plugs.findPlug("t", mobj)
        txPlug = _plugs.findSubplugByName(tPlug, "tx")
        self.assertTrue(txPlug)
        self.assertTrue(_plugs.plugIsValid(txPlug))
        self.assertTrue(txPlug.parent() == tPlug)

    def test_nextAvailableElementIndex(self):
        arrayPlug = self._prepareArrayAttribute()
        idx = _plugs.nextAvailableElementIndex(arrayPlug)
        self.assertEqual(idx, 0)
        elementPlug = _plugs.nextAvailableElement(arrayPlug)
        self.assertEqual(elementPlug.logicalIndex(), 0)

        # now occupy index 1
        dummyMobj = _plugs.createAttributeDummy()
        srcPlug = _plugs.findPlug("kMessage", dummyMobj)
        cmds.connectAttr(str(srcPlug), str(elementPlug))

        idx = _plugs.nextAvailableElementIndex(arrayPlug)
        self.assertEqual(idx, 1)

        # skip index 1 but occupy 3, the next available index should be 1:
        cmds.connectAttr(str(srcPlug), f"{arrayPlug}[3]")
        idx = _plugs.nextAvailableElementIndex(arrayPlug)
        self.assertEqual(idx, 1)
        elementPlug = _plugs.nextAvailableElement(arrayPlug)
        self.assertEqual(elementPlug.logicalIndex(), 1)

    def test_plugLockElision(self):
        mobj = _nodes.findNode("pCube1")
        txPlug = _plugs.findPlug("tx", mobj)
        txPlug.isLocked = True
        self.assertTrue(txPlug.isLocked)
        self.assertFalse(_getPlugLockStateWithElision(txPlug))
        self.assertTrue(txPlug.isLocked)

    def test_iterAttributeFnTypesAndClasses(self):
        for fnType, fnCls in _plugs.iterAttributeFnTypesAndClasses():
            self.assertTrue(issubclass(fnCls, om2.MFnAttribute))
            self.assertTrue(isinstance(fnType, int))
