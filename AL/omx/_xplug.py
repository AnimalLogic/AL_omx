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
from AL.omx.utils import _plugs
from AL.omx.utils import _exceptions

logger = logging.getLogger(__name__)


def _currentModifier():
    from AL.omx import _xmodifier

    return _xmodifier.currentModifier()


class XPlug(om2.MPlug):
    """ XPlug is not meant to be used directly, get one from :class:`XNode`!

    You can use omx.XPlug over an om2.MPlug to take advantage of the extra convenience features.

    Examples:

    .. code:: python

        xplug = xnode.attr
        xplug.get()                 # Get you the value of the plug
        xplug.set(value)            # Set the value of the plug
        xplug[0]                    # The element xplug by the logicial index 0 if xplug is an array plug.
        xplug['childAttr']          # The child xplug named 'childAttr' if xplug is a compound plug.
        xplug.xnode()               # Get you the parent xnode.

    Invalid Examples:

    .. code:: python

        xplug['childAttr.attr1']    # This won't work, use xplug['childAttr']['attr1'] instead.
        xplug['childAttr[0]']       # This won't work, use xplug['childAttr'][0] instead.
        ...

    """

    def __init__(self, *args, **kwargs):
        om2.MPlug.__init__(self, *args, **kwargs)

    def get(self, asDegrees=False):
        """Get the value of the plug.
        
        Args:
            asDegrees (bool, optional): For an angle unit attribute we return the value in degrees or in radians.
        """
        return _plugs.valueFromPlug(self, flattenComplexData=False, asDegrees=asDegrees)

    def set(self, value, asDegrees=False):
        """Set plug to the value.

        Notes:
            For enum attribute, you can set value by both short int or a valid enum name string.
            To retrieve the valid enum names, use :func:`XPlug.enumNames()`

            This method does many checks to make sure it works for different types of attributes.
            If you know the type of attribute, the preference would be to use the set*() methods 
            instead, they are more lightweight and have better performance.

        Args:
            value (any): The plug value to set.

            asDegrees (bool, optional): When it is an angle unit attribute, if this is True than 
            we take the value as degrees, otherwise as radians.This flag has no effect when it is 
            not an angle unit attribute.

        Returns:
            The previous value if it is simple plug and the set was successful. None or empty list
            otherwise.
        """
        return _plugs.setValueOnPlug(
            self, value, modifier=_currentModifier(), doIt=False, asDegrees=asDegrees
        )

    def setBool(self, value):
        """Adds an operation to the modifier to set a value onto a bool plug.

        Args:
            value (bool): the value.
        """
        _currentModifier().newPlugValueBool(self, value)

    def setChar(self, value):
        """Adds an operation to the modifier to set a value onto a char (single
        byte signed integer) plug.

        Args:
            value (int): the value.
        """
        _currentModifier().newPlugValueChar(self, value)

    def setDouble(self, value):
        """Adds an operation to the modifier to set a value onto a double-precision
        float plug.

        Args:
            value (float): the value.
        """
        _currentModifier().newPlugValueDouble(self, value)

    def setFloat(self, value):
        """Adds an operation to the modifier to set a value onto a single-precision
        float plug.

        Args:
            value (float): the value.
        """
        _currentModifier().newPlugValueFloat(self, value)

    def setInt(self, value):
        """Adds an operation to the modifier to set a value onto an int plug.

        Args:
            value (int): the value.
        """
        _currentModifier().newPlugValueInt(self, value)

    def setAngle(self, value):
        """Adds an operation to the modifier to set a value onto an angle plug.

        Args:
            value (``om2.MAngle``): the value.
        """
        _currentModifier().newPlugValueMAngle(self, value)

    def setDistance(self, value):
        """Adds an operation to the modifier to set a value onto a distance plug.

        Args:
            value (``om2.MDistance``): the value.
        """
        _currentModifier().newPlugValueMDistance(self, value)

    def setTime(self, value):
        """Adds an operation to the modifier to set a value onto a time plug.

        Args:
            value (``om2.MTime``): the value.
        """
        _currentModifier().newPlugValueMTime(self, value)

    def setShort(self, value):
        """Adds an operation to the modifier to set a value onto a short
        integer plug.

        Args:
            value (int): the value.
        """
        _currentModifier().newPlugValueShort(self, value)

    def setString(self, value):
        """Adds an operation to the modifier to set a value onto a string plug.

        Args:
            value (str): the value.
        """
        _currentModifier().newPlugValueString(self, value)

    def setCompoundDouble(self, value):
        """Adds an operation to the modifier to compound attribute's double 
        plugs children.

        Args:
            value ([double]): the list of double value whose amount should be 
                no larger to the amount of children.
        """
        for i, v in enumerate(value):
            child = self.child(i)
            _currentModifier().newPlugValueDouble(child, v)

    def enumNames(self):
        """Get the enum name tuple if it is an enum attribute, otherwise None.

        Returns:
            tuple of strs: The tuple of enum names.
        """
        return _plugs.plugEnumNames(self)

    def disconnectFromSource(self):
        """ Disconnect this plug from a source plug, if it's connected
        """
        if self.isDestination:
            with self.UnlockedModification(self):
                _currentModifier().disconnect(self.source(), self)

    def connectTo(self, destination, force=False):
        """ Connect this plug to a destination plug

        Args:
            destination (:class:`om2.MPlug` | :class:`XPlug`): destination plug

            force (bool, optional): override existing connection
        """
        destXPlug = XPlug(destination)
        if destXPlug.isDestination:
            if not force:
                logger.warning(
                    "%s connected to %s, use force=True to override this connection",
                    destXPlug,
                    destXPlug.source(),
                )
                return

            destXPlug.disconnectFromSource()

        with self.UnlockedModification(destXPlug):
            _currentModifier().connect(self, destXPlug)

    def connectFrom(self, source, force=False):
        """ Connect this plug to a source plug

        This is an alias to `connect`

        Args:
            source (:class:`om2.MPlug` | :class:`XPlug`): source plug
            
            force (bool, optional): override existing connection
        """
        if self.isDestination:
            if not force:
                logger.warning(
                    "%s connected to %s, use force=True to override this connection",
                    self,
                    self.source(),
                )
                return
            self.disconnectFromSource()

        with self.UnlockedModification(self):
            _currentModifier().connect(source, self)

    def setLocked(self, locked):
        """Set the plug's lock state.
        """
        self._setState("lock", self.isLocked, locked)

    def setKeyable(self, keyable):
        """Set the plug's keyable state.
        """
        self._setState("keyable", self.isKeyable, keyable)

    def setChannelBox(self, channelBox):
        """Set the plug's channelBox state.
        """
        self._setState("channelBox", self.isChannelBox, channelBox)

    def source(self):
        """Returns the source connection as an XPlug.
        
        Returns:
            omx.XPlug | NullPlug : A valid XPlug if there is a source connection, NullPlug (as an XPlug) if is there is no source connection.
        """
        return XPlug(om2.MPlug.source(self))

    def child(self, index):
        """Returns the child at index as an XPlug, if this plug is of type compound.

        Args:
            index (int): The child index.

        Returns:
            omx.XPlug | NullPlug : A valid XPlug or NullPlug (as an XPlug)
        """
        return XPlug(om2.MPlug.child(self, index))

    def destinations(self):
        """Get the destination plugs as a list of XPlugs for valid outgoing connections.
        
        Returns:
            List[omx.XPlug, ] | []
        """
        return [XPlug(p) for p in om2.MPlug.destinations(self)]

    def xnode(self):
        """Get the MObject the plug belongs to and return as a XNode.

        Notes:
            Invalid XNode will be returned instead of None on failure.

        Returns:
            omx.XNode
        """
        from AL.omx import _xnode

        return _xnode.XNode(om2.MPlug.node(self))

    def nextAvailable(self):
        """Get the next available element plug that does not exist yet for this array plug.

        Returns:
            omx.XPlug | None
        """
        nextElement = _plugs.nextAvailableElement(self)
        if nextElement is not None:
            return XPlug(nextElement)
        return None

    def _checkNullPlug(self):
        if self.isNull:
            raise _exceptions.NullXPlugError("The XPlug is null")

    def _setState(self, flag, currentState, targetState):
        self._checkNullPlug()

        if targetState == currentState:
            return

        state = 1 if targetState else 0
        cmd = f"setAttr -{flag} {state} {self}"
        logger.debug(cmd)
        _currentModifier().commandToExecute(cmd)

    class UnlockedModification:
        def __init__(self, xplug):
            self._xplug = xplug

        def __enter__(self):
            self._oldLocked = self._xplug.isLocked
            if self._oldLocked:
                # here we cannot use `plug.isLocked = False` because when doIt()
                # is called, it is already reverted to locked.
                self._xplug.setLocked(False)
            return self

        def __exit__(self, *_, **__):
            if self._oldLocked:
                self._xplug.setLocked(True)

    @staticmethod
    def _iterPossibleNamesOfPlug(plug):
        yield plug.partialName(includeNodeName=False, useAlias=False, useLongNames=True)
        yield plug.partialName(
            includeNodeName=False, useAlias=False, useLongNames=False
        )
        yield plug.partialName(includeNodeName=False, useAlias=True)

    @classmethod
    def _childPlugByName(cls, xplug, key):
        for i in range(xplug.numChildren()):
            childXplug = xplug.child(i)
            for name in cls._iterPossibleNamesOfPlug(childXplug):
                if key in (name, name.split(".")[-1]):
                    return childXplug

            # Since arrayOfCompoundPlug.isCompound == True, we need to filter it out first:
            if childXplug.isArray:
                continue

            if childXplug.isCompound:
                plug = cls._childPlugByName(childXplug, key)
                if plug:
                    return plug

        return None

    def __iter__(self):
        """Adds support for the `for p in xPlug` syntax so you can iter through an
        array's elements, or a compound's children, as XPlugs.

        Yields:
            :class:`XPlug`
        """
        if self.isArray:
            for logicalIndex in self.getExistingArrayAttributeIndices():
                yield XPlug(self.elementByLogicalIndex(logicalIndex))
        elif self.isCompound:
            for i in range(self.numChildren()):
                yield XPlug(self.child(i))

    def __getitem__(self, key):
        """Adds support for the `xplug[key]` syntax where you can get one of an array's elements, 
        or a compound's child, as XPlug.

        Args:
            key (int | str): The array element plug logical index or the child plug name.

        Returns:
            :class:`XPlug`
        
        Raises:
            AttributeError if compound plug doesn't have the child with name, TypeError
            for all the other cases.
        """
        if isinstance(key, int):
            if self.isArray:
                return XPlug(self.elementByLogicalIndex(key))

            raise TypeError(
                f"Failed to retrieve element [{key}]. {self.info} is not an array."
            )

        if isinstance(key, str):
            if self.isCompound:
                xplug = self._childPlugByName(self, key)
                if xplug:
                    return xplug

                raise AttributeError(
                    f"Compound plug {self.info} has no child called {key}."
                )

            raise TypeError(
                f"Plug {self.info} is not a compound to retrieve an XPlug from child [{key}]."
            )

        raise TypeError(f"The valid types for XPlug['{key}'] are: int | string.")

    def __contains__(self, key):
        """Add support for the `key in xPlug` syntax. 
        
        Checks if the index is an existing index of an array, or the str name is a valid child of a compound.

        Args:
            key (int | str): The array element plug logical index or the child plug name.

        Notes:
            We can extend to accept om2.MPlug or omx.XPlug as the input to check, but here we just 
            stay lined up with __getitem__().

        Returns:
            bool: True if index or name is valid, False otherwise.
        """
        if isinstance(key, int):
            if self.isArray:
                return key in self.getExistingArrayAttributeIndices()

        elif isinstance(key, str):
            if self.isCompound:
                return bool(self._childPlugByName(self, key))

        return False

    def __str__(self):
        """Returns an easy-readable str representation of this XPlug. Constructs a minimum unique path 
        to support duplicate MObjects in scene. "NullPlug" will be returned if this plug isNull.

        Returns:
            str
        """
        if self.isNull:
            return "NullPlug"

        attrName = self.partialName(
            includeNodeName=False,
            includeNonMandatoryIndices=False,
            includeInstancedIndices=True,
            useAlias=True,
            useFullAttributePath=False,
            useLongNames=True,
        )
        return f"{self.xnode()}.{attrName}"

    def __repr__(self):
        """Get the more unambiguous str representation. This is mainly for debugging purposes.

        Returns:
            str
        """
        return f'XPlug("{self}")'
