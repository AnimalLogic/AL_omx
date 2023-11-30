import pymel.core as pmc

# execute the code from common in maya script editor first.


def createInPyMel(locCount):
    maxValue = getMaxValue(locCount)

    controller = pmc.joint()
    controller.addAttr("flash", attributeType="long", min=0, max=maxValue)
    parent = pmc.createNode("transform", n="stars")

    stars = [None] * locCount
    toDelete = [None] * locCount

    for i in range(locCount):
        condition = pmc.createNode("condition")

        loc = pmc.spaceLocator()
        pmc.parent(loc, parent)
        loc.addAttr("flashIndex", at="long", min=0, max=maxValue)

        testDel = pmc.spaceLocator()
        pmc.parent(testDel, loc)

        pmc.objExists(testDel)
        stars[i] = (loc, condition)
        toDelete[i] = testDel

    return controller, stars, toDelete


def editInPyMel(controller, stars):
    maxValue = getMaxValue(len(stars))

    controller.radius.set(10)
    controller.flash.setKeyable(True)
    pmc.setKeyframe(controller.flash, time=(1,), value=0)
    pmc.setKeyframe(controller.flash, time=(120,), value=maxValue)

    for loc, condition in stars:
        condition.colorIfTrue.set([1.0, 1.0, 1.0])
        condition.colorIfFalse.set([0.0, 0.0, 0.0])

        loc.overrideEnabled.set(True)
        loc.overrideColor.set(getRandomColor())

        loc.t.set(getRandomPosition(maxValue))
        loc.s.set(getRandomScale())
        loc.displayHandle.lock()
        loc.overrideDisplayType.lock()
        loc.overrideDisplayType.unlock()

        loc.flashIndex.set(getRandomIndex(maxValue))

        controller.r.connect(loc.r)
        controller.overrideShading.connect(loc.overrideShading)
        controller.overrideShading.disconnect(loc.overrideShading)

        controller.flash.connect(condition.firstTerm)
        loc.flashIndex.connect(condition.secondTerm)
        condition.outColorR.connect(loc.visibility)


def renameInPyMel(nodesToRename):
    for node in nodesToRename:
        node.rename(f"{node}New")
        node.rename(str(node))


def queryInPyMel(controller, stars):
    controller.flash.outputs()
    for loc, _ in stars:
        pmc.objExists(loc)
        loc.t.get()
        loc.wm[0].get()
        loc.overrideDisplayType.isLocked()


def deleteInPyMel(nodesToDelete):
    for toDel in nodesToDelete:
        pmc.delete(toDel)


def categorizedPerformanceTestInPyMel():
    for num in NUM_NODES_LIST:
        pmc.system.newFile(force=True)
        with TotalPerfMeasurement(f"Deal with {num} nodes in PyMel") as measure:
            with measure.add(f"Create {num}+ nodes in PyMel"):
                controller, stars, nodes = createInPyMel(num)

            with measure.add(f"Edit {num}+ nodes in PyMel"):
                editInPyMel(controller, stars)

            with measure.add(f"Rename {num} nodes in PyMel"):
                renameInPyMel(nodes)

            with measure.add(f"Query {num}+ nodes in PyMel"):
                queryInPyMel(controller, stars)

            with measure.add(f"Remove {num} nodes in PyMel"):
                deleteInPyMel(nodes)


def totalPerformanceTestInPyMel():
    for num in REFINED_NUM_NODES_LIST:
        pmc.system.newFile(force=True)
        with PerfMeasurement(f"Deal with {num} nodes in PyMel"):
            controller, stars, nodes = createInPyMel(num)
            editInPyMel(controller, stars)
            renameInPyMel(nodes)
            queryInPyMel(controller, stars)
            deleteInPyMel(nodes)


if __name__ == "__main__":
    categorizedPerformanceTestInPyMel()
    # totalPerformanceTestInPyMel()
