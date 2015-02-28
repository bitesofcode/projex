""" 
Defines helper methods for the PyInstaller utility
"""

import os
import projex
import sys


def collect(basepath, exclude=None, processPlugins=True):
    """
    Collects all the packages associated with the inputted filepath.
    
    :param      module | <module>
    
    :return     ([<str> pkg, ..], [(<str> path, <str> relpath), ..] data)
    """
    if exclude is None:
        exclude = ['.py', '.pyc', '.pyo', '.css', '.exe']

    imports = []
    datas = []

    # walk the folder structure looking for all packages and data files
    basename = os.path.basename(basepath)
    basepath = os.path.abspath(basepath)
    baselen = len(basepath) - len(basename)

    plugfiles = []

    for root, folders, files in os.walk(basepath):
        if '.svn' in root or '.git' in root:
            continue

        # mark the plugins file for load
        plugdata = None
        if processPlugins and '__plugins__.py' in files:
            filename = os.path.join(root, '__plugins__.py')
            package = projex.packageFromPath(filename) + '.__plugins__'
            pkgpath = projex.packageRootPath(filename)

            if pkgpath not in sys.path:
                sys.path.insert(0, pkgpath)

            # import the plugins module
            __import__(package)
            pkg = sys.modules[package]

            recurse = getattr(pkg, '__recurse__', False)
            plugdata = {'recurse': recurse,
                        'packages': [],
                        'path': root}

            plugfiles.append(plugdata)

        # look for any recursion plugins
        else:
            for data in plugfiles:
                if data['recurse'] and root.startswith(data['path']):
                    plugdata = data
                    break

        if plugdata is not None:
            packages = plugdata['packages']

            # include package plugins
            for folder in folders:
                pkgpath = os.path.join(root, folder, '__init__.py')
                if os.path.exists(pkgpath):
                    packages.append(projex.packageFromPath(pkgpath))

        for file_ in files:
            module, ext = os.path.splitext(file_)

            # look for python modules
            if ext == '.py':
                package_path = projex.packageFromPath(os.path.join(root, file_))
                if not package_path:
                    continue

                if module != '__init__':
                    package_path += '.' + module

                imports.append(package_path)

                # test to see if this is a plugin file
                if plugdata is not None and module not in ('__init__',
                                                           '__plugins__'):
                    plugdata['packages'].append(package_path)

            # look for data
            elif ext not in exclude:
                src = os.path.join(root, file_)
                targ = os.path.join(root[baselen:])
                datas.append((src, targ))

    # save the plugin information
    for plugdata in plugfiles:
        fname = os.path.join(plugdata['path'], '__plugins__.py')
        packages = plugdata['packages']

        plugs = ',\n'.join(map(lambda x: "r'{0}'".format(x), packages))
        data = [
            '__recurse__ = {0}'.format(plugdata['recurse']),
            '__toc__ = [{0}]'.format(plugs)
        ]

        # write the data to the system
        f = open(fname, 'w')
        f.write('\n'.join(data))
        f.close()

    return imports, datas


