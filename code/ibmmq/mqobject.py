"""This class is intended to be superclass for other MQ Object types.
It is a fairly empty class to start with. Can migrate values like the
object handle from subclasses, and functions such as open(), close() or inq() later.
"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

class MQObject:
    """
    Note that the name might not be available at construction time; the subclass
    will have to set it when known. This will allow us to potentially create classes (or
    use this one directly) for Namelist and Process objects that can be worked with in the MQI.
    """
    def __init__(self, name):
        # print(f"In MQObject constructor for class {type(self)} with value {name}")
        self._name = name
