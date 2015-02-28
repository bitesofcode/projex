""" Defines the Plugin class, a generic way to define Python plugins. """

import glob
import os.path
import logging
import sys

from .text import nativestring as nstr
from xml.etree import ElementTree

import projex
import projex.text
from projex.enum import enum

__all__ = ['Plugin']

logger = logging.getLogger(__name__)

# plugin registry file format
"""
<plugin name="Plugin Name" icon="./icon.png" version="1.0">
    <description>This is my description</description
    <author>Eric Hulser</author>
    <email>eric.hulser@gmail.com</email>
    <url>http://projexsoftware.github.io</url>
    <import path="./__init__.py"/>
</plugin>
"""


class Plugin(object):
    """
    Defines the base class for generating a plugin based system in Python.
    This class is just an abstract framework to provide an interface to
    managing multiple objects of a particular plugin type through a simple
    registration system.  To use, you will need to subclass this object and
    implement your own abstract and virtual methods to provide an interface
    to your application, however it will handle all the common methods such
    as registration, enabling, etc. from here.
    
    :usage      |from projex.plugin import Plugin
                |from projex.decorators import abstractmethod
                |
                |class MyPlugin(Plugin):
                |   @abstractmethod
                |   def convert(self, value):
                |       pass
                |
                |class StringPlugin(MyPlugin):
                |   def __init__( self ):
                |       super(StringPlugin, self).__init__('string')
                |
                |   def convert(self, value):
                |       return str(value)
                |
                |class BoolPlugin(MyPlugin):
                |   def __init__( self ):
                |       super(StringPlugin, self).__init__('bool')
                |
                |   def convert(self, value):
                |       return bool(value)
                |
                |MyPlugin.register(StringPlugin())
                |MyPlugin.register(BoolPlugin())
                |
                |for plugin in MyPlugin.plugins():
                |   print plugin.instance().convert(1)
                |
                |print MyPlugin.plugin('string').instance().convert(1)
                
    """
    # define enums
    Type = enum('Module', 'Package', 'RegistryFile')

    def __init__(self, name, version=1.0):
        # define basic information
        self._name = nstr(name)
        self._version = version

        # define advanced information
        self._enabled = True
        self._filepath = ''
        self._icon = ''
        self._description = ''

        # define error information
        self._loaded = True
        self._instance = self
        self._error = None

        # define authorship information
        self._author = ''
        self._email = ''
        self._url = ''

        # define the filepath loading information
        mod = sys.modules.get(self.__class__.__module__)
        if mod:
            self._filepath = os.path.abspath(mod.__file__)

    def author(self):
        """
        Returns the author information for this plugin.
        
        :return     <str>
        """
        return self._author

    def description(self):
        """
        Returns the description for this plugin.
        
        :return     <str>
        """
        return self._description

    def disable(self):
        """
        Disables this plugin.
        
        :sa     setEnabled
        """
        self.setEnabled(False)

    def email(self):
        """
        Returns the email information for this plugin.
        
        :return     <str>
        """
        return self._email

    def enable(self):
        """
        Enables this plugin.
        
        :sa     setEnabled
        """
        self.setEnabled(True)

    def error(self):
        """
        Returns the error from this plugin.
        
        :return     <Exception> || None
        """
        return self._error

    def filepath(self):
        """
        Returns the filepath from which this plugin was loaded.
        
        :return     <str>
        """
        return self._filepath

    def icon(self):
        """
        Returns the icon filepath for this plugin.
        
        :return     <str>
        """
        path = self._icon
        if not path:
            return ''

        path = os.path.expandvars(os.path.expanduser(path))
        if path.startswith('.'):
            base_path = os.path.dirname(self.filepath())
            path = os.path.abspath(os.path.join(base_path, path))

        return path

    def instance(self):
        """
        Returns the main instance of this plugin.  When wanting to use
        custom methods from a plugin class, call this method first, as plugins
        may decide to generate their instances in different ways.  By default,
        this will just return the self value.  
        
        For instance, a PluginProxy class will load its plugin registration 
        information during the initialization stage, but not load the actual
        class until the instance method is called, delaying the load of the 
        actual module until later.
        """
        return self._instance

    def isEnabled(self):
        """
        Returns whether or not this plugin is enabled.
        
        :return     <bool>
        """
        return self._enabled and not self.isErrored()

    def isErrored(self):
        """
        Returns whether or not the plugin ran into errors.
        
        :return     <bool>
        """
        return self._error is not None

    def isLoaded(self):
        """
        Returns whether or not this plugin has been loaded or not.
        
        :return     <bool>
        """
        return self._loaded

    def name(self):
        """
        Returns the name for this plugin.
        
        :return     <str>
        """
        return self._name

    def setAuthor(self, author):
        """
        Sets the author information for this plugin.
        
        :param      author | <str>
        """
        self._author = nstr(author)

    def setDescription(self, description):
        """
        Sets the description for this plugin to the inputted plugin.
        
        :param      description | <str>
        """
        self._description = description

    def setEmail(self, email):
        """
        Sets the email information for this plugin.
        
        :param      email | <str>
        """
        self._email = nstr(email)

    def setEnabled(self, state):
        """
        Sets whether or not this plugin is enabled.
        
        :param      state | <bool>
        """
        self._enabled = state

    def setError(self, error):
        """
        Sets the error that this plugin ran into last.
        
        :param      error | <Exception> || None
        """
        self._error = error

    def setFilepath(self, filepath):
        """
        Sets the filepath location for this plugin.
        
        :param      filepath | <str>
        """
        self._filepath = filepath

    def setIcon(self, filepath):
        """
        Sets the icon filepath for this plugin to the inputted path.  This can
        be either an absolute path, or a relative path from the location this
        plugin was loaded from.
        
        :param      filepath | <str>
        """
        self._icon = nstr(filepath)

    def setUrl(self, url):
        """
        Sets the url information for this plugin.
        
        :param      url | <str>
        """
        self._url = nstr(url)

    def url(self):
        """
        Returns the URL information for this plugin.
        
        :return     <str>
        """
        return self._url

    def version(self):
        """
        Returns the version for this plugin.
        
        :return     <float>
        """
        return self._version

    @classmethod
    def addPluginPath(cls, pluginpath):
        """
        Adds the plugin path for this class to the given path.  The inputted
        pluginpath value can either be a list of strings, or a string
        containing paths separated by the OS specific path separator (':' on
        Mac & Linux, ';' on Windows)
        
        :param      pluginpath | [<str>, ..] || <str>
        """
        prop_key = '_%s__pluginpath' % cls.__name__
        curr_path = getattr(cls, prop_key, None)
        if not curr_path:
            curr_path = []
            setattr(cls, prop_key, curr_path)

        if isinstance(pluginpath, basestring):
            pluginpath = pluginpath.split(os.path.pathsep)

        for path in pluginpath:
            if not path:
                continue

            path = os.path.expanduser(os.path.expandvars(path))
            paths = path.split(os.path.pathsep)

            if len(paths) > 1:
                cls.addPluginPath(paths)
            else:
                curr_path.append(path)

    @classmethod
    def pluginRegisterType(cls):
        """
        Returns the register type for this plugin class.
        
        :return     <Plugin.RegisterType>
        """
        default = Plugin.Type.Module
        default |= Plugin.Type.Package
        default |= Plugin.Type.RegistryFile

        return getattr(cls, '_%s__pluginRegisterType', default)

    @classmethod
    def loadPlugins(cls):
        """
        Initializes the plugins by loading modules from the inputted paths.
        """
        plugs = getattr(cls, '_%s__plugins' % cls.__name__, None)
        if plugs is not None:
            return

        plugs = {}
        setattr(cls, '_%s__plugins' % cls.__name__, plugs)
        typ = cls.pluginRegisterType()

        for path in cls.pluginPath():
            base_package = projex.packageFromPath(path)
            base_path = os.path.normpath(projex.packageRootPath(path))

            # make sure it is at the front of the path
            if base_path in sys.path:
                sys.path.remove(base_path)

            sys.path.insert(0, base_path)
            processed = ['__init__']

            # load support for registries
            if typ & Plugin.Type.RegistryFile:
                files = glob.glob(os.path.join(path, '*/register.xml'))
                for file_ in files:
                    name = os.path.normpath(file_).split(os.path.sep)[-2]
                    processed.append(name)

                    try:
                        proxy = PluginProxy.fromFile(cls, file_)
                        cls.register(proxy)

                    except Exception, e:
                        name = projex.text.pretty(name)
                        err = Plugin(name)
                        err.setError(e)
                        err.setFilepath(file_)

                        cls.register(err)

                        # log the error
                        msg = "%s.plugin('%s') failed to load from %s."
                        logger.warning(msg % (cls.__name__, name, file_))
                        logger.error(e)

            # load support for packages
            if typ & Plugin.Type.Package:
                files = glob.glob(os.path.join(path, '*/__init__.py'))
                for file_ in files:
                    name = os.path.normpath(file_).split(os.path.sep)[-2]
                    if name in processed:
                        continue

                    processed.append(name)
                    package = '.'.join([base_package, name]).strip('.')
                    if not package:
                        continue

                    try:
                        __import__(package)

                    except Exception, e:
                        name = projex.text.pretty(name)
                        err = Plugin(name)
                        err.setError(e)
                        err.setFilepath(file_)

                        cls.register(err)

                        # log the error
                        msg = "%s.plugin('%s') failed to load from %s."
                        logger.warning(msg % (cls.__name__, name, file_))
                        logger.error(e)

            # load support for modules
            if typ & Plugin.Type.Module:
                files = glob.glob(os.path.join(path, '*.py'))
                for file_ in files:
                    name = os.path.basename(file_).split('.')[0]
                    if name in processed:
                        continue

                    processed.append(name)
                    package = '.'.join([base_package, name]).strip('.')
                    if not package:
                        continue

                    try:
                        __import__(package)

                    except Exception, e:
                        name = projex.text.pretty(name)
                        err = Plugin(name)
                        err.setError(e)
                        err.setFilepath(file_)

                        cls.register(err)

                        # log the error
                        msg = "%s.plugin('%s') failed to load from %s."
                        logger.warning(msg % (cls.__name__, name, file_))
                        logger.error(e)

    @classmethod
    def plugin(cls, name):
        """
        Retrieves the plugin based on the inputted name.
        
        :param      name | <str>
        
        :return     <Plugin>
        """
        cls.loadPlugins()
        plugs = getattr(cls, '_%s__plugins' % cls.__name__, {})
        return plugs.get(nstr(name))

    @classmethod
    def pluginNames(cls, enabled=True):
        """
        Returns the names of the plugins for a given class.
        
        :param      enabled     | <bool> || None
        
        :return     [<str>, ..]
        """
        return map(lambda x: x.name(), cls.plugins(enabled))

    @classmethod
    def pluginPath(cls):
        """
        Returns the plugin path for this class.
        
        :return     [<str>, ..]
        """
        return getattr(cls, '_%s__pluginpath' % cls.__name__, [])

    @classmethod
    def plugins(cls, enabled=True):
        """
        Returns the plugins for the given class.
        
        :param      enabled | <bool> || None
        
        :return     [<Plugin>, ..]
        """
        cls.loadPlugins()
        plugs = getattr(cls, '_%s__plugins' % cls.__name__, {}).values()
        if enabled is None:
            return plugs

        return filter(lambda x: x.isEnabled() == enabled, plugs)

    @classmethod
    def register(cls, plugin):
        """
        Registers the given plugin instance to this system.  If a plugin with
        the same name is already registered, then this plugin will not take
        effect.  The first registered plugin is the one that is used.
        
        :param      plugin | <Plugin>
        
        :return     <bool>
        """
        plugs = getattr(cls, '_%s__plugins' % cls.__name__, None)
        if plugs is None:
            cls.loadPlugins()

        plugs = getattr(cls, '_%s__plugins' % cls.__name__, {})

        if plugin.name() in plugs:
            inst = plugs[plugin.name()]

            # assign the plugin instance to the proxy
            if isinstance(inst, PluginProxy) and \
                    not isinstance(plugin, PluginProxy) and \
                    not inst._instance:
                inst._instance = plugin
                return True

            return False

        plugs[plugin.name()] = plugin
        setattr(cls, '_%s__plugins' % cls.__name__, plugs)
        return True

    @classmethod
    def setPluginRegisterType(cls, registerType):
        """
        Sets the registration type for this class.  By default, the Plugin
        class will register modules, however you can set it to register 
        packages or registration files as well.
        
        :param      registertype | <Plugin.RegisterType>
        """
        setattr(cls, '_%s__pluginRegisterType' % cls.__name__, registerType)

    @classmethod
    def setPluginPath(cls, pluginpath):
        """
        Sets the plugin path for this class to the given path.  The inputted
        pluginpath value can either be a list of strings, or a string
        containing paths separated by the OS specific path separator (':' on
        Mac & Linux, ';' on Windows)
        
        :param      pluginpath | [<str>, ..] || <str>
        """
        setattr(cls, '_%s__pluginpath' % cls.__name__, None)
        cls.addPluginPath(pluginpath)

    @classmethod
    def unregister(cls, plugin):
        """
        Unregisters the given plugin from the system based on its name.
        
        :param      plugin | <Plugin>
        """
        plugs = getattr(cls, '_%s__plugins' % cls.__name__, {})
        try:
            plugs.pop(plugin.name())
        except AttributeError:
            pass
        except ValueError:
            pass


# ------------------------------------------------------------------------------

class PluginProxy(Plugin):
    """
    Defines a proxy class that will be used when loading a plugin from a
    registry file.
    """

    def __init__(self, cls, name, version=1.0):
        super(PluginProxy, self).__init__(name, version)

        # clear the loading information
        self._proxyClass = cls
        self._instance = None
        self._loaded = False

        # define proxy information
        self._importPath = ''

    def loadInstance(self):
        """
        Loads the plugin from the proxy information that was created from the
        registry file.
        """
        if self._loaded:
            return

        self._loaded = True
        module_path = self.modulePath()

        package = projex.packageFromPath(module_path)
        path = os.path.normpath(projex.packageRootPath(module_path))

        if path in sys.path:
            sys.path.remove(path)

        sys.path.insert(0, path)

        try:
            __import__(package)

        except Exception, e:
            err = Plugin(self.name(), self.version())
            err.setError(e)
            err.setFilepath(module_path)

            self._instance = err

            self.setError(e)

            msg = "%s.plugin('%s') errored loading instance from %s"
            opts = (self.proxyClass().__name__, self.name(), module_path)
            logger.warning(msg % opts)
            logger.error(e)

    def importPath(self):
        """
        Returns the import path for the registry module for this plugin.
        
        :return     <str>
        """
        return self._importPath

    def instance(self):
        """
        Retrieves the instance for this plugin proxy object.  If the instance
        is not defined yet, then it will be loaded based on the proxy's loaded
        information.
        
        :return     <Plugin> || None
        """
        self.loadInstance()

        return self._instance

    def proxyClass(self):
        """
        Returns the proxy class that this proxy represents.
        
        :return     <subclass of Plugin>
        """
        return self._proxyClass

    def modulePath(self):
        """
        Returns the module path information for this proxy plugin.  This path
        will represent the root module that will be imported when the instance
        is first created of this plugin.
        
        :return     <str>
        """
        base_path = os.path.dirname(self.filepath())
        module_path = self.importPath()

        module_path = os.path.expanduser(os.path.expandvars(module_path))
        if module_path.startswith('.'):
            module_path = os.path.abspath(os.path.join(base_path, module_path))

        return module_path

    def setImportPath(self, path):
        """
        Sets the import path for the registry module for this plugin.
        
        :param      path | <str>
        """
        self._importPath = path

    @staticmethod
    def fromFile(cls, filepath):
        """
        Creates a proxy instance from the inputted registry file.
        
        :param      filepath | <str>
        
        :return     <PluginProxy> || None
        """
        xdata = ElementTree.parse(nstr(filepath))
        xroot = xdata.getroot()

        # collect variable information
        name = xroot.get('name')
        ver = float(xroot.get('version', '1.0'))

        if not name:
            name = os.path.basename(filepath).split('.')
            if name == '__init__':
                name = os.path.normpath(filepath).split(os.path.sep)[-2]
            name = projex.text.pretty(name)

        icon = xroot.get('icon', './icon.png')

        ximport = xroot.find('import')
        if ximport is not None:
            importpath = ximport.get('path', './__init__.py')
        else:
            importpath = './__init__.py'

        params = {'description': '', 'author': '', 'email': '', 'url': ''}
        for param, default in params.items():
            xdata = xroot.find(param)
            if xdata is not None:
                params[param] = xdata.text

        # generate the proxy information
        proxy = PluginProxy(cls, name, ver)
        proxy.setImportPath(importpath)
        proxy.setDescription(params['description'])
        proxy.setAuthor(params['author'])
        proxy.setEmail(params['email'])
        proxy.setUrl(params['url'])
        proxy.setFilepath(filepath)

        return proxy