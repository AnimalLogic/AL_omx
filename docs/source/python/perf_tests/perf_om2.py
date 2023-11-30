from maya.api import OpenMaya as om2
from maya import cmds

# execute the code from common in maya script editor first.


def createInOM2(modifier, locCount):
    maxValue = getMaxValue(locCount)

    controller = modifier.createNode("joint")
    modifier.renameNode(controller, "controller")

    fnAttr = om2.MFnNumericAttribute()
    attrObj = fnAttr.create("flash", "flash", om2.MFnNumericData.kInt)
    fnAttr.setMin(0)
    fnAttr.setMax(maxValue)
    modifier.addAttribute(controller, attrObj)

    parent = modifier.createNode("transform")
    modifier.renameNode(parent, "stars")

    stars = [None] * locCount
    toDelete = [None] * locCount
    for i in range(locCount):
        condition = om2.MDGModifier.createNode(modifier, "condition")

        loc = modifier.createNode("transform", parent=parent)
        modifier.createNode("locator", parent=loc)
        attrObj = fnAttr.create("flashIndex", "flashIndex", om2.MFnNumericData.kInt)
        fnAttr.setMin(0)
        fnAttr.setMax(maxValue)
        modifier.addAttribute(loc, attrObj)

        testDel = modifier.createNode("transform", parent=parent)
        modifier.createNode("locator", parent=testDel)

        om2.MObjectHandle(testDel).isValid()
        stars[i] = (loc, condition)
        toDelete[i] = testDel

    modifier.doIt()
    return controller, stars, toDelete


def editInOM2(modifier, controller, stars):
    maxValue = getMaxValue(len(stars))
    controllerFn = om2.MFnDependencyNode(controller)
    plug = controllerFn.findPlug("radius", True)
    modifier.newPlugValueInt(plug, 10)

    plug = controllerFn.findPlug("flash", True)
    plug.isKeyable = True
    modifier.commandToExecute(
        f"setKeyframe -attribute flash -t 1 -v 0 {controllerFn.name()}"
    )
    modifier.commandToExecute(
        f"setKeyframe -attribute flash -t 120 -v {maxValue} {controllerFn.name()}"
    )

    colorIfTrueNames = ("colorIfTrueR", "colorIfTrueG", "colorIfTrueB")
    colorIfFalseNames = ("colorIfFalseR", "colorIfFalseG", "colorIfFalseB")

    translation = ("tx", "ty", "tz")
    scale = ("sx", "sy", "sz")
    for loc, condition in stars:
        locFn = om2.MFnDependencyNode(loc)
        conditionFn = om2.MFnDependencyNode(condition)
        for trueAttr in colorIfTrueNames:
            plug = conditionFn.findPlug(trueAttr, True)
            modifier.newPlugValueDouble(plug, 1.0)

        for falseAttr in colorIfFalseNames:
            plug = conditionFn.findPlug(falseAttr, True)
            modifier.newPlugValueDouble(plug, 0.0)

        plug = locFn.findPlug("overrideEnabled", True)
        modifier.newPlugValueBool(plug, True)

        plug = locFn.findPlug("overrideColor", True)
        modifier.newPlugValueInt(plug, getRandomColor())

        for name, value in zip(translation, getRandomPosition(maxValue)):
            plug = locFn.findPlug(name, True)
            modifier.newPlugValueDouble(plug, value)

        for name, value in zip(scale, getRandomScale()):
            plug = locFn.findPlug(name, True)
            modifier.newPlugValueDouble(plug, value)

        plug = locFn.findPlug("displayHandle", True)
        plug.isLocked = True

        plug = locFn.findPlug("overrideDisplayType", True)
        plug.isLocked = True
        plug.isLocked = False

        plug = locFn.findPlug("flashIndex", True)
        modifier.newPlugValueInt(plug, getRandomIndex(maxValue))

        src = controllerFn.findPlug("r", True)
        dst = locFn.findPlug("r", True)
        modifier.connect(src, dst)

        src = controllerFn.findPlug("overrideShading", True)
        dst = locFn.findPlug("overrideShading", True)
        modifier.connect(src, dst)
        modifier.disconnect(src, dst)

        src = controllerFn.findPlug("flash", True)
        dst = conditionFn.findPlug("firstTerm", True)
        modifier.connect(src, dst)

        src = locFn.findPlug("flashIndex", True)
        dst = conditionFn.findPlug("secondTerm", True)
        modifier.connect(src, dst)

        src = conditionFn.findPlug("outColorR", True)
        dst = locFn.findPlug("visibility", True)
        modifier.connect(src, dst)

    modifier.doIt()


def renameInOM2(modifier, nodesToRename):
    for node in nodesToRename:
        transformName = str(node)
        modifier.renameNode(node, f"{transformName}New")
        modifier.renameNode(node, f"{transformName}")

    modifier.doIt()


def queryInOM2(controller, stars):
    translation = ("tx", "ty", "tz")
    controllerFn = om2.MFnDependencyNode(controller)
    controllerFn.findPlug("flash", True).destinations()
    for loc, _ in stars:
        om2.MObjectHandle(loc).isValid()
        locFn = om2.MFnDependencyNode(loc)
        [locFn.findPlug(n, True).asDouble() for n in translation]
        wm0Plug = locFn.findPlug("wm", True).elementByLogicalIndex(0)
        attrData = om2.MFnMatrixData(wm0Plug.asMObject()).matrix()
        [attrData[i] for i in range(len(attrData))]
        locFn.findPlug("overrideDisplayType", True).isLocked


def deleteInOM2(modifier, nodesToDelete):
    for toDel in nodesToDelete:
        modifier.deleteNode(toDel)
        modifier.doIt()


def categorizedPerformanceTestInOM2():
    for num in NUM_NODES_LIST:
        cmds.file(new=True, force=True)
        with TotalPerfMeasurement(f"Deal with {num} nodes in om2") as measure:
            modifier = om2.MDagModifier()
            with measure.add(f"Create {num}+ nodes in om2"):
                controller, stars, nodes = createInOM2(modifier, num)

            with measure.add(f"Edit {num}+ nodes in om2"):
                editInOM2(modifier, controller, stars)

            with measure.add(f"Rename {num} nodes in om2"):
                renameInOM2(modifier, nodes)

            with measure.add(f"Query {num}+ nodes in om2"):
                queryInOM2(controller, stars)

            with measure.add(f"Remove {num} nodes in om2"):
                deleteInOM2(modifier, nodes)


def totalPerformanceTestInOM2():
    for num in REFINED_NUM_NODES_LIST:
        cmds.file(new=True, force=True)
        with PerfMeasurement(f"Deal with {num} nodes in om2"):
            modifier = om2.MDagModifier()
            controller, stars, nodes = createInOM2(modifier, num)
            editInOM2(modifier, controller, stars)
            renameInOM2(modifier, nodes)
            queryInOM2(controller, stars)
            deleteInOM2(modifier, nodes)


if __name__ == "__main__":
    categorizedPerformanceTestInOM2()
    # totalPerformanceTestInOM2()
