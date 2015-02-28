"""
Defines helper methods to XML.
"""

from collections import OrderedDict
from xml.etree import ElementTree

from .addon import AddonManager
from .decorators import abstractmethod
from .text import nativestring as nstr


class XmlObject(AddonManager):
    def __init__(self):
        super(XmlObject, self).__init__()

        # define the custom properties
        self._xmlData = {}

    def allXmlData(self):
        """
        Returns a dictionary of the properties that are loaded and saved to the XML file for this object.

        :return     {<str> name: <variant> value, ..}
        """
        return self._xmlData

    def loadXml(self, xml):
        """
        Loads the data for this object from XML.

        :param      xml | <xml.etree.ElementTree.Element> || None
        """
        if xml is not None:
            for xprop in xml:
                self.loadXmlProperty(xprop)

    def loadXmlProperty(self, xprop):
        """
        Loads an XML property that is a child of the root data being loaded.

        :param      xprop | <xml.etree.ElementTree.Element>
        """
        if xprop.tag == 'property':
            value = self.dataInterface().fromXml(xprop[0])
            self._xmlData[xprop.get('name', '')] = value

    def setXmlData(self, name, value):
        """
        Sets the property for this XML object to the inputted name and value.

        :param      name  | <str>
                    value | <variant>
        """
        self._xmlData[name] = value

    def toXml(self, xparent=None):
        """
        Converts this object to XML.

        :param      xparent | <xml.etree.ElementTree.Element> || None

        :return     <xml.etree.ElementTree.Element>
        """
        if xparent is None:
            xml = ElementTree.Element('object')
        else:
            xml = ElementTree.SubElement(xparent, 'object')

        xml.set('class', self.__class__.__name__)
        for name, value in self._xmlData.items():
            xprop = ElementTree.SubElement(xml, 'property')
            xprop.set('name', name)
            XmlDataIO.toXml(value, xprop)
        return xml

    def xmlData(self, name, default=None):
        """
        Returns the XML property that was created for this object.

        :return     <variant>
        """
        return self._xmlData.get(name, default)

    @classmethod
    def fromXml(cls, xml):
        """
        Restores an object from XML.

        :param      xml | <xml.etree.ElementTree.Element>

        :return     subclass of <XmlObject>
        """
        clsname = xml.get('class')
        if clsname:
            subcls = XmlObject.byName(clsname)
            if subcls is None:
                inst = MissingXmlObject(clsname)
            else:
                inst = subcls()
        else:
            inst = cls()

        inst.loadXml(xml)
        return inst

    @staticmethod
    def dataInterface():
        """
        Returns the XmlDataIO interface associated with this XmlObject class.

        :return     subclass of <XmlDataIO>
        """
        return XmlDataIO


class MissingXmlObject(XmlObject):
    def __init__(self, missingType):
        super(MissingXmlObject, self).__init__()

        self.setXmlData('missingType', missingType)


# ----------------------------------------------------------------------

class XmlDataIO(AddonManager):
    @abstractmethod('XmlDataIO', 'No load method defined.')
    def load(self, elem):
        """
        Parses the element from XML to Python.
        
        :param      elem | <xml.etree.ElementTree.Element>
        
        :return     <variant>
        """
        return None

    @abstractmethod('XmlDataIO', 'No parse method defined.')
    def save(self, data, xparent=None):
        """
        Parses the element from XML to Python.
        
        :param      data    | <variant>
                    xparent | <xml.etree.ElementTree.Element> || None
        
        :return     <xml.etree.ElementTree.Element>
        """
        return None

    @staticmethod
    def testTag(elem, tag):
        """
        Tests the element's tag to make sure it matches the inputted one.  If
        it fails, a RuntimeError will be raised.
        
        :param      elem | <xml.etree.ElementTree.Element>
                    tag  | <str>
        
        :return     <bool>
        """
        if elem.tag == tag:
            return True
        else:
            raise 'Invalid element tag "{0}", expected "{1}"'.format(elem.tag,
                                                                     tag)

    @classmethod
    def fromXml(cls, elem):
        """
        Converts the inputted element to a Python object by looking through
        the IO addons for the element's tag.
        
        :param      elem | <xml.etree.ElementTree.Element>
        
        :return     <variant>
        """
        if elem is None:
            return None

        addon = cls.byName(elem.tag)
        if not addon:
            raise RuntimeError('{0} is not a supported XML tag'.format(elem.tag))

        return addon.load(elem)

    @classmethod
    def toXml(cls, data, xparent=None):
        """
        Converts the inputted element to a Python object by looking through
        the IO addons for the element's tag.
        
        :param      data     | <variant>
                    xparent | <xml.etree.ElementTree.Element> || None
        
        :return     <xml.etree.ElementTree.Element>
        """
        if data is None:
            return None

        # store XmlObjects separately from base types
        if isinstance(data, XmlObject):
            name = 'object'
        else:
            name = type(data).__name__

        addon = cls.byName(name)
        if not addon:
            raise RuntimeError('{0} is not a supported XML tag'.format(name))

        return addon.save(data, xparent)


# B
# ----------------------------------------------------------------------

class BoolIO(XmlDataIO):
    def load(self, elem):
        """
        Converts the inputted bool tag to Python.
        
        :param      elem | <xml.etree.ElementTree>
        
        :return     <bool>
        """
        self.testTag(elem, 'bool')
        return elem.text == 'True'

    def save(self, data, xparent=None):
        """
        Parses the element from XML to Python.
        
        :param      data    | <variant>
                    xparent | <xml.etree.ElementTree.Element> || None
        
        :return     <xml.etree.ElementTree.Element>
        """
        if xparent is not None:
            elem = ElementTree.SubElement(xparent, 'bool')
        else:
            elem = ElementTree.Element('bool')

        elem.text = nstr(data)
        return elem


XmlDataIO.registerAddon('bool', BoolIO())

# D
# ----------------------------------------------------------------------


class DictIO(XmlDataIO):
    def load(self, elem):
        """
        Converts the inputted dict tag to Python.
        
        :param      elem | <xml.etree.ElementTree>
        
        :return     <dict>
        """
        self.testTag(elem, 'dict')

        out = {}
        for xitem in elem:
            key = xitem.get('key')
            try:
                value = XmlDataIO.fromXml(xitem[0])
            except IndexError:
                value = None
            out[key] = value
        return out

    def save(self, data, xparent=None):
        """
        Parses the element from XML to Python.
        
        :param      data    | <variant>
                    xparent | <xml.etree.ElementTree.Element> || None
        
        :return     <xml.etree.ElementTree.Element>
        """
        if xparent is not None:
            elem = ElementTree.SubElement(xparent, 'dict')
        else:
            elem = ElementTree.Element('dict')

        for key, value in sorted(data.items()):
            xitem = ElementTree.SubElement(elem, 'item')
            xitem.set('key', nstr(key))
            XmlDataIO.toXml(value, xitem)

        return elem


XmlDataIO.registerAddon('dict', DictIO())

# F
# ----------------------------------------------------------------------


class FloatIO(XmlDataIO):
    def load(self, elem):
        """
        Converts the inputted float tag to Python.
        
        :param      elem | <xml.etree.ElementTree>
        
        :return     <float>
        """
        self.testTag(elem, 'float')
        return float(elem.text) if elem.text is not None else 0

    def save(self, data, xparent=None):
        """
        Parses the element from XML to Python.
        
        :param      data    | <variant>
                    xparent | <xml.etree.ElementTree.Element> || None
        
        :return     <xml.etree.ElementTree.Element>
        """
        if xparent is not None:
            elem = ElementTree.SubElement(xparent, 'float')
        else:
            elem = ElementTree.Element('float')

        elem.text = nstr(data)
        return elem


XmlDataIO.registerAddon('float', FloatIO())

# I
# ----------------------------------------------------------------------


class IntegerIO(XmlDataIO):
    def load(self, elem):
        """
        Converts the inputted int tag to Python.
        
        :param      elem | <xml.etree.ElementTree>
        
        :return     <int>
        """
        self.testTag(elem, 'int')
        return int(elem.text) if elem.text is not None else 0

    def save(self, data, xparent=None):
        """
        Parses the element from XML to Python.
        
        :param      data    | <variant>
                    xparent | <xml.etree.ElementTree.Element> || None
        
        :return     <xml.etree.ElementTree.Element>
        """
        if xparent is not None:
            elem = ElementTree.SubElement(xparent, 'int')
        else:
            elem = ElementTree.Element('int')

        elem.text = nstr(data)
        return elem


XmlDataIO.registerAddon('int', IntegerIO())

# L
# ----------------------------------------------------------------------


class ListIO(XmlDataIO):
    def load(self, elem):
        """
        Converts the inputted list tag to Python.
        
        :param      elem | <xml.etree.ElementTree>
        
        :return     <list>
        """
        self.testTag(elem, 'list')
        out = []
        for xitem in elem:
            out.append(XmlDataIO.fromXml(xitem))
        return out

    def save(self, data, xparent=None):
        """
        Parses the element from XML to Python.
        
        :param      data    | <variant>
                    xparent | <xml.etree.ElementTree.Element> || None
        
        :return     <xml.etree.ElementTree.Element>
        """
        if xparent is not None:
            elem = ElementTree.SubElement(xparent, 'list')
        else:
            elem = ElementTree.Element('list')

        for item in data:
            XmlDataIO.toXml(item, elem)

        return elem


XmlDataIO.registerAddon('list', ListIO())

# O
# ----------------------------------------------------------------------


class ObjectIO(XmlDataIO):
    def load(self, elem):
        """
        Converts the inputted object to Python.  This object class must have the fromXml method defined
        for this to work.

        :param      elem | <xml.etree.ElementTree>

        :return     <object>
        """
        self.testTag(elem, 'object')
        return XmlObject.fromXml(elem)

    def save(self, data, xparent=None):
        """
        Parses the element from XML to Python.

        :param      data    | <variant>
                    xparent | <xml.etree.ElementTree.Element> || None

        :return     <xml.etree.ElementTree.Element>
        """
        return data.toXml(xparent)


XmlDataIO.registerAddon('object', ObjectIO())


class OrderedDictIO(XmlDataIO):
    def load(self, elem):
        """
        Converts the inputted ordereddict tag to Python.
        
        :param      elem | <xml.etree.ElementTree>
        
        :return     <OrderedDict>
        """
        self.testTag(elem, 'OrderedDict')

        out = OrderedDict()
        for xitem in elem:
            key = xitem.get('key')
            try:
                value = XmlDataIO.fromXml(xitem[0])
            except IndexError:
                value = None
            out[key] = value
        return out

    def save(self, data, xparent=None):
        """
        Parses the element from XML to Python.
        
        :param      data    | <variant>
                    xparent | <xml.etree.ElementTree.Element> || None
        
        :return     <xml.etree.ElementTree.Element>
        """
        if xparent is not None:
            elem = ElementTree.SubElement(xparent, 'OrderedDict')
        else:
            elem = ElementTree.Element('OrderedDict')

        for key, value in sorted(data.items()):
            xitem = ElementTree.SubElement(elem, 'item')
            xitem.set('key', nstr(key))
            XmlDataIO.toXml(value, xitem)

        return elem


XmlDataIO.registerAddon('OrderedDict', OrderedDictIO())

# S
# ----------------------------------------------------------------------


class SetIO(XmlDataIO):
    def load(self, elem):
        """
        Converts the inputted set tag to Python.
        
        :param      elem | <xml.etree.ElementTree>
        
        :return     <set>
        """
        self.testTag(elem, 'set')
        out = set()
        for xitem in elem:
            out.add(XmlDataIO.fromXml(xitem))
        return out

    def save(self, data, xparent=None):
        """
        Parses the element from XML to Python.
        
        :param      data    | <variant>
                    xparent | <xml.etree.ElementTree.Element> || None
        
        :return     <xml.etree.ElementTree.Element>
        """
        if xparent is not None:
            elem = ElementTree.SubElement(xparent, 'set')
        else:
            elem = ElementTree.Element('set')

        for item in data:
            XmlDataIO.toXml(item, elem)

        return elem


XmlDataIO.registerAddon('set', SetIO())


class StringIO(XmlDataIO):
    def load(self, elem):
        """
        Converts the inputted string tag to Python.
        
        :param      elem | <xml.etree.ElementTree>
        
        :return     <str>
        """
        self.testTag(elem, 'str')
        return elem.text if elem.text is not None else ''

    def save(self, data, xparent=None):
        """
        Parses the element from XML to Python.
        
        :param      data    | <variant>
                    xparent | <xml.etree.ElementTree.Element> || None
        
        :return     <xml.etree.ElementTree.Element>
        """
        if xparent is not None:
            elem = ElementTree.SubElement(xparent, 'str')
        else:
            elem = ElementTree.Element('str')

        elem.text = nstr(data)
        return elem


XmlDataIO.registerAddon('str', StringIO())

# T
#----------------------------------------------------------------------


class TupleIO(XmlDataIO):
    def load(self, elem):
        """
        Converts the inputted tuple tag to Python.
        
        :param      elem | <xml.etree.ElementTree>
        
        :return     <tuple>
        """
        self.testTag(elem, 'tuple')
        out = []
        for xitem in elem:
            out.append(XmlDataIO.fromXml(xitem))
        return tuple(out)

    def save(self, data, xparent=None):
        """
        Parses the element from XML to Python.
        
        :param      data    | <variant>
                    xparent | <xml.etree.ElementTree.Element> || None
        
        :return     <xml.etree.ElementTree.Element>
        """
        if xparent is not None:
            elem = ElementTree.SubElement(xparent, 'tuple')
        else:
            elem = ElementTree.Element('tuple')

        for item in data:
            XmlDataIO.toXml(item, elem)

        return elem


XmlDataIO.registerAddon('tuple', TupleIO())
