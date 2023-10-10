from AL.maya2 import om2, omx
from AL.libs.commandmaya import undoablecommands

import logging

logger = logging.getLogger(__name__)


class SimpleConstraint(undoablecommands.UndoablePureMayaOm2Command):
    def resolve(self):
        if not self.argumentValue("driver") and not self.argumentValue("driven"):
            sel = om2.MGlobal.getActiveSelectionList(orderedSelectionIfAvailable=True)
            if sel.length() == 2:
                self.setArgumentValue("driver", sel.getDagPath(0))
                self.setArgumentValue("driven", sel.getDagPath(1))
            else:
                logger.error("ParentConstraint needs 2 objects selected!")
                self.cancelExecution("ParentConstraint needs 2 objects selected!")

    def doIt(self, driver=None, driven=None):
        with omx.commandModifierContext(self) as modifier:
            # This converts possible string, MObject inputs to XNode:
            driver = omx.XNode(driver)
            driven = omx.XNode(driven)

            # You can get and set plug values easily, all the modification will be done
            # using the modifier we created in the context above`:
            driver.translateX.set(5)
            print(driver.translateX.get())
            print(driver.worldMatrix[0].get())

            reparent = modifier.createDGNode("AL_rig_reparentSingle")
            reparent.worldMatrix.connectFrom(driver.worldMatrix[0])
            driven.translate.connectFrom(reparent.translate)
            driven.rotate.connectFrom(reparent.rotate)
            driven.scale.connectFrom(reparent.scale)
            driven.rotateOrder.connectFrom(reparent.rotateOrder_out)
