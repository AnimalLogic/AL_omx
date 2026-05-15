# Copyright © 2026 Netflix, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.#
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import logging

from AL.omx.utils._stubs import cmds
from AL.omx.utils._stubs import om2

logger = logging.getLogger(__name__)


def partitionNameAndTrailingDigits(inputName):
    """Separate a node name into (name, trailingDigits)

    Args:
        inputName (str): the input name to partition.

    Returns:
        (str, int) if inputName has non-digit name and trailing digits.

    Examples:
        partitionNameAndTrailingDigits('') -> (None, None)
        partitionNameAndTrailingDigits('my_motion:name') -> ('my_motion:name', None)
        partitionNameAndTrailingDigits('2343') -> (None, 2343)
        partitionNameAndTrailingDigits('my_motion:name12') -> ('my_motion:name', 12)
    """
    if not inputName:
        return (None, None)

    nameLen = len(inputName)
    digits = []
    for i in range(nameLen - 1, -1, -1):
        if inputName[i].isdigit():
            digits.append(inputName[i])
        else:
            break

    digitLen = len(digits)
    if not digitLen:
        return (inputName, None)

    digit = int("".join(reversed(digits)))
    if not digitLen < nameLen:
        return (None, digit)

    baseName = inputName[: nameLen - digitLen]
    return (baseName, digit)


def closestAvailableNodeName(nodeName, _maximumAttempts=10000):
    """Return the closest node name that does not exist in Maya.

    Args:
        nodeName (str): the input name.
        _maximumAttempts (int, optional): The maximum attempts before get a node name that does not exists.

    Returns:
        str | None: Return the closest name that is available if nodeName is a valid Maya
            node name, otherwise None.

    Examples:
        Say in Maya scene we have nodes my_motion:ctrl, my_motion:ctrl1
        closestAvailableNodeName('my_motion:ctrl') -> 'my_motion:ctrl2'
    """
    if not nodeName:
        return None

    if not cmds.objExists(nodeName):
        if nodeName[0].isalpha() or nodeName[0] == "_":
            return nodeName
        return None

    baseName, digit = partitionNameAndTrailingDigits(nodeName)
    if not baseName:
        return None

    if digit is None:
        digit = 1
    else:
        digit = digit + 1

    i = 0
    _maximumAttempts = max(_maximumAttempts, 0)
    while i < _maximumAttempts:
        newName = f"{baseName}{digit}"
        if not cmds.objExists(newName):
            return newName

        digit = digit + 1
        i = i + 1

    return closestAvailableNodeName(f"{nodeName}_1")


def createSelectionList(*objects, silent=True):
    """An convenient util to create a MSelectionList from arbitrary number of inputs.

    Args:
        objects (any): A list of any supported input for MSelectionList creation.
            e.g. MObject, str, MDagPath, MPlug, MUuid, etc.

    Returns:
        om2.MSelectionList if success, otherwise None.
    """
    sl = om2.MSelectionList()
    # to avoid expensive check for existence, wrap with try except...
    # A cmds.objExists(name) test will return True for duplicate-named nodes, but it will
    # still raise run-time error when you add them to om2.MSelectionList.
    try:
        for obj in objects:
            sl.add(obj)

        return sl
    except RuntimeError as e:
        logMethod = logger.debug if silent else logger.error
        logMethod(
            "The input %s is not valid to be added to MSelectionList.\n%s", obj, str(e)
        )
        return None


def findNode(nodeName):
    """Find the dependency node MObject by name

    Args:
        nodeName (str): full or short name of the node

    Returns:
        om2.MObject if found or None otherwise
    """
    sl = createSelectionList(nodeName)
    if sl is None:
        return None

    if sl.length() == 1:
        node = sl.getDependNode(0)
        if node.isNull():
            logger.error('Node: "%s" is Null.', nodeName)
        else:
            return node

    elif sl.length() > 1:
        logger.error('Node: "%s" is not unique.', nodeName)

    return None


def findDagPath(nodeName):
    """Find the MDagPath by name

    Args:
        nodeName (str): full or short name of the dag node

    Returns:
        om2.MDagPath if found or None otherwise
    """
    sl = createSelectionList(nodeName)
    if sl is None:
        return None

    try:
        if sl.length() == 1:
            node = sl.getDependNode(0)
            if not node.hasFn(om2.MFn.kDagNode):
                logger.warning(
                    "The node %s is not a Dag node to get a Dag path.", nodeName
                )
                return None

            return sl.getDagPath(0)

        elif sl.length() > 1:
            logger.error('Node: "%s" is not unique.', nodeName)

    except RuntimeError as e:
        logger.debug(
            "The input %s is not valid to get a MDagPath.\n%s", nodeName, str(e)
        )
        return None

    return None
