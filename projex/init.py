"""
This is the core Python package for all of the projex software
projects.  At the bare minimum, this package will be required, and 
depending on which software you are interested in, other packages 
will be required and updated.
"""

__IMPORTED = set()

import importlib
import logging
import os
import traceback
import sys

from .text import nativestring as nstr

# initialize the main projex logger class
logger = logging.getLogger(__name__)

WEBSITES = {
    'home': 'http://projexsoftware.github.io',
    'docs': 'http://projexsoftware.github.io',
    'blog': 'http://projexsoftware.github.io/blog',
    'dev': 'http://github.com/projexsoftware'
}

SUBCONTEXT_MAP = {
    ('home', 'Product'): '%(base_url)s/products/%(app)s',
    ('docs', 'UserGuide'): '%(base_url)s/userguide/%(app)s',
    ('docs', 'APIReference'): 'http://github.com/projexsoftware',
    ('dev', 'Project'): '%(base_url)s/projects/%(app)s',
    ('dev', 'NewIssue'): '%(base_url)s/projects/%(app)s/issues/new?tracker_id=1',
    ('dev', 'NewFeature'): '%(base_url)s/projects/%(app)s/issues/new?tracker_id=2',
}


class attrdict(object):
    def __init__(self, data):
        self.__dict__.update(data)


# ------------------------------------------------------------------------------

def environ():
    """
    Returns the current environment that is being used.
    
    :return     <projex.envmanager.EnvManager> || None
    """
    from projex.envmanager import EnvManager

    return EnvManager.current()


def findmodules(path, recurse=False):
    """
    Looks up the modules for the given path and returns a list of the
    packages.  If the recurse flag is set to True, then it will look
    through the package recursively.
    
    :param      path    | <str>
                recurse | <bool>
    
    :return     ([<str>, ..] modules, [<str>, ..] paths)
    """
    output = set()
    roots = set()
    for root, folders, files in os.walk(path):
        # add packages
        for folder in folders:
            pkgpath = os.path.join(root, folder, '__init__.py')
            if os.path.exists(pkgpath):
                output.add(packageFromPath(pkgpath))

        # add modules
        rootpth = packageRootPath(root)
        rootpkg = packageFromPath(root)
        roots.add(rootpth)
        for file_ in files:
            name, ext = os.path.splitext(file_)
            if ext not in ('.py', '.pyo', '.pyc'):
                continue

            if name in ('__init__', '__plugins__'):
                continue

            if rootpkg:
                output.add(rootpkg + '.' + name)
            else:
                output.add(name)

        if not recurse:
            break

    return list(output), list(roots)


def importfile(filename):
    """
    Imports a module specifically from a file.
    
    :param      filename | <str>
    
    :return     <module> || None
    """
    pkg = packageFromPath(filename, includeModule=True)
    root = packageRootPath(filename)

    if root not in sys.path:
        sys.path.insert(0, root)

    __import__(pkg)
    return sys.modules[pkg]


def importmodules(package_or_toc, ignore=None, recurse=False, silent=None):
    """
    Imports all the sub-modules of a package, a useful technique for developing
    plugins.  By default, this method will walk the directory structure looking
    for submodules and packages.  You can also specify a __toc__ attribute
    on the package to define the sub-modules that you want to import.
    
    :param      package_or_toc  | <package> || <str> filename
                ignore          | [<str>, ..] || None
                recurse         | <bool>
                silent          | <bool>
    
    :usage      |>>> import projex
                |>>> import projex.docgen
                |>>> projex.importmodules(projex.docgen)
                |[<projex.docgen.commands>, <projex.docgen.default_config>, ..]
    
    :return     [<module> || <package>, ..]
    """
    if package_or_toc in __IMPORTED:
        return

    __IMPORTED.add(package_or_toc)

    if silent is None:
        silent = os.environ.get('PROJEX_LOG_IMPORTS', 'False').lower() != 'true'

    toc = []
    output = []
    if ignore is None:
        ignore = []

    # import from a set toc file
    if type(package_or_toc) in (str, unicode):
        # import a toc file
        if os.path.isfile(package_or_toc):
            f = open(package_or_toc, 'r')
            toc = f.readlines()
            f.close()

        # import from a directory
        elif os.path.isdir(package_or_toc):
            toc, paths = findmodules(package_or_toc, recurse=recurse)
            for path in paths:
                if path in sys.path:
                    sys.path.remove(path)

                sys.path.insert(0, path)

        # import a module by string
        else:
            use_sub_modules = False
            if package_or_toc.endswith('.*'):
                use_sub_modules = True
                package_or_toc = package_or_toc[:-2]

            try:
                __import__(package_or_toc)
                module = sys.modules[package_or_toc]
            except ImportError as err:
                if not silent:
                    logger.error('Unable to import module: %s', package_or_toc)
                    logger.debug(traceback.print_exc())
                return []
            except KeyError:
                if not silent:
                    logger.error('Unable to find module: %s', package_or_toc)
                return []

            if use_sub_modules:
                base = os.path.dirname(module.__file__)
                for path in os.listdir(base):
                    if path.endswith('.py') and path != '__init__.py':
                        importmodules(package_or_toc + '.' + path.replace('.py', ''))
                    elif os.path.isdir(os.path.join(base, path)):
                        importmodules(package_or_toc + '.' + path)
            else:
                return importmodules(module)

    # import from a given package
    else:
        toc = getattr(package_or_toc, '__toc__', [])

        if not toc:
            toc = []
            recurse = getattr(package_or_toc, '__recurse__', False)
            try:
                paths = package_or_toc.__path__
            except AttributeError:
                try:
                    paths = [os.path.dirname(package_or_toc.__file__)]
                except AttributeError:
                    paths = []

            for path in paths:
                data = findmodules(path, recurse=recurse)
                toc += data[0]
                for sub_path in data[1]:
                    if sub_path in sys.path:
                        sys.path.remove(sub_path)

                    sys.path.insert(0, sub_path)

            setattr(package_or_toc, '__toc__', toc)

    # import using standard means (successful for when dealing with 
    for modname in sorted(toc):
        # check against a callable ignore method
        if callable(ignore) and ignore(modname):
            continue

        elif type(modname) in (list, tuple) and modname not in ignore:
            continue

        # ignore preset options
        if modname.endswith('__init__'):
            continue
        elif modname.endswith('__plugins__'):
            continue

        try:
            output.append(sys.modules[modname])
            continue
        except KeyError:
            pass

        if not silent:
            logger.debug('Importing: %s' % modname)
        try:
            mod = importlib.import_module(modname)
            sys.modules[modname] = mod
            output.append(mod)
        except ImportError, err:
            if not silent:
                logger.error('Error importing module: %s', modname)
                logger.debug(traceback.print_exc())

    return output


def importobject(module_name, object_name):
    """
    Imports the object with the given name from the inputted module.
    
    :param      module_name | <str>
                object_name | <str>
    
    :usage      |>>> import projex
                |>>> modname = 'projex.envmanager'
                |>>> attr = 'EnvManager'
                |>>> EnvManager = projex.importobject(modname, attr)
    
    :return     <object> || None
    """
    if module_name not in sys.modules:
        try:
            __import__(module_name)
        except ImportError:
            logger.debug(traceback.print_exc())
            logger.error('Could not import module: %s', module_name)
            return None

    module = sys.modules.get(module_name)
    if not module:
        logger.warning('No module %s found.' % module_name)
        return None

    if not hasattr(module, object_name):
        logger.warning('No object %s in %s.' % (object_name, module_name))
        return None

    return getattr(module, object_name)


def packageRootPath(path):
    """
    Returns the root file path that defines a Python package from the inputted
    path.
    
    :param      path | <str>
    
    :return     <str>
    """
    path = nstr(path)
    if os.path.isfile(path):
        path = os.path.dirname(path)

    parts = os.path.normpath(path).split(os.path.sep)
    package_parts = []

    for i in range(len(parts), 0, -1):
        filename = os.path.sep.join(parts[:i] + ['__init__.py'])

        if not os.path.isfile(filename):
            break

        package_parts.insert(0, parts[i - 1])

    if not package_parts:
        return path
    return os.path.abspath(os.path.sep.join(parts[:-len(package_parts)]))


def packageFromPath(path, includeModule=False):
    """
    Determines the python package path based on the inputted path.
    
    :param      path | <str>
    
    :return     <str>
    """
    path = nstr(path)
    module = ''
    if os.path.isfile(path):
        path, fname = os.path.split(path)
        if fname.endswith('.py') and fname != '__init__.py':
            module = fname.split('.')[0]

    parts = os.path.normpath(path).split(os.path.sep)
    package_parts = []

    for i in range(len(parts), 0, -1):
        filename = os.path.sep.join(parts[:i] + ['__init__.py'])

        if not os.path.isfile(filename):
            break

        package_parts.insert(0, parts[i - 1])

    if includeModule and module:
        package_parts.append(module)

    return '.'.join(package_parts)


def refactor(module, name, repl):
    """
    Convenience method for the EnvManager.refactor 
    """
    environ().refactor(module, name, repl)


def requires(*modules):
    """
    Convenience method to the EnvManager.current().requires method.
    
    :param      *modules    | (<str>, .. )
    """
    environ().requires(*modules)


def website(app=None, mode='home', subcontext='UserGuide'):
    """
    Returns the website location for projex software.
    
    :param      app  | <str> || None
                mode | <str> (home, docs, blog, dev)
    
    :return     <str>
    """
    base_url = WEBSITES.get(mode, '')

    if app and base_url:
        opts = {'app': app, 'base_url': base_url}
        base_url = SUBCONTEXT_MAP.get((mode, subcontext), base_url)
        base_url %= opts

    return base_url