# Copyright (C) Animal Logic Pty Ltd. All rights reserved.


class NullXPlugError(RuntimeError):
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
    """This is very specific.
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
        self.plugname = None
        localMessage = message or self.__DEFAULT_MESSAGE
        try:
            self.plugname = plug.name()
        except Exception:  # yeah, it's an except all, but we don't want errorception here.
            self.plugname = self.__PLUGNOTFOUND_MESSAGE

        self.message = f"error on plug: {self.plugname} - {localMessage}"
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
        self.plugname = None
        localMessage = message or self.__DEFAULT_MESSAGE
        try:
            self.plugname = plug.name()
        except Exception:
            self.plugname = self.__PLUGNOTFOUND_MESSAGE

        self.message = f"error on plug: {self.plugname} of type and subtype: {typeID},{subTypeID} - {localMessage}"
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
        self.plugname = None
        try:
            self.plugname = plug.name()
        except Exception:
            self.plugname = self.__PLUGNOTFOUND_MESSAGE

        self.message = f"error on plug: {self.plugname} attribute functors failed"
        super().__init__(self.message)
