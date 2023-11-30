from AL import omx
from maya import cmds
from maya.api import OpenMaya as om2

# execute the code from common in maya script editor first.


def createInOMX(locCount, immediate):
    maxValue = getMaxValue(locCount)
    modifier = omx.newModifier()
    if immediate:
        # usually you use omx.currentModifier() but it is not guaranteed
        # to be a immediate one, like in our case here.
        modifier._immediate = immediate

    controller = omx.createDagNode("joint", nodeName="controller")

    fnAttr = om2.MFnNumericAttribute()
    attrObj = fnAttr.create("flash", "flash", om2.MFnNumericData.kInt)
    fnAttr.setMin(0)
    fnAttr.setMax(maxValue)
    modifier.addAttribute(controller.object(), attrObj)

    parent = omx.createDagNode("transform", nodeName="stars")

    stars = [None] * locCount
    toDelete = [None] * locCount

    for i in range(locCount):
        condition = omx.createDGNode("condition")

        loc = omx.createDagNode("transform", parent=parent)
        omx.createDagNode("locator", parent=loc)
        attrObj = fnAttr.create("flashIndex", "flashIndex", om2.MFnNumericData.kInt)
        fnAttr.setMin(0)
        fnAttr.setMax(maxValue)
        modifier.addAttribute(loc.object(), attrObj)

        testDel = omx.createDagNode("transform", parent=parent)
        omx.createDagNode("locator", parent=testDel)

        testDel.isValid()
        stars[i] = (loc, condition)
        toDelete[i] = testDel

    modifier.doIt()
    return controller, stars, toDelete


def editInOMX(controller, stars):
    maxValue = getMaxValue(len(stars))
    modifier = omx.currentModifier()

    controller.radius.setInt(10)
    controller.flash.isKeyable = True
    modifier.commandToExecute(f"setKeyframe -attribute flash -t 1 -v 0 {controller}")
    modifier.commandToExecute(
        f"setKeyframe -attribute flash -t 120 -v {maxValue} {controller}"
    )

    for loc, condition in stars:
        condition.colorIfTrue.setCompoundDouble((1.0, 1.0, 1.0))
        condition.colorIfFalse.setCompoundDouble((0.0, 0.0, 0.0))

        loc.overrideEnabled.setBool(True)
        loc.overrideColor.setInt(getRandomColor())

        loc.t.setCompoundDouble(getRandomPosition(maxValue))
        loc.s.setCompoundDouble(getRandomScale())

        # here we don't care about plug state change undoability as the whole
        # node creation is done in the same XModifier.
        # otherwise we would use loc.displayHandle.setLocked(True)
        loc.displayHandle.isLocked = True
        loc.overrideDisplayType.isLocked = True
        loc.overrideDisplayType.isLocked = False

        loc.flashIndex.setInt(getRandomIndex(maxValue))

        controller.r.connectTo(loc.r)
        controller.overrideShading.connectTo(loc.overrideShading)
        loc.overrideShading.disconnectFromSource()

        controller.flash.connectTo(condition.firstTerm)
        loc.flashIndex.connectTo(condition.secondTerm)
        condition.outColorR.connectTo(loc.visibility)

    modifier.doIt()


def renameInOMX(nodesToRename):
    modifier = omx.currentModifier()
    for node in nodesToRename:
        transformName = str(node)
        modifier.renameNode(node.object(), f"{transformName}New")
        modifier.renameNode(node.object(), f"{transformName}")

    modifier.doIt()


def queryInOMX(controller, stars):
    controller.flash.destinations()
    for loc, _ in stars:
        loc.isValid()
        loc.t.get()
        loc.wm[0].get()
        loc.overrideDisplayType.isLocked


def deleteInOMX(nodesToDelete):
    modifier = omx.currentModifier()
    for toDel in nodesToDelete:
        modifier.deleteNode(toDel.object())
        modifier.doIt()


def categorizedPerformanceTestInOMX():
    for num in NUM_NODES_LIST:
        for immediate in (True, False):
            cmds.file(new=True, force=True)
            with TotalPerfMeasurement(
                f"Deal with {num} nodes in AL.omx, immediate={immediate}"
            ) as measure:
                with measure.add(
                    f"Create {num}+ nodes in AL.omx, immediate={immediate}"
                ):
                    controller, stars, nodes = createInOMX(num, immediate=immediate)

                with measure.add(f"Edit {num}+ nodes in AL.omx, immediate={immediate}"):
                    editInOMX(controller, stars)

                with measure.add(
                    f"Rename {num} nodes in AL.omx, immediate={immediate}"
                ):
                    renameInOMX(nodes)

                with measure.add(
                    f"Query {num}+ nodes in AL.omx, immediate={immediate}"
                ):
                    queryInOMX(controller, stars)

                with measure.add(
                    f"Remove {num} nodes in AL.omx, immediate={immediate}"
                ):
                    deleteInOMX(nodes)


def totalPerformanceTestInOMX():
    for immediate in (True, False):
        for num in REFINED_NUM_NODES_LIST:
            cmds.file(new=True, force=True)
            with PerfMeasurement(
                f"Deal with {num} nodes in AL.omx, immediate={immediate}"
            ):
                controller, stars, nodes = createInOMX(num, immediate=immediate)
                editInOMX(controller, stars)
                renameInOMX(nodes)
                queryInOMX(controller, stars)
                deleteInOMX(nodes)


if __name__ == "__main__":
    categorizedPerformanceTestInOMX()
    # totalPerformanceTestInOMX()
