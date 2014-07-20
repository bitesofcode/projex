""" Defines an addon mixin for classes """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

import projex
from projex import errors

class AddonManager(object):
    @classmethod
    def _initAddons(cls, recurse=True):
        """
        Initializes the addons for this manager.
        """
        for addon_module in cls.addonModules(recurse):
            projex.importmodules(addon_module)
    
    @classmethod
    def addons(cls, recurse=True):
        """
        Returns a dictionary containing all the available addons
        for this mixin class.  If the optional recurse flag is set to True,
        then all the base classes will be searched for the given addon as well.
        
        :param      recurse | <bool>
        
        :return     {<str> name: <variant> addon, ..}
        """
        cls.initAddons()
        prop = '_{0}__addons'.format(cls.__name__)
        out = {}
        
        # lookup base classes
        if recurse:
            for base in cls.__bases__:
                if issubclass(base, AddonManager):
                    out.update(base.addons(recurse))
        
        # always use the highest level for any given key
        out.update(getattr(cls, prop, {}))
        return out

    @classmethod
    def addonModules(cls, recurse=True):
        """
        Returns all the modules that this addon class uses to load plugins
        from.
        
        :param      recurse | <bool>
        
        :return     [<str> || <module>, ..]
        """
        prop = '_{0}__addon_modules'.format(cls.__name__)
        out = set()
        
        # lookup base classes
        if recurse:
            for base in cls.__bases__:
                if issubclass(base, AddonManager):
                    out.update(base.addonModules(recurse))
        
        # always use the highest level for any given key
        out.update(getattr(cls, prop, set()))
        return out

    @classmethod
    def byName(cls, name, recurse=True):
        """
        Returns the addon whose name matches the inputed name.  If
        the optional recurse flag is set to True, then all the base classes
        will be searched for the given addon as well.
        
        :param      name | <str>
        """
        cls.initAddons()
        prop = '_{0}__addons'.format(cls.__name__)
        try:
            return getattr(cls, prop, {})[name]
        except KeyError:
            if recurse:
                for base in cls.__bases__:
                    if issubclass(base, AddonManager):
                        return base.byName(name, recurse)
        return None

    @classmethod
    def initAddons(cls, recurse=True):
        """
        Loads different addon modules for this class.  This method
        should not be overloaded in a subclass as it also manages the loaded
        state to avoid duplicate loads.  Instead, you can re-implement the
        _initAddons method for custom loading.
        
        :param      recurse | <bool>
        """
        key = '_{0}__addons_loaded'.format(cls.__name__)
        if getattr(cls, key, False):
            return
        
        cls._initAddons(recurse)
        setattr(cls, key, True)

    @classmethod
    def registerAddon(cls, name, addon, force=False):
        """
        Registers the inputed addon to the class.
        
        :param      name    | <str>
                    addon   | <variant>
        """
        prop = '_{0}__addons'.format(cls.__name__)
        cmds = getattr(cls, prop, {})
        
        if name in cmds and not force:
            raise errors.AddonAlreadyExists(cls, name, addon)
        
        cmds[name] = addon
        setattr(cls, prop, cmds)

    @classmethod
    def registerAddonModule(cls, module):
        """
        Registers a module to use to import addon subclasses from.
        
        :param      module | <str> || <module>
        """
        prop = '_{0}__addon_modules'.format(cls.__name__)
        mods = getattr(cls, prop, set())
        mods.add(module)
        setattr(cls, prop, mods)

    @classmethod
    def unregisterAddon(cls, name):
        """
        Unregisters the addon defined by the given name from the class.
        
        :param      name    | <str>
        """
        prop = '_{0}__addons'.format(cls.__name__)
        cmds = getattr(cls, prop, {})
        cmds.pop(name, None)

    @classmethod
    def unregisterAddonModule(cls, module):
        """
        Unregisters the module to use to import addon subclasses from.
        
        :param      module | <str> || <module>
        """
        prop = '_{0}__addon_modules'.format(cls.__name__)
        mods = getattr(cls, prop, set())
        try:
            mods.remove(module)
        except KeyError:
            pass

