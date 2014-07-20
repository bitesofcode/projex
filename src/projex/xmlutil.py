"""
Defines helper methods to XML.
"""

# define authorship information
__authors__         = ['Eric Hulser', 'Michael Hale Ligh']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software, LLC'
__license__         = 'LGPL'

__maintainer__      = 'Projex Software, LLC'
__email__           = 'team@projexsoftware.com'

from collections import OrderedDict
from xml.etree import ElementTree

from .addon import AddonManager
from .decorators import abstractmethod
from .text import nativestring

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

    def testTag(self, elem, tag):
        """
        Tests the element's tag to make sure it matches the inputed one.  If
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
        Converts the inputed element to a Python object by looking through
        the IO addons for the element's tag.
        
        :param      elem | <xml.etree.ElementTree.Element>
        
        :return     <variant>
        """
        if elem is None:
            return None
        
        addon = cls.byName(elem.tag)
        if not addon:
            raise RuntimeError, '{0} is not a supported XML tag'.format(elem.tag)
        
        return addon.load(elem)

    @classmethod
    def toXml(cls, data, xparent=None):
        """
        Converts the inputed element to a Python object by looking through
        the IO addons for the element's tag.
        
        :param      data     | <variant>
                    xparent | <xml.etree.ElementTree.Element> || None
        
        :return     <xml.etree.ElementTree.Element>
        """
        if data is None:
            return None
        
        name = type(data).__name__
        addon = cls.byName(name)
        if not addon:
            raise RuntimeError, '{0} is not a supported XML tag'.format(name)
        
        return addon.save(data, xparent)

# B
#----------------------------------------------------------------------

class BoolIO(XmlDataIO):
    def load(self, elem):
        """
        Converts the inputed bool tag to Python.
        
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
        
        elem.text = str(data)
        return elem

XmlDataIO.registerAddon('bool', BoolIO())

# D
#----------------------------------------------------------------------

class DictIO(XmlDataIO):
    def load(self, elem):
        """
        Converts the inputed dict tag to Python.
        
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
            xitem.set('key', nativestring(key))
            XmlDataIO.toXml(value, xitem)
        
        return elem

XmlDataIO.registerAddon('dict', DictIO())

# F
#----------------------------------------------------------------------

class FloatIO(XmlDataIO):
    def load(self, elem):
        """
        Converts the inputed float tag to Python.
        
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
        
        elem.text = str(data)
        return elem

XmlDataIO.registerAddon('float', FloatIO())

# I
#----------------------------------------------------------------------

class IntegerIO(XmlDataIO):
    def load(self, elem):
        """
        Converts the inputed int tag to Python.
        
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
        
        elem.text = str(data)
        return elem

XmlDataIO.registerAddon('int', IntegerIO())

# L
#----------------------------------------------------------------------

class ListIO(XmlDataIO):
    def load(self, elem):
        """
        Converts the inputed list tag to Python.
        
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
#----------------------------------------------------------------------

class OrderedDictIO(XmlDataIO):
    def load(self, elem):
        """
        Converts the inputed ordereddict tag to Python.
        
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
            xitem.set('key', nativestring(key))
            XmlDataIO.toXml(value, xitem)
        
        return elem

XmlDataIO.registerAddon('OrderedDict', OrderedDictIO())

# S
#----------------------------------------------------------------------

class SetIO(XmlDataIO):
    def load(self, elem):
        """
        Converts the inputed set tag to Python.
        
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
        Converts the inputed string tag to Python.
        
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
        
        elem.text = nativestring(data)
        return elem

XmlDataIO.registerAddon('str', StringIO())

# T
#----------------------------------------------------------------------

class TupleIO(XmlDataIO):
    def load(self, elem):
        """
        Converts the inputed tuple tag to Python.
        
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
