# Copyright © 2023 Animal Logic. All Rights Reserved.
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
import warnings

from AL.omx.utils._stubs import om2

logger = logging.getLogger(__name__)


class MModifier(om2.MDagModifier):
    """MModifier is a `om2.MDagModifier` that implements the ability to create both DG and DAG node.
    """

    def __init__(self):
        om2.MDagModifier.__init__(self)

        # for self._dgMode:
        # If True, then MModifier behaves like an MDGModifier, except it has ability to use reparentNode.
        #     MModifier.createNode()       -> Create and return a DG node.
        #     MModifier.createDGNode()     -> Create and return a DG node.
        #     MModifier.createDagNode()     -> Create and return a DAG node.

        # If False, then it will behave like an MDGModifier, except it has ability to create DG nodes.
        #     MModifier.createNode()       -> Create and return a DAG node.
        #     MModifier.createDGNode()     -> Create and return a DG node.
        #     MModifier.createDagNode()     -> Create and return a DAG node.
        self._dgMode = False

    def createDGNode(self, typeName):
        """Create a DG node of the type.

        Args:
            typeName (str): The Maya node type name.

        Returns:
            om2.MObject: The DG node created.
        """
        logger.debug("Creating DG node of type %s using MModifier.", typeName)
        mob = om2.MDGModifier.createNode(self, typeName)
        return mob

    def createDagNode(self, typeName, parent=om2.MObject.kNullObj):
        """Create a DAG node of type typeName.

        Args:
            typeName (str): The Maya node type name.
            parent (om2.MObject, optional): The parent MObject. 

        Returns:
            om2.MObject: The DAG node created.
        """
        logger.debug(
            "Creating DAG node of type %s, parent %s  using MModifier.",
            typeName,
            parent,
        )
        mob = om2.MDagModifier.createNode(self, typeName, parent=parent)
        return mob

    def redoIt(self):
        """Actually perform the action in the modifier.
        """
        om2.MDagModifier.doIt(self)

    def createNode(self, *args, **kwargs):
        """Create DAG or DG node based on the internal mode state.

        Returns:
            om2.MObject: The DAG/DG node created.
        """
        warnings.warn(
            "Please use MModifier.createDGNode() or MModifier.createDagNode() over MModifier.createNode() to make it clear.",
            DeprecationWarning,
        )
        if self._dgMode:
            return self.createDGNode(*args, **kwargs)
        return self.createDagNode(*args, **kwargs)


class ToDGModifier:
    """A python context to use an :class:`MModifier` in DG mode, which means :func:`MModifier.createNode()` will create a DG node.
    """

    def __init__(self, mmodifer):
        self._mmodifer = mmodifer
        self._oldDGMode = mmodifer._dgMode

    def __enter__(self):
        self._mmodifer._dgMode = True
        return self._mmodifer

    def __exit__(self, *_, **__):
        self._mmodifer._dgMode = self._oldDGMode


class ToDagModifier:
    """A python context to use an :class:`MModifier` in DAG mode, which means :func:`MModifier.createNode()` will create a DAG node.
    """

    def __init__(self, mmodifer):
        self._mmodifer = mmodifer
        self._oldDGMode = mmodifer._dgMode

    def __enter__(self):
        self._mmodifer._dgMode = False
        return self._mmodifer

    def __exit__(self, *_, **__):
        self._mmodifer._dgMode = self._oldDGMode
