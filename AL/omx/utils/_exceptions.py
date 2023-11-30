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


class NullXPlugError(RuntimeError):
    """Used when an unexpected null XPlug is encountered.
    """

    pass


class PlugArrayOutOfBounds(Exception):
    """Used for when an array's plug index does not exist.
    """

    def __init__(self, message):
        """
        Args:
            message (str, optional): The message override, a default message will be used if not provided.
        """
        super().__init__(message)
        self.message = message


class PlugMayaInvalidException(Exception):
    """This is very specific Exception for invalid maya plug.

    Notes:
        Sometimes Maya generates plugs in an invalid state that are perfectly legal, but won't 
        behave as expected. These plugs can hard crash Maya when manipulated or queried.
        The most common example are arrays of compounds without any elements.

        This is to be used for those cases, and for those cases only.
    """

    __DEFAULT_MESSAGE = (
        "invalid plug, this usually happens with uninitialised array plugs"
    )
    __PLUGNOTFOUND_MESSAGE = "plug name unavailable"

    def __init__(self, plug, message=""):
        """
        Args:
            plug (om2.MPlug): The plug to raise exception for.
            message (str, optional): The message override, a default message will be used if not provided.
        """
        self.plugName = None
        localMessage = message or self.__DEFAULT_MESSAGE
        try:
            self.plugName = plug.name()
        except Exception:  # yeah, it's an except all, but we don't want errorception here.
            self.plugName = self.__PLUGNOTFOUND_MESSAGE

        self.message = f"Error on plug: {self.plugName} - {localMessage}"
        super().__init__(self.message)


class PlugUnhandledTypeException(Exception):
    """This is used when a plug of a certain type is found that is not handled in code.
    """

    __DEFAULT_MESSAGE = "a type, or mixed type, or subtype is of an unsupported type"
    __PLUGNOTFOUND_MESSAGE = "plug name unavailable"

    def __init__(self, plug, typeID, subTypeID, message=""):
        """
        Args:
            plug (om2.MPlug): The plug to raise exception for.
            typeID (int): The attribute type, `om2.MFn.k*Attribute`.
            subTypeID (int): The numeric type, `om2.MFnNumericData.k*`.
            message (str, optional): The message override, a default message will be used if not provided.
        """
        self.plugName = None
        localMessage = message or self.__DEFAULT_MESSAGE
        try:
            self.plugName = plug.name()
        except Exception:
            self.plugName = self.__PLUGNOTFOUND_MESSAGE

        self.message = f"Error on plug: {self.plugName} of type and subtype: {typeID},{subTypeID} - {localMessage}"
        super().__init__(self.message)


class PlugAttributePredicateError(Exception):
    """An exception raised when calling predicate function ends in error.
    """

    __PLUGNOTFOUND_MESSAGE = "plug name unavailable"

    def __init__(self, plug):
        """
        Args:
            plug (om2.MPlug): The plug to raise exception for.
        """
        self.plugName = None
        try:
            self.plugName = plug.name()
        except Exception:
            self.plugName = self.__PLUGNOTFOUND_MESSAGE

        self.message = f"Error on plug: {self.plugName} attribute functors failed"
        super().__init__(self.message)


class PlugLockedForEditError(Exception):
    """An exception raised when calling predicate function results in an error.
    """

    __PLUGNOTFOUND_MESSAGE = "[INVALID PLUG]."

    def __init__(self, plug):
        """
        Args:
            plug (om2.MPlug): The plug to raise exception for.
        """
        self.plugName = None
        try:
            self.plugName = plug.name()
        except Exception:
            self.plugName = self.__PLUGNOTFOUND_MESSAGE

        self.message = f"The plug: {self.plugName} is locked from edit."
        super().__init__(self.message)
