from maya import cmds

# execute the code from common in maya script editor first.


def createInCmds(locCount):
    maxValue = getMaxValue(locCount)

    controller = cmds.joint()
    cmds.addAttr(controller, ln="flash", at="long", min=0, max=maxValue)

    stars = [None] * locCount
    toDelete = [None] * locCount
    parent = cmds.createNode("transform", n="stars")

    for i in range(locCount):
        condition = cmds.createNode("condition")

        (loc,) = cmds.spaceLocator()
        cmds.parent(loc, parent)
        cmds.addAttr(loc, ln="flashIndex", at="long", min=0, max=maxValue)

        (testDel,) = cmds.spaceLocator()
        cmds.parent(testDel, loc)

        cmds.objExists(testDel)
        stars[i] = (loc, condition)
        toDelete[i] = testDel

    return controller, stars, toDelete


def editInCmds(controller, stars):
    maxValue = getMaxValue(len(stars))

    cmds.setAttr(f"{controller}.radius", 10)
    cmds.setAttr(f"{controller}.flash", keyable=True)
    cmds.setKeyframe(f"{controller}.flash", time=(1,), value=0)
    cmds.setKeyframe(f"{controller}.flash", time=(120,), value=maxValue)

    for loc, condition in stars:
        cmds.setAttr(f"{condition}.colorIfTrue", 1.0, 1.0, 1.0)
        cmds.setAttr(f"{condition}.colorIfFalse", 0.0, 0.0, 0.0)

        cmds.setAttr(f"{loc}.overrideEnabled", True)
        cmds.setAttr(f"{loc}.overrideColor", getRandomColor())

        pos = getRandomPosition(maxValue)
        cmds.move(pos[0], pos[1], pos[2], loc)
        cmds.setAttr(f"{loc}.s", *getRandomScale())
        cmds.setAttr(f"{loc}.displayHandle", lock=True)
        cmds.setAttr(f"{loc}.overrideDisplayType", lock=True)
        cmds.setAttr(f"{loc}.overrideDisplayType", lock=False)

        cmds.setAttr(f"{loc}.flashIndex", getRandomIndex(maxValue))

        cmds.connectAttr(f"{controller}.r", f"{loc}.r")
        cmds.connectAttr(f"{controller}.overrideShading", f"{loc}.overrideShading")
        cmds.disconnectAttr(f"{controller}.overrideShading", f"{loc}.overrideShading")

        cmds.connectAttr(f"{controller}.flash", f"{condition}.firstTerm")
        cmds.connectAttr(f"{loc}.flashIndex", f"{condition}.secondTerm")
        cmds.connectAttr(f"{condition}.outColorR", f"{loc}.visibility")


def renameInCmds(nodesToRename):
    for node in nodesToRename:
        cmds.rename(node, f"{node}New")
        cmds.rename(f"{node}New", node)


def queryInCmds(controller, stars):
    cmds.listConnections(f"{controller}.flash")
    for loc, _ in stars:
        cmds.objExists(loc)
        cmds.getAttr(f"{loc}.t")
        cmds.getAttr(f"{loc}.wm[0]")
        cmds.getAttr(f"{loc}.overrideDisplayType", lock=True)


def deleteInCmds(nodesToDelete):
    for toDel in nodesToDelete:
        cmds.delete(toDel)


def categorizedPerformanceTestInCmds():
    for num in NUM_NODES_LIST:
        cmds.file(new=True, force=True)
        with TotalPerfMeasurement(f"Deal with {num} nodes in maya.cmds") as measure:
            with measure.add(f"Create {num}+ nodes in maya.cmds"):
                controller, stars, nodes = createInCmds(num)

            with measure.add(f"Edit {num}+ nodes in maya.cmds"):
                editInCmds(controller, stars)

            with measure.add(f"Rename {num} nodes in maya.cmds"):
                renameInCmds(nodes)

            with measure.add(f"Query {num}+ nodes in maya.cmds"):
                queryInCmds(controller, stars)

            with measure.add(f"Remove {num} nodes in maya.cmds"):
                deleteInCmds(nodes)


def totalPerformanceTestInCmds():
    for num in REFINED_NUM_NODES_LIST:
        cmds.file(new=True, force=True)
        with PerfMeasurement(f"Deal with {num} nodes in maya.cmds"):
            controller, stars, nodes = createInCmds(num)
            editInCmds(controller, stars)
            renameInCmds(nodes)
            queryInCmds(controller, stars)
            deleteInCmds(nodes)


if __name__ == "__main__":
    categorizedPerformanceTestInCmds()
    # totalPerformanceTestInCmds()
