""" Defines a file/folder template architecture. """

import logging
import os
import re
import tempfile
import zipfile

from collections import OrderedDict
from xml.etree import ElementTree

import projex.text
from projex import makotext
from .text import nativestring as nstr

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------


class Property(object):
    def __init__(self, **kwds):
        self.type = kwds.get('type', 'str')
        self.name = kwds.get('name', '')
        self.value = kwds.get('value', None)
        self.default = kwds.get('default', None)
        self.choices = kwds.get('choices', [])
        self.required = kwds.get('required', False)
        self.regex = kwds.get('regex', '')
        self.hidden = kwds.get('hidden', False)
        self.label = kwds.get('label', projex.text.pretty(self.name))

    def prompt(self, error=''):
        """
        Prompts the user to set the value for this item.
        
        :return     <bool> | success
        """
        if self.hidden:
            return True

        cmd = [self.label]

        if self.default is not None:
            cmd.append('(default: {0})'.format(self.default))
        elif not self.required:
            cmd.append('(default: )')

        if self.type == 'bool':
            cmd.append('(y/n)')

        if self.choices:
            print 'Choices:'
            for choice in self.choices:
                print choice
        if error:
            print error

        value = raw_input(' '.join(cmd) + ':')
        if value == '':
            value = self.default

        if self.type == 'bool':
            if value == 'y':
                value = True
            elif value == 'n':
                value = False
            else:
                value = self.default

        if value is None and self.required:
            return self.prompt('{0} is required.')

        if self.regex and not re.match(self.regex, value):
            error = '{0} must match {1}'.format(self.name, self.regex)
            return self.prompt(error)

        self.value = value
        return True

    @staticmethod
    def fromXml(xprop):
        opts = xprop.attrib.copy()
        typ = opts.pop('type', 'str')

        for key, value in opts.items():
            try:
                value = eval(value)
            except StandardError:
                pass

            opts[key] = value

        choices = []
        for xchoice in xprop:
            choices.append(xchoice.text)

        opts['type'] = typ
        opts['choices'] = choices
        return Property(**opts)


#----------------------------------------------------------------------

class Template(object):
    GlobalOptions = {}
    Plugins = {}

    def __init__(self, **kwds):
        self.name = kwds.get('name', '')
        self.text = ''
        self.options = {}

    def render(self, **options):
        opts = {}
        opts.update(Template.GlobalOptions)
        opts.update(self.options)
        opts.update(options)

        return makotext.render(self.text, options)


#----------------------------------------------------------------------

class Scaffold(object):
    def __init__(self):
        self._name = ''
        self._group = ''
        self._language = ''
        self._icon = ''
        self._description = ''
        self._source = ''
        self._properties = OrderedDict()
        self._templates = {}

    def addProperty(self, prop):
        """
        Adds a new property to this scaffold.
        
        :param      prop | <projex.scaffold.Property>
        """
        self._properties[prop.name] = prop

    def addTemplate(self, template):
        """
        Adds a new template to this scaffold.  Templates are other
        renderable items within the system.
        
        :param      template | <projex.scaffold.Template>
        """
        self._templates[template.name] = template

    def build(self, outpath, structure=None):
        """
        Builds this scaffold out to the given filepath with the 
        chosen structure.
        
        :param      outpath   | <str>
                    structure | <xml.etree.ElementTree.Element> || None

        :return     <bool> | success
        """
        if not os.path.exists(outpath):
            return False

        opts = {'scaffold': self}

        if structure is not None:
            xstruct = structure
        else:
            xstruct = self.structure()

        if zipfile.is_zipfile(self.source()):
            zfile = zipfile.ZipFile(self.source(), 'r')
        else:
            zfile = None
            base = os.path.dirname(self.source())

        # build the structure information
        # noinspection PyShadowingNames
        def build_level(root, xlevel):
            # ignore the entry
            if xlevel.get('enabled', 'True') == 'False':
                return

            # create a folder
            if xlevel.tag == 'folder':
                name = makotext.render(xlevel.get('name'), opts)
                dirname = os.path.join(root, name)
                if not os.path.exists(dirname):
                    os.mkdir(dirname)

                for xchild in xlevel:
                    build_level(dirname, xchild)

            # create a file
            elif xlevel.tag == 'file':
                name = makotext.render(xlevel.get('name'), opts)
                fname = os.path.join(root, name)

                # create from a template
                templ = xlevel.get('templ')
                if templ:
                    if zfile:
                        templ_str = zfile.read('templ/{0}'.format(templ))
                    else:
                        templ_path = os.path.join(base, 'templ', templ)
                        templ_str = open(templ_path, 'r').read()

                    rendered = makotext.render(templ_str, opts)
                    rendered = rendered.replace('\r\n', '\r')

                    f = open(fname, 'w')
                    f.write(rendered)
                    f.close()

                # create a blank file
                else:
                    f = open(fname, 'w')
                    f.close()

        for xlevel in xstruct:
            build_level(outpath, xlevel)

        if zfile:
            zfile.close()
        return True

    def description(self):
        """
        Returns the description associated with this scaffold.
        
        :return     <str>
        """
        return self._description

    def get(self, key):
        """
        Returns the value of the property for this scaffold for the given key.
        
        :param      key | <str>
        
        :return     <variant>
        """
        return self._properties[key].value

    def group(self):
        """
        Returns the group associated with this scaffold.
        
        :return     <str>
        """
        return self._group

    def icon(self):
        """
        Returns the icon associated with this scaffold.
        
        :return     <str>
        """
        return self._icon

    def language(self):
        """
        Returns the language associated with this scaffold.
        
        :return     <str>
        """
        return self._language

    def name(self):
        """
        Returns the name associated with this scaffold.
        
        :return     <str>
        """
        return self._name

    def property(self, name):
        """
        Returns the property for the given name.
        
        :return     <Property> || None
        """
        return self._properties.get(nstr(name))

    def properties(self):
        """
        Returns a list of the scaffold properties associated with this instance.
        
        :return     [<Property>, ..]
        """
        return self._properties.values()

    def render(self, template, fail='## :todo: add {template}'):
        """
        Returns the rendered value for the inputted template name.
        
        :param      template | <str>
        """
        try:
            return self._templates[template].render(scaffold=self)
        except KeyError:
            return fail.format(template=template)

    def run(self, path=None):
        """
        Runs the scaffold option generation for this scaffold in the given
        path.  If no path is supplied, then the current path is used.
        
        :param      path | <str> || None
        """
        if path is None:
            path = '.'

        for prop in self._properties.values():
            if not prop.prompt():
                return False

        return self.build(path)

    def setDescription(self, description):
        """
        Sets the description of this scaffold to the inputted description.
        
        :param      description | <str>
        """
        self._description = description

    def setGroup(self, group):
        """
        Sets the group of this scaffold to the inputted group.
        
        :param      group | <str>
        """
        self._group = group

    def setIcon(self, icon):
        """
        Sets the icon of this scaffold to the inputted icon.
        
        :param      icon | <str>
        """
        self._icon = icon

    def setLanguage(self, lang):
        """
        Sets the language of this scaffold to the inputted language.
        
        :param      lang | <str>
        """
        self._language = lang

    def setName(self, name):
        """
        Sets the name of this scaffold to the inputted name.
        
        :param      name | <str>
        """
        self._name = name

    def setSource(self, source):
        """
        Sets the source file location for this scaffold.
        
        :param      source | <str>
        """
        self._source = source

    def set(self, key, value):
        """
        Sets the value of the property for this scaffold to the given key.
        
        :param      key | <str>
                    value | <variant>
        """
        self._properties[key].value = value

    def source(self):
        """
        Returns the source associated with this scaffold.
        
        :return     <str>
        """
        return self._source

    def structure(self):
        """
        Returns the structure for this scaffold.
        
        :return     <xml.etree.ElementTree.Element> || None
        """
        opts = {'scaffold': self}

        # build from a zip file
        if zipfile.is_zipfile(self.source()):
            zfile = zipfile.ZipFile(self.source(), 'r')
            try:
                contents = zfile.read('structure.xml')
                contents = makotext.render(contents, opts)
                zfile.close()
                return ElementTree.fromstring(contents)
            except StandardError:
                logger.exception('Failed to load structure.')
                zfile.close()
                return None

        else:
            try:
                filename = os.path.join(os.path.dirname(self.source()),
                                        'structure.xml')
                xdata = open(filename, 'r').read()
                xdata = makotext.render(xdata, opts)
                return ElementTree.fromstring(xdata)
            except StandardError:
                logger.exception('Failed to load structure.')
                return None

    def template(self, key):
        """
        Returns the template associated with this scaffold.
        
        :param      key | <str>
        
        :return     <projex.scaffold.Template> || None
        """
        try:
            return self._templates[key]
        except KeyError:
            return Template.Plugins[key]

    def uifile(self):
        """
        Returns the uifile for this scaffold.
        
        :return     <str>
        """
        output = ''

        # build from a zip file
        if zipfile.is_zipfile(self.source()):
            zfile = zipfile.ZipFile(self.source(), 'r')
            if 'properties.ui' in zfile.namelist():
                tempdir = tempfile.gettempdir()
                output = os.path.join(tempdir,
                                      '{0}_properties.ui'.format(self.name()))

                f = open(output, 'w')
                f.write(zfile.read('properties.ui'))
                f.close()
            zfile.close()

        else:
            uifile = os.path.join(os.path.dirname(self.source()),
                                  'properties.ui')
            if os.path.exists(uifile):
                output = uifile

        return output

    @staticmethod
    def load(filename):
        """
        Loads the scaffold from the given XML file.
        
        :param      filename | <str>
        
        :return     <Scaffold> || None
        """
        # parse a zipped file
        if zipfile.is_zipfile(filename):
            zfile = zipfile.ZipFile(filename, 'r')
            try:
                xml = ElementTree.fromstring(zfile.read('scaffold.xml'))
            except StandardError:
                logger.exception('Failed to load scaffold: {0}'.format(filename))
                zfile.close()
                return None
            zfile.close()

        # parse a standard xml file
        else:
            try:
                xml = ElementTree.parse(filename).getroot()
            except StandardError:
                logger.exception('Failed to load scaffold: {0}'.format(filename))
                return None

        # generate a scaffold
        scaffold = Scaffold()
        scaffold.setSource(filename)
        scaffold.setName(xml.get('name', 'Missing'))
        scaffold.setGroup(xml.get('group', 'Default'))
        scaffold.setLanguage(xml.get('lang', 'Python'))
        scaffold.setIcon(xml.get('icon', ''))

        # define properties
        xprops = xml.find('properties')
        if xprops is not None:
            for xprop in xprops:
                scaffold.addProperty(Property.fromXml(xprop))

        return scaffold
