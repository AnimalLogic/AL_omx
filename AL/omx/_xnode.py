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

from AL.omx.utils._stubs import om2

from AL.omx import _xplug
from AL.omx.utils import _nodes
from AL.omx.utils import _plugs

logger = logging.getLogger(__name__)


class XNode:
    """Easy wrapper around om2 objects mainly to access plugs. 
    """

    _NODE_CLASS_CACHE = {}
    _ATTRIBUTE_CACHE = {}

    def __init__(self, obj):
        """ Creates a new XNode

        Args:
            obj (:class:`om2.MObject` | :class:`XNode` | :class:`om2.MFnBase` | string): A object to wrap

        Returns:
            :class:`XNode`: An instance of a XNode object
        """
        if isinstance(obj, om2.MObject):
            mob = obj
        elif isinstance(obj, om2.MObjectHandle):
            mob = obj.object()
        elif isinstance(obj, XNode):
            mob = obj.object()
        elif isinstance(obj, om2.MFnBase):
            mob = obj.object()
        elif isinstance(obj, om2.MDagPath):
            mob = obj.node()
        elif isinstance(obj, str):
            mob = _nodes.findNode(obj)
            if mob is None:
                raise RuntimeError(f"Object {obj} is not valid!")

        else:
            raise RuntimeError(f"Cannot use {obj} with XNode!")

        if mob != om2.MObject.kNullObj and not mob.hasFn(om2.MFn.kDependencyNode):
            raise RuntimeError(
                "Cannot use XNode on an object that is not a DependencyNode!"
            )

        self._mobHandle = om2.MObjectHandle(mob)
        nodeFn = om2.MFnDependencyNode(mob)
        self._lastKnownName = nodeFn.absoluteName()
        self._mayaType = mayaType = nodeFn.typeName
        nodeCls = XNode._NODE_CLASS_CACHE.get(mayaType, None)
        if nodeCls is None:
            nodeCls = om2.MNodeClass(mayaType)
            XNode._NODE_CLASS_CACHE[mayaType] = nodeCls
            XNode._ATTRIBUTE_CACHE[mayaType] = {}

    def __getattribute__(self, name):
        # Normal attributes (such as methods) are handled here
        if hasattr(XNode, name):
            return object.__getattribute__(self, name)

        mob = object.__getattribute__(self, "object")()

        # We expose the MObject.apiTypeStr property here
        if name == "apiTypeStr":
            return mob.apiTypeStr

        if mob == om2.MObject.kNullObj:
            lastName = object.__getattribute__(self, "_lastKnownName")
            raise RuntimeError(f"XNode({lastName}) associated MObject is null!")
        mayaType = object.__getattribute__(self, "_mayaType")

        nodeClass = XNode._NODE_CLASS_CACHE[mayaType]
        attrs = XNode._ATTRIBUTE_CACHE[mayaType]
        attr = attrs.get(name, None)
        # if it is a dynamic attribute:
        if attr is None:
            if not nodeClass.hasAttribute(name):
                plug = _plugs.findPlug(name, mob)
                if plug:
                    return _xplug.XPlug(plug)

                raise AttributeError(f"Node {mayaType} has no attribute called {name}")

            attr = nodeClass.attribute(name)
            attrs[name] = attr
        return _xplug.XPlug(mob, attr)

    def object(self):
        """Returns the associated MObject

        Raises:
            RuntimeError: When the MObject is invalid.

        Returns:
            :class:`om2.MObject`: the associated MObject
        """
        mobHandle = object.__getattribute__(self, "_mobHandle")

        # no need to test isAlive() as being valid is guaranteed to be alive.
        # and usually we only care if it is valid.
        if not mobHandle.isValid():
            lastName = object.__getattribute__(self, "_lastKnownName")
            raise RuntimeError(f"XNode({lastName}) is not valid!")

        mob = mobHandle.object()
        return mob

    def isAlive(self):
        """Returns the live state of the current MObject associated with this XNode.
        An object can still be 'alive' but not 'valid'
        (eg. a deleted object that resides in the undo queue).

        Returns:
            bool: the live state
        """
        return object.__getattribute__(self, "_mobHandle").isAlive()

    def isValid(self):
        """Returns the validity of the current MObject associated with this XNode.

        Returns:
            bool: the valid state
        """
        return object.__getattribute__(self, "_mobHandle").isValid()

    def isNull(self):
        """Tests whether there is an internal Maya object.

        Returns:
            bool: Returns True if the MObject is not referring to any Maya internal internal object (i.e. it is equivalent to kNullObj).
        """
        return self.object().isNull()

    def apiType(self):
        """Returns the function set type for the object.

        Returns:
            `om2.MFn`: Returns a constant indicating the type of the internal Maya object. If the MObject is null MFn.kInvalid will be returned.
        """
        return self.object().apiType()

    def hasFn(self, fn):
        """Tests whether object is compatible with the specified function set.

        Args:
            fn (`om2.MFn`): MFn type constant

        Returns:
            bool: Returns True if the internal Maya object supports the specified function set specified by fn.
        """
        return self.object().hasFn(fn)

    def createDagNode(self, typeName, nodeName=""):
        """Creates a child DAG node on the current node if possible.

        Adds an operation to the modifier to create a DAG node of the specified type. If a parent DAG node is provided the new node will be parented under it.
        If no parent is provided and the new DAG node is a transform type then it will be parented under the world. In both of these cases the method returns
        the new DAG node.

        If no parent is provided and the new DAG node is not a transform type then a transform node will be created and the child parented under that.
        The new transform will be parented under the world and it is the transform node which will be returned by the method, not the child.

        None of the newly created nodes will be added to the DAG until the modifier's doIt() method is called.

        Raises:
            :class:`TypeError` if the node type does not exist or if the parent is not a transform type.

        Args:
            typeName (string): the type of the object to create, e.g. "transform"
            
            nodeName (str, optional): the node name, if non empty will be used in a modifier.renameObject call. Defaults to "".

        Returns:
            :class:`XNode`: An XNode instance around the created MObject.
        """
        mob = self.object()
        if not mob.hasFn(om2.MFn.kDagNode):
            raise TypeError(
                f"Cannot create a DAG node {nodeName}[{typeName}] under this non-DAG node {self}"
            )

        from AL.omx import _xmodifier

        return _xmodifier.createDagNode(typeName, parent=mob, nodeName=nodeName)

    def bestFn(self):
        """Returns the best MFn function set for the associated MObject

        Raises:
            RuntimeError: if no MFn is found for the wrapped MObject

        Returns:
            om2.MFn*: the best MFn object for this MObject (usually a :class:`om2.MFnTransform` or a :class:`om2.MFnDependencyNode`)
        """
        mob = self.object()
        fnList = reversed(om2.MGlobal.getFunctionSetList(mob))
        for k in fnList:
            om2Type = getattr(om2, "MFn" + k[1:], None)
            if om2Type:
                return om2Type(mob)
        raise RuntimeError(f"No best Fn found for {self}")

    def basicFn(self):
        """Returns the basic MFnDAGNode or MFnDependencyNode for the associated MObject

        Notes:
            Usually you would use xnode.bestFn() to get the most useful function set. But for an empty nurbsCurve
            or an empty mesh node, only xnode.basicFn() will work as expected.

        Returns:
            om2.MFnDagNode | om2.MFnDependencyNode: For a DAG node or a DG node respectively.
        """
        mob = self.object()
        if mob.hasFn(om2.MFn.kDagNode):
            return om2.MFnDagNode(mob)

        return om2.MFnDependencyNode(mob)

    def __str__(self):
        """Returns an easy-readable str representation of this XNode. 

        Construct a minimum unique path to support duplicate MObjects in scene. 
        For invalid MObject we return the last known name with a suffix (dead) 
        or (invalid) respectively.

        Returns:
            str: the string representation.
        """
        mobHandle = object.__getattribute__(self, "_mobHandle")
        if not mobHandle.isAlive():
            lastName = object.__getattribute__(self, "_lastKnownName")
            return f"{lastName}(dead)"

        if not mobHandle.isValid():
            lastName = object.__getattribute__(self, "_lastKnownName")
            return f"{lastName}(invalid)"

        mob = mobHandle.object()
        if mob.hasFn(om2.MFn.kDagNode):
            return om2.MFnDagNode(mob).partialPathName()

        if mob.hasFn(om2.MFn.kDependencyNode):
            return om2.MFnDependencyNode(mob).name()

        return "None"

    def __repr__(self):
        """Get the more unambiguous str representation. This is mainly for debugging purposes.

        Returns:
            str
        """
        return f'XNode("{self}")'

    def __eq__(self, other):
        """Add support for XNode comparison.
        """
        if isinstance(other, XNode):
            return self.object().__eq__(other.object())

        if isinstance(other, om2.MObject):
            return self.object().__eq__(other)

        return False

    def __ne__(self, other):
        """Add support for XNode comparison.
        """
        if isinstance(other, XNode):
            return self.object().__ne__(other.object())

        if isinstance(other, om2.MObject):
            return self.object().__ne__(other)

        return True

    def __hash__(self):
        """Add support for using XNode for containers that require uniqueness, e.g. dict key.
        """
        return object.__getattribute__(self, "_mobHandle").hashCode()
