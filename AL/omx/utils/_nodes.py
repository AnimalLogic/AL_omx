# Copyright (C) Animal Logic Pty Ltd. All rights reserved.

import logging
from maya import cmds
from maya.api import OpenMaya as om2

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
        _maximumAttempts (int): The maximum attempts before get a node name that does not exists.
        
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


def findNode(nodeName):
    """ Find the dependency node MObject by name

    Args:
        nodeName (str): full or short name of the node

    Returns:
        (MObject) if found (None) otherwise
    """
    # to avoid expensive check for existence, wrap with try except...
    # A cmds.objExists() test will return True for duplicate-named nodes, but it will
    # still raise run-time error when you add them to om2.MSelectionList.
    sl = om2.MSelectionList()
    try:
        sl.add(nodeName)
    except RuntimeError as e:
        logger.debug("Node %r does not exist.\n%s", nodeName, str(e))
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
