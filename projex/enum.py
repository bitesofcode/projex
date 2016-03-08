"""
Defines the enum class type that can be used to generate 
enumerated types 
"""

# use the text module from projex
from projex import text


class enum(dict):
    C_TYPES = ['EnumType']

    """ 
    Class for generating enumerated types. 
    
    :usage      |>>> from projex.enum import enum
                |>>> TestType = enum( 'Value1', 'Value2', 'Value3' )
                |>>> TestType.Value1 | TestType.Value2
                |3
                |>>> (3 & TestType.Value1) != 0
                |True
                |>>> TestType['Value1']
                |1
                |>>> TestType[3]
                |'Value1'
                |>>> TestType.Value1
                |1
                |>>> TestType.keys()
                |[1,2,4]
    """
    def __json__(self):
        return dict(self)

    def __call__(self, key):
        """
        Same as __getitem__.  This will cast the inputted key to its corresponding
        value in the enumeration.  This works for both numeric and alphabetical
        values.
        
        :param      key | <str> || <int>
        
        :return     <int> || <str>
        """
        if isinstance(key, set):
            return self.fromSet(key)
        else:
            return self[key]

    def __getitem__(self, key):
        """
        Overloads the base dictionary functionality to support
        lookups by value as well as by key.  If the inputted
        type is an integer, then a string is returned.   If the
        lookup is a string, then an integer is returned
        
        :param      key     <str> || <int>
        :return     <int> || <key>
        """
        # lookup the key for the inputted value
        if type(key) in (int, long):
            result = self.text(key)
            if not result:
                raise KeyError(key)
            return result

        # lookup the value for the inputted key
        else:
            return super(enum, self).__getitem__(key)

    def __init__(self, *args, **kwds):
        """
        Initializes the enum type by assigning a binary
        value to the inputted arguments in the order they
        are supplied.
        """
        super(enum, self).__init__()

        # initialize from a wrapped C Enum type
        if len(args) == 1 and type(args[0]).__name__ in enum.C_TYPES:
            cenum = args[0]
            args = tuple()

            for k in dir(cenum):
                val = getattr(cenum, k)
                if type(val) == cenum:
                    kwds[k] = val

        # store the base types for different values
        self._bases = {}
        self._labels = {}

        # update based on the inputted arguments
        kwds.update(dict([(key, 2 ** index) for index, key in enumerate(args)]))

        # set the properties
        for key, value in kwds.items():
            setattr(self, key, value)

        # update the keys based on the current keywords
        self.update(kwds)

    def add(self, key, value=None):
        """
        Adds the new key to this enumerated type.
        
        :param      key | <str>
        """
        if value is None:
            value = 2 ** (len(self))

        self[key] = value
        setattr(self, key, self[key])
        return value

    def all(self):
        """
        Returns all the values joined together.
        
        :return     <int>
        """
        out = 0
        for key, value in self.items():
            out |= value
        return out

    def base(self, value, recurse=True):
        """
        Returns the root base for the given value from this enumeration.
        
        :param      value   | <variant>
                    recurse | <bool>
        """
        while value in self._bases:
            value = self._bases[value]
            if not recurse:
                break
        return value

    def displayText(self, value, blank='', joiner=', '):
        """
        Returns the display text for the value associated with
        the inputted text.  This will result in a comma separated
        list of labels for the value, or the blank text provided if
        no text is found.
        
        :param      value  | <variant>
                    blank  | <str>
                    joiner | <str>
        
        :return     <str>
        """
        if value is None:
            return ''

        labels = []
        for key, my_value in sorted(self.items(), key=lambda x: x[1]):
            if value & my_value:
                labels.append(self._labels.get(my_value, text.pretty(key)))

        return joiner.join(labels) or blank

    def extend(self, base, key, value=None):
        """
        Adds a new definition to this enumerated type, extending the given
        base type.  This will create a new key for the type and register
        it as a new viable option from the system, however, it will also
        register its base information so you can use enum.base to retrieve
        the root type.
        
        :param      base  | <variant> | value for this enumeration
                    key   | <str>     | new key for the value
                    value | <variant> | if None is supplied, it will be auto-assigned
        
        :usage      |>>> from projex.enum import enum
                    |>>> Types = enum('Integer', 'Boolean')
                    |>>> Types.Integer
                    |1
                    |>>> Types.Boolean
                    |2
                    |>>> Types.extend(Types.Integer, 'BigInteger')
                    |>>> Types.BigInteger
                    |4
                    |>>> Types.base(Types.BigInteger)
                    |1
        """
        new_val = self.add(key, value)
        self._bases[new_val] = base

    def fromSet(self, values):
        """
        Generates a flag value based on the given set of values.

        :param values: <set>

        :return: <int>
        """
        value = 0
        for flag in values:
            value |= self(flag)
        return value

    def label(self, value):
        """
        Returns a pretty text version of the key for the inputted value.

        :param      value | <variant>

        :return     <str>
        """
        return self._labels.get(value) or text.pretty(self(value))

    def labels(self):
        """
        Return a list of "user friendly" labels.
        
        :return     <list> [ <str>, .. ]
        """
        return [self._labels.get(value) or text.pretty(key)
                for key, value in sorted(self.items(), key=lambda x: x[1])]

    def setLabel(self, value, label):
        """
        Sets the label text for the inputted value.  This will override the default pretty
        text label that is used for the key.

        :param      value | <variant>
                    label | <str>
        """
        if label:
            self._labels[value] = label
        else:
            self._labels.pop(value, None)

    def text(self, value, default=''):
        """
        Returns the text for the inputted value.
        
        :return     <str>
        """
        for key, val in self.items():
            if val == value:
                return key
        return default

    def toSet(self, flags):
        """
        Generates a flag value based on the given set of values.

        :param values: <set>

        :return: <int>
        """
        return {key for key, value in self.items() if value & flags}

    def valueByLabel(self, label):
        """
        Determine a given value based on the inputted label.

        :param      label   <str>
        
        :return     <int>
        """
        keys = self.keys()
        labels = [text.pretty(key) for key in keys]
        if label in labels:
            return self[keys[labels.index(label)]]
        return 0
