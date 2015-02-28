""" Defines a commonly used data paradigm for all projex systems. """

from .text import nativestring as nstr
from xml.etree import ElementTree


class DataSet(dict):
    _xmlTypes = {}

    def __init__(self, *args, **defaults):
        super(DataSet, self).__init__()

        for arg in args:
            defaults.update(arg)

        self._defaults = defaults
        self.update(defaults)

    def __add__(self, other):
        """
        Adds two data sets together and returns a new dataset.
        
        :param      other | <DataSet> || <dict>
        """
        if not isinstance(other, dict):
            return super(DataSet, self).__add__(other)

        output = DataSet(self)
        output.update(other)
        return output

    def define(self, key, value):
        """
        Defines the value for the inputted key by setting both its default and \
        value to the inputted value.
        
        :param      key   | <str>
                    value | <variant>
        """
        skey = nstr(key)
        self._defaults[skey] = value
        self[skey] = value

    def reset(self):
        """
        Resets the values for this option set to the default values.
        """
        self.clear()
        self.update(self._defaults)

    def setValue(self, key, value):
        """
        Sets the current value for the inputted key to the given value.
        
        :param      key     | <str>
                    value   | <variant>
        """
        self[nstr(key)] = value

    def toXml(self, xparent):
        """
        Saves the settings for this dataset to the inputted parent xml.
        
        :param      xparent | <xml.etree.ElementTree.Element>
        """
        for key, value in self.items():
            elem = ElementTree.SubElement(xparent, 'entry')
            typ = type(elem).__name__

            elem.set('key', key)
            elem.set('type', typ)

            if typ in DataSet._xmlTypes:
                DataSet._xmlTypes[typ][0](elem, value)
            else:
                elem.set('value', nstr(value))

    def value(self, key, default=None):
        """
        Returns the current value for the inputted key.
        
        :param      key     | <str>
                    default | <variant>
        
        :return     <variant>
        """
        return self.get(nstr(key), default)

    @classmethod
    def fromXml(cls, xparent):
        """
        Loads the settings for this dataset to the inputted parent xml.
        
        :param      xparent | <xml.etree.ElementTree.Element>
        """
        output = cls()

        for xentry in xparent:
            key = xentry.get('key')
            if not key:
                continue

            typ = xentry.get('type', 'str')

            if typ in DataSet._xmlTypes:
                value = DataSet._xmlTypes[typ][1](xentry)
            else:
                value = xentry.get('value', '')

            output.define(key, value)

        return output

    @staticmethod
    def registerXmlType(typ, encoder, decoder):
        """
        Registers a data type to encode/decode for xml settings.
        
        :param      typ     | <object>
                    encoder | <method>
                    decoder | <method>
        """
        DataSet._xmlTypes[nstr(typ)] = (encoder, decoder)

# ------------------------------------------------------------------------------

DataSet.registerXmlType('int',
                        lambda x, v: x.set('value', nstr(v)),
                        lambda x: int(x.get('value', 0)))

DataSet.registerXmlType('float',
                        lambda x, v: x.set('value', nstr(v)),
                        lambda x: float(x.get('value', 0)))

DataSet.registerXmlType('bool',
                        lambda x, v: x.set('value', nstr(v)),
                        lambda x: x.get('value') == 'True')