from AL.maya2 import omx

driver = omx.createDagNode("locator", nodeName="driver")
driven = omx.createDagNode("locator", nodeName="driven")

# If you are going to retrieve plug values you need to run doIt before hand.
# N.B this is optional when executing code from the maya script editor as doIt is run automatically every time it is needed!
# But if you use this code inside an ALCommand, doIt becomes necessary.
omx.doIt()

# You can get and set plug values easily:
driver.translateX.set(5)
print(driver.translateX.get())
print(driver.worldMatrix[0].get())

reparent = omx.createDGNode("AL_rig_reparentSingle")
reparent.worldMatrix.connectFrom(driver.worldMatrix[0])
driven.translate.connectFrom(reparent.translate)
driven.rotate.connectFrom(reparent.rotate)
driven.scale.connectFrom(reparent.scale)
driven.rotateOrder.connectFrom(reparent.rotateOrder_out)
