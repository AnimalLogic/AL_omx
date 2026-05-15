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

from AL.omx.utils._stubs import om2
from AL.omx import _xnode
from AL.omx import _xplug


class XFn:
    """Easy wrapper around om2 MFn* mainly to query and edit MObject. This is served as a convenient
    replacement of om2.MFn classes.
    """

    def __init__(self, obj):
        """Creates a new XFn

        Args:
            obj (:class:`om2.MObject` | :class:`XNode` | :class:`om2.MFnBase` | string): A object to wrap

        Returns:
            :class:`XFn`: An instance of a XFn object
        """
        node = _xnode.XNode(obj)
        self._xnode = node
        self._mfn = node.bestFn()

    def xnode(self):
        """Get the MObject the XFn was attached to and return as a XNode.

        Notes:
            Invalid XNode will be returned instead of None on failure.

        Returns:
            omx.XNode
        """
        return object.__getattribute__(self, "_xnode")

    def object(self):
        """Returns the associated MObject

        Raises:
            RuntimeError: When the MObject is invalid.

        Returns:
            :class:`om2.MObject`: the associated MObject
        """
        xnode = object.__getattribute__(self, "_xnode")
        return xnode.object()

    def hasDagNode(self):
        """Return if this XFn is attached to a Dag node.

        Returns:
            boolean: True if it is a Dag node.
        """
        xnode = object.__getattribute__(self, "_xnode")
        if not xnode.isValid():
            return False

        return xnode.hasFn(om2.MFn.kDagNode)

    def hasParentAtIndex(self, index=0):
        """Check if there is a DAG parent at the given index.

        Returns:
            boolean: True if there is a parent at the given index.
        """
        if not self.hasDagNode():
            return False

        mfn = object.__getattribute__(self, "_mfn")
        parentCount = mfn.parentCount()
        if index < 0 or index >= parentCount:
            return False

        if parentCount == 1 and mfn.parent(index).hasFn(om2.MFn.kWorld):
            return False

        return True

    def hasShapeAtIndex(self, index=0):
        """Check if there is a shape at the given index.

        Returns:
            boolean: True if there is a shape at the given index.
        """
        if not self.hasDagNode():
            return False

        for i, _ in enumerate(self.iterShapes()):
            if i == index:
                return True

        return False

    def hasChildAtIndex(self, index=0):
        """Check if there is a DAG child at the given index.

        Returns:
            boolean: True if there is a DAG child at the given index.
        """
        if not self.hasDagNode():
            return False

        mfn = object.__getattribute__(self, "_mfn")
        return 0 <= index < mfn.childCount()

    def getMFnClass(self):
        """Return the actual om2.MFn* class that is used by this XFn

        Returns:
            type: The om2.MFn* class object.
        """
        mfn = object.__getattribute__(self, "_mfn")
        return type(mfn)

    def _checkIsDagNode(self, methodName, arg):
        xnode = object.__getattribute__(self, "_xnode")
        if not xnode.isValid():
            raise RuntimeError(f"The {xnode} is invalid for XFn.{methodName}({arg}).")

        if not xnode.hasFn(om2.MFn.kDagNode):
            raise RuntimeError(
                f"The {xnode} is not a Dag node for XFn.{methodName}({arg})."
            )

    def getParent(self, index=0):
        """Get the DAG parent by index.

        Raises:
            RuntimeErrors: if it is not a DAG node, or there is no such parent at the index.

        Args:
            index (int): The index of parent. Default to 0 as most of time we ask for the
                         the first parent unless it is instanced.

        Returns:
            omx.XNode: the parent XNode.
        """
        self._checkIsDagNode("getParent", index)
        xnode = object.__getattribute__(self, "_xnode")
        if not xnode.hasFn(om2.MFn.kDagNode):
            raise RuntimeError(
                f"The {xnode} is not a Dag node for XFn.getParent({index})."
            )

        mfn = object.__getattribute__(self, "_mfn")
        if index < 0 or index >= mfn.parentCount():
            raise RuntimeError(f"The {xnode} has no parent at the index {index}.")

        parent = mfn.parent(index)
        if parent.hasFn(om2.MFn.kWorld):
            raise RuntimeError(f"The {xnode} has no parent.")

        return _xnode.XNode(parent)

    def getChild(self, index):
        """Get the child DAG node by index.

        Raises:
            RuntimeErrors: if it is not a DAG node, or there is no such child at the index.

        Args:
            index (int): The index of child.

        Returns:
            omx.XNode: the child XNode.
        """
        self._checkIsDagNode("getChild", index)

        mfn = object.__getattribute__(self, "_mfn")
        xnode = object.__getattribute__(self, "_xnode")
        if index < 0 or index >= mfn.childCount():
            raise RuntimeError(f"The {xnode} has no child at the index {index}.")

        return _xnode.XNode(mfn.child(index))

    def getShape(self, index=0):
        """Get the DAG shape by index. Note that this will raise exception if it is not
        a Dag node, or there is no such shape at the index.

        Args:
            index (int): The index of shape.

        Returns:
            omx.XNode: the shape XNode.
        """
        self._checkIsDagNode("getShape", index)

        cIndex = 0
        predicate = lambda n: n.hasFn(om2.MFn.kShape)
        for c in self.iterChildren(predicate=predicate):
            if cIndex == index:
                return c

            cIndex += 1

        xnode = object.__getattribute__(self, "_xnode")
        raise RuntimeError(f"The {xnode} has no shape at the index {index}.")

    def iterChildren(self, predicate=lambda xnode: True):
        """Iter all the child XNodes.

        Raises:
            RuntimeErrors: if it is not a DAG node.

        Args:
            predicate (callable): A callable object that takes an xnode as an argument and
                                  returns True to include a child or False to ignore it.

        Yields:
            omx.XNode: The child XNode.
        """
        self._checkIsDagNode("iterChildren", predicate)
        mfn = object.__getattribute__(self, "_mfn")
        for i in range(mfn.childCount()):
            child = _xnode.XNode(mfn.child(i))
            if predicate(child):
                yield child

    def iterShapes(self, predicate=lambda xnode: True):
        """Iter all the shape XNodes.

        Raises:
            RuntimeErrors: if it is not a DAG node.

        Args:
            predicate (callable): A callable object that takes an xnode as an argument and
                                  returns True to include a shape or False to ignore it.

        Yields:
            omx.XNode: The shape XNode.
        """
        shapePredicate = lambda xnode: xnode.hasFn(om2.MFn.kShape)
        for shape in self.iterChildren(predicate=shapePredicate):
            if predicate(shape):
                yield shape

    def iterAncestors(self, predicate=lambda xnode: True):
        """Iter all the ancestor XNodes.

        Raises:
            RuntimeErrors: if it is not a DAG node.

        Args:
            predicate (callable): A callable object that takes an xnode as an argument and
                                  returns True to include an ancestor or False to ignore it.

        Notes:
            If an ancestor node is filtered out, we will still keep iterating its potential
            ancestors. The iteration will be depth-first.
            The world virtual root node will not be included in the iteration.

        To-Do:
            Cover the imagePlane special case.

        Yields:
            omx.XNode: The ancestor XNode.
        """
        self._checkIsDagNode("iterAncestors", predicate)
        mfn = object.__getattribute__(self, "_mfn")
        for i in range(mfn.parentCount()):
            mobj = mfn.parent(i)
            # We skip the scene's root world transform.
            if mobj.hasFn(om2.MFn.kWorld):
                continue

            ancestor = _xnode.XNode(mobj)
            if predicate(ancestor):
                yield ancestor

            xfn = ancestor.xFn()
            yield from xfn.iterAncestors(predicate)

    def iterDescendants(self, predicate=lambda xnode: True):
        """Iter all the descendant XNodes.

        Raises:
            RuntimeErrors: if it is not a DAG node.

        Args:
            predicate (callable): A callable object that takes an xnode as an argument and
                                  returns True to include a descendant or False to ignore it.

        Notes:
            If an ancestor node is filtered out, we will still keep iterating its potential
            descendants. The iteration will be depth-first.

        Yields:
            omx.XNode: The descendant XNode.
        """
        self._checkIsDagNode("iterDescendants", predicate)
        mfn = object.__getattribute__(self, "_mfn")
        for i in range(mfn.childCount()):
            child = _xnode.XNode(mfn.child(i))
            if predicate(child):
                yield child

            xfn = child.xFn()
            yield from xfn.iterDescendants(predicate)

    def iterXPlugs(
        self,
        attrType=_xplug.XAttrType.ALL,
        states=_xplug.XPlugState.ALL,
        predicate=lambda xplug: True,
    ):
        """Iterate over all XPlugs on the XNode that this XFn wraps, that matches the criteria.
        Check out :meth:`omx.XNode.iterXPlugs` for more details.
        """
        xnode = object.__getattribute__(self, "_xnode")
        yield from xnode.iterXPlugs(
            attrType=attrType,
            states=states,
            predicate=predicate,
        )

    def getPath(self):
        """Return the minimum path of the DAG node, or name for the DG node."""
        return str(object.__getattribute__(self, "_xnode"))

    def getFullPath(self):
        """Return the full path of the DAG node, or name for the DG node."""
        xnode = object.__getattribute__(self, "_xnode")
        if not xnode.object().hasFn(om2.MFn.kDagNode):
            return str(xnode)

        mfn = object.__getattribute__(self, "_mfn")
        return mfn.fullPathName()

    def getName(self, namespaced=True):
        """Return the name of the node.

        Args:
            namespaced (bool): Whether we return namspaced or unnamespaced.
        """
        mfn = object.__getattribute__(self, "_mfn")
        n = mfn.name()
        if namespaced or not mfn.namespace:
            return n

        return n[len(mfn.namespace) + 1 :]

    def getNamespace(self):
        """Return the namespace of the node."""
        mfn = object.__getattribute__(self, "_mfn")
        return mfn.namespace

    def __getattribute__(self, name):
        # Normal attributes (such as methods) are handled here
        if hasattr(XFn, name):
            return object.__getattribute__(self, name)

        # We delegate all the other stuff to self._mfn
        mfn = object.__getattribute__(self, "_mfn")
        if not hasattr(mfn, name):
            raise RuntimeError(f"The {self} does not have the method {name}")

        return getattr(mfn, name)

    def __str__(self):
        """Returns an easy-readable str representation of this XNode.

        Construct a minimum unique path to support duplicate MObjects in scene.
        For invalid MObject we return the last known name with a suffix (dead)
        or (invalid) respectively.

        Returns:
            str: the string representation.
        """
        _xnode = object.__getattribute__(self, "_xnode")
        return f"XFn({_xnode})"

    def __repr__(self):
        """Get the more unambiguous str representation. This is mainly for debugging purposes.

        Returns:
            str
        """
        _xnode = object.__getattribute__(self, "_xnode")
        return f"XFn[{self.getMFnClass().__name__}]({_xnode})"

    def __eq__(self, other):
        """Add support for XNode comparison."""
        if isinstance(other, (XFn, _xnode.XNode, om2.MFnBase)):
            return self.object().__eq__(other.object())

        if isinstance(other, om2.MObject):
            return self.object().__eq__(other)

        return False

    def __ne__(self, other):
        """Add support for XNode comparison."""
        if isinstance(other, (XFn, _xnode.XNode, om2.MFnBase)):
            return self.object().__ne__(other.object())

        if isinstance(other, om2.MObject):
            return self.object().__ne__(other)

        return True

    def __hash__(self):
        """Add support for using XNode for containers that require uniqueness, e.g. dict key."""
        return object.__getattribute__(self, "_xnode").__hash__()
