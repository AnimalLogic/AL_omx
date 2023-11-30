from AL import omx
from maya.api import OpenMaya as om2

# you might need to create new Maya scene to avoid potential node name conflicts.

# creating nodes:
transform, locator = omx.createDagNode(
    "locator", nodeName="myLocShape", returnAllCreated=True
)
omx.createDGNode("time", nodeName="myTime")

# constructing XNode from existing nodes:
persp = omx.XNode("persp")
perspShape = omx.XNode("perspShape")
print("a XNode is a om2.MObject:", isinstance(persp, om2.MObject))
print("camera api type: ", perspShape.apiType())
print("has camera functor: ", perspShape.hasFn(om2.MFn.kCamera))
print("camera is null: ", perspShape.isNull())
print("camera is valid: ", perspShape.isValid())
print("camera MObject: ", perspShape.object())

# getting om2.MFn functors.
print("basic functor for DAG:", persp.basicFn())
print("basic functor for DG:", omx.XNode("time1").basicFn())
print("basic functor for transform:", persp.bestFn())
print("basic functor for camera:", perspShape.bestFn())

# XPlug set and get:
print("a XPlug is an MPlug:", isinstance(persp.visibility, om2.MPlug))
persp.visibility.setLocked(True)
print(f"XNode from xplug {persp.v} :", persp.v.xnode())
print(f"om2.MObject from xplug {persp.v} :", persp.v.node())
transform.t.set([2.0, 2.0, 2.0])
print("locator translation:", transform.t.get())
print(f"locator worldMatrix: {transform.wm[0].get()}")
locator.overrideEnabled.set(True)
locator.overrideColor.set(14)

# connection
persp.r.connectTo(transform.r)
print(f"Source of {transform.r}: {transform.r.source()}")
transform.sx.connectFrom(omx.XNode("time1").outTime)
transform.sy.connectFrom(omx.XNode("time1").outTime)

# disconnect
transform.r.disconnectFromSource()
print(f"After disconnection, source of {transform.r}: {transform.r.source()}")

# undo & redo
omx.currentModifier().undoIt()
omx.currentModifier().doIt()
