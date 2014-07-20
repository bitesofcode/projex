#!/usr/bin/python

"""
Defines the EnvManager class to handle manipulation of environment variables
and modules, as well as control dependency requirements.  The manager will be
accessed via the projex.env variable, and can be subclassed to control
the way the environments for your particular company should work.

The projex package will create its environment manager instance at import
time, so to assign your own custom environment manager, you will need to either
reassign the manager instance, or define:

PROJEX_PATH=/path/to/modules:/path/to/other/modules/

As an environment variable before import.  The variable would consist of the
path to the root package or module, and the import term to use.
"""

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

#------------------------------------------------------------------------------

import logging
import os
import re
import sys

logger = logging.getLogger(__name__)

class EnvManager(object):
    """ Class to manage different paths are requirements. """
    
    _current = None
    
    def __init__( self ):
        self._loadedRequires    = []
        self._issetup           = False
        self._origpath          = sys.path[:]  # duplicate the path
        self._addedpaths        = []
  
    def _setup( self ):
        """
        Sets up the global import environment variables by registering the
        sub-folders for projex as import locations.  When defining your 
        custom manager, you will want to overload this method to do any
        sort of global initialization that you wish before continuing.
        
        :warning    This method is called by the _setup method, and should 
                    not be called directly.
        """
        projex_path = os.getenv('PROJEX_PATH')
        if ( not projex_path ):
            return
        
        base_path   = os.path.dirname(__file__)
        
        logger.debug('Loading PROJEX_PATH: %s' % projex_path)
        
        # load the defaults from the install directory
        # load the paths from the environment
        paths = projex_path.split(os.path.pathsep)
        paths += [
            os.path.join(base_path, 'userplug'),
            os.path.join(base_path, 'stdplug'),
            os.path.join(base_path, 'lib'),
        ]
        
        sys.path = paths + sys.path
        
    def appendPath( self, path ):
        """
        Appends the inputed path to the end of the sys.path variable,
        provided the path does not already exist in it.
        
        :param      path
        :type       str
        
        :return     bool: success
        """
        # normalize the path
        path = os.path.normcase(str(path)).strip()
        if ( path and path != '.' and not path in sys.path ):
            sys.path.append(path)
            self._addedpaths.append(path)
            return True
        return False
        
    def expandvars( self, text, environ = None, cache = None ):
        """
            Recursively expands the text variables, vs. the os.path \
            method which only works at one level.  The cache value should be \
            left blank as it is used to protect against recursion.
            
            :param      text    | <str>
                        environ | <dict> || None
                        cache   | <dict> { <str>: <str>, .. }
                        
            :return     <str>
        """
        if ( not environ ):
            environ = os.environ
        
        # make sure we have data
        if ( not text ):
            return ''
        
        # check for circular dependencies
        if ( cache == None ):
            cache = {}
        
        # return the cleaned variable
        output  = str(text)
        keys    = re.findall( '\$(\w+)|\${(\w+)\}|\%(\w+)\%', text )
        
        for first, second, third in keys:
            repl    = ''
            key     = ''
            if ( first ):
                repl = '$%s' % first
                key = first
            elif ( second ):
                repl = '${%s}' % second
                key = second
            elif ( third ):
                repl = '%%%s%%' % third
                key = third
            else:
                continue
            
            value = environ.get(key)
            if ( value ):
                if ( not key in cache ):
                    cache[key]  = value
                    value       = self.expandvars(value, environ, cache)
                else:
                    err = '%s environ variable causes an infinite loop.' % key
                    logger.warning(err)
                    value = cache[key]
            else:
                value = repl
            
            output = output.replace( repl, value )
            
        return os.path.expanduser(output)
        
    def pushPath( self, path ):
        """
        Pushes the inputed path at the front of the sys.path variable, making
        it the first path python uses when importing a module.
        
        :param      path
        :type       str
        
        :return     bool: success
        """
        # normalize the path
        path = os.path.normcase(str(path)).strip()
        if ( path and path != '.' and not path in sys.path ):
            sys.path.append(path)
            self._addedpaths.insert(0, path)
            return True
        return False
    
    def requires( self, *modules ):
        """
        Registers the system paths for the inputed modules so that they can
        be imported properly.  By default, this will check to see if the
        key PROJEX_[MODULE]_PATH exists in the environment, and if so, insert
        that path to the front of the sys.path for import.  Out of the box
        installations will register import paths to default projex folders
        and won't need to define these path variables. (lib/,stdplug/,userplug)
        
        :param      *modules     ( <str>, .. )
        
        :usage      |>>> import projex
                    |>>> projex.logger.setLevel( projex.logging.DEBUG )
                    |>>> projex.environ().requires( 'orb', 'anansi' )
                    |DEBUG: EnvManager.requires: PROJEX_ORB_PATH
                    |DEBUG: EnvManager.requires: PROJEX_ANANSI_PATH
                    |>>> import opb
                    |>>> import openwebdk
        """
        self._setup()
        
        for module in modules:
            if ( '-' in module ):
                parts   = module.split('-')
                module  = parts[0]
                version = '-'.join(parts)
            else:
                version = ''
            
            if ( module in self._loadedRequires ):
                continue
            
            self._loadedRequires.append(module)
            path_key = 'PROJEX_%s_PATH' % str(module).upper()
            env_path = os.getenv(path_key)
            
            logger.debug( 'Looking up %s: %s' % (path_key, env_path) )
            
            # push the path for the particular module if found in the env
            if ( env_path ):
                self.pushPath(env_path)
    
    def refactor( self, module, name, repl ):
        """
        Replaces the name in the module dictionary with the inputed replace \
        value.
        
        :param      module  | <str> || <module>
                    name    | <str>
                    repl    | <variant>
        
        :return     <bool>
        """
        name = str(name)
        
        # import a module when refactoring based on a string
        if ( isinstance(module, basestring) ):
            try:
                module = __import__(module)
            except ImportError:
                logger.exception('Could not import module: %s' % module)
                return False
        
        try:
            glbls = module.__dict__
        except AttributeError:
            err = '%s cannot support refactoring.' % module.__name__
            logger.exception(err)
            return False
        
        if ( name in glbls ):
            # refactor the value
            glbls[name] = repl
            
            return True
        else:
            err = '%s is not a member of %s.' % (name, module.__name__)
            logger.warning(err)
            return False
    
    def setCurrent( self ):
        """
        Sets the current instance of this EnvManager class as the global
        current manager.
        """
        EnvManager._current = self
    
    def setup( self ):
        """
        Initializes the global path variables for the first time if it
        has not already been done.
        
        :sa     [[#_setup]]
        """
        if ( self._issetup ):
            return
        
        self.setup()
        self._issetup = True
    
    @staticmethod
    def current():
        """
        Returns the current environment manager for the projex system.
        
        :return     <EnvManager>
        """
        if ( not EnvManager._current ):
            path    = os.environ.get('PROJEX_ENVMGR_PATH')
            module  = os.environ.get('PROJEX_ENVMGR_MODULE')
            clsname = os.environ.get('PROJEX_ENVMGR_CLASS')
            cls     = EnvManager
            
            if ( module and clsname ):
                # check if the user specified an import path
                if ( path ):
                    logger.info('Adding env manager path: %s' % path)
                    sys.path.insert(0, path)
                
                logger.info('Loading env manager: %s.%s' % (module, clsname))
                
                try:
                    __import__(module)
                    mod = sys.modules[module]
                    cls = getattr(mod, clsname)
                
                except ImportError:
                    logger.error('Could not import env manager %s', module)
                
                except KeyError:
                    logger.error('Could not import env manager %s', module)
                
                except AttributeError:
                    msg = '%s is not a valid class of %s' % (clsname, module)
                    logger.error(msg)
            
            EnvManager._current = cls()
        return EnvManager._current
    
    @staticmethod
    def fileImport( filepath, ignore = None ):
        """
        Imports the module located at the given filepath.
        
        :param      filepath    | <str>
                    ignore      | [<str>, ..] || None
        
        :return     <module> || None
        """
        basepath, package = EnvManager.packageSplit( filepath )
        if ( not (basepath and package) ):
            return None
        
        # make sure this is not part of the ignored package list
        if ( ignore and package in ignore ):
            return None
        
        basepath = os.path.normcase(basepath)
        if ( not basepath in sys.path ):
            sys.path.insert(0, basepath)
        
        logger.debug('Importing: %s' % package)
        
        try:
            __import__(package)
            module = sys.modules[package]
        except ImportError:
            logger.exception('ImportError: %s' % package)
            return None
        except KeyError:
            logger.exception('Could not find sys.modules package:' % package)
            return None
        except Exception:
            logger.exception('Unknown error occurred not import %s' % package)
            return None
        
        return module
            
    @staticmethod
    def packageSplit( filepath ):
        """ 
        Determines the python path, and package information for the inputed
        filepath.
        
        :param      filepath  |  <str>
        
        :return     (<str> path, <str> package)
        """
        filepath = str(filepath).strip().strip('.')
        if ( not filepath ):
            return ('', '')
        
        basepath, module = os.path.split(str(filepath))
        module       = os.path.splitext(module)[0]
        pathsplit    = os.path.normpath(basepath).split( os.path.sep )
        packagesplit = []
        
        if ( module and module != '__init__' ):
            packagesplit.append(module)
        
        testpath = os.path.sep.join( pathsplit + [ '__init__.py' ] )
        while ( os.path.exists( testpath ) ):
            packagesplit.insert(0, pathsplit[-1])
            pathsplit = pathsplit[:-1]
            testpath = os.path.sep.join( pathsplit + [ '__init__.py' ] )
        
        return (os.path.sep.join(pathsplit), '.'.join(packagesplit))
