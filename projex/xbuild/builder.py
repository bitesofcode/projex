""" 
Defines the builder class for building versions.
"""

import logging
import os
import projex
import projex.resources
import projex.pyi
import re
import shutil
import subprocess
import sys
import time
import zipfile

from xml.etree import ElementTree
from projex.enum import enum
from projex.xbuild import templ
from projex.xbuild import errors
from projex.text import nativestring as nstr

try:
    import yaml
except ImportError:
    yaml = None

log = logging.getLogger(__name__)

wrap_str = lambda x: map(lambda y: "r'{0}'".format(y.replace('\\', '/')), x)

os.environ.setdefault('PYTHON', 'python')
os.environ.setdefault('PYINSTALLER', '/pyinstaller/pyinstaller.py')
os.environ.setdefault('NSIS_EXE', 'makensis.exe')
os.environ.setdefault('SIGNTOOL', 'signtool')


def cmdexec(cmd):
    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True)

    result = proc.poll()
    while result is None:
        info, err = proc.communicate()

        if info:
            log.info(info)
        if err:
            log.error(err)

        result = proc.poll()

    return result


def _mkpath(filepath, text, **opts):
    path = text.format(**opts)
    path = os.path.expandvars(path)
    path = os.path.join(filepath, path)
    return os.path.abspath(path)


class Builder(object):
    Options = enum('GenerateRevision',
                   'GenerateDocs',
                   'GenerateExecutable',
                   'GenerateInstaller',
                   'GenerateSetupFile',
                   'GenerateEgg',
                   'GenerateZipFile',
                   'Signed', )

    _plugins = {}

    def __init__(self):
        # set general information
        self._name = ''
        self._version = ''
        self._revision = ''
        self._license = ''
        self._environment = {}
        self._options = Builder.Options.all()
        self._ignoreFileTypes = ['.pyc', '.pyo']
        self._language = 'English'

        # set meta information
        self._company = ''
        self._companyUrl = ''
        self._author = ''
        self._authorEmail = ''
        self._certificate = ''
        self._signcmd = '$SIGNTOOL sign /v /a /f "{cert}" "{filename}"'

        # set build paths
        self._distributionPath = ''
        self._sourcePath = ''
        self._outputPath = ''
        self._buildPath = ''
        self._licenseFile = ''

        # set executable options
        opts = {
            'excludeBinaries': 1,
            'debug': False,
            'console': False,
            'strip': None,
            'logo': projex.resources.find('img/logo.ico'),
            'upx': True,
            'onefile': False,
            'cmd': '$PYTHON -O $PYINSTALLER "{spec}"'
        }

        self._runtime = ''
        self._resourcePath = ''
        self._specfile = ''
        self._hookPaths = []
        self._hiddenImports = []
        self._executableData = []
        self._executableExcludes = []
        self._executableName = ''
        self._executableCliName = ''
        self._executablePath = ''
        self._productName = ''
        self._executableOptions = opts

        # set installation options
        opts = {
            'logo': projex.resources.find('img/logo.ico'),
            'header_image': projex.resources.find('img/installer.bmp'),
            'finish_image': projex.resources.find('img/installer-side.bmp'),
        }

        for k, v in opts.items():
            opts[k] = os.path.abspath(v)

        opts['cmd'] = r'$NSIS_EXE "{script}"'
        opts['require_license_approval'] = False
        opts['choose_dir'] = True

        self._installName = ''
        self._installPath = ''
        self._installerOptions = opts
        self._installDirectories = {}

        # set documentation options
        self._doxfile = ''

        # set revision options
        self._revisionFilename = '__revision__.py'

        # set setuptools options
        self._distributionName = ''
        self._keywords = ''
        self._brief = ''
        self._description = ''
        self._dependencies = []
        self._classifiers = []

    def author(self):
        """
        Returns the author associated with this builder.
        
        :return     <str>
        """
        return self._author

    def authorEmail(self):
        """
        Returns the author email associated with this builder.
        
        :return     <str>
        """
        return self._authorEmail

    def brief(self):
        """
        Returns the brief associated with this builder.
        
        :return     <str>
        """
        return self._brief

    def build(self):
        """
        Builds this object into the desired output information.
        """
        signed = bool(self.options() & Builder.Options.Signed)

        # remove previous build information
        buildpath = self.buildPath()
        if not buildpath:
            raise errors.InvalidBuildPath(buildpath)

        # setup the environment
        for key, value in self.environment().items():
            log.info('SET {0}={1}'.format(key, value))
            os.environ[key] = value

        if os.path.exists(buildpath):
            shutil.rmtree(buildpath)

        # generate the build path for the installer
        os.makedirs(buildpath)

        # create the output path
        outpath = self.outputPath()
        if not os.path.exists(outpath):
            os.makedirs(outpath)

        # copy license information
        src = self.licenseFile()
        if src and os.path.exists(src):
            targ = os.path.join(buildpath, 'license.txt')
            shutil.copyfile(src, targ)

        # generate revision information
        if self.options() & Builder.Options.GenerateRevision:
            self.generateRevision()

        # generate documentation information
        if self.options() & Builder.Options.GenerateDocs:
            self.generateDocumentation(buildpath)

        # generate setup file
        if self.options() & Builder.Options.GenerateSetupFile:
            setuppath = os.path.join(self.sourcePath(), '..')
            egg = (self.options() & Builder.Options.GenerateEgg) != 0
            self.generateSetupFile(setuppath, egg=egg)

        # generate executable information
        if self.options() & Builder.Options.GenerateExecutable:
            if not self.generateExecutable(signed=signed):
                return

        # generate zipfile information
        if self.options() & Builder.Options.GenerateZipFile:
            self.generateZipFile(self.outputPath())

        # generate installer information
        if self.options() & Builder.Options.GenerateInstaller:
            self.generateInstaller(buildpath, signed=signed)

    def buildPath(self):
        """
        Returns the root path for building this instance.
        
        :return     <str>
        """
        return self._buildPath

    def classifiers(self):
        """
        Returns the classifiers associated with this builder.
        
        :return     [<str>, ..]
        """
        return self._classifiers

    def certificate(self):
        """
        Returns the signing certificate file for this builder.
        
        :return     <str>
        """
        return self._certificate

    def company(self):
        """
        Returns the company associated with this builder.
        
        :return     <str>
        """
        return self._company

    def companyUrl(self):
        """
        Returns the company url associated with this builder.
        
        :return     <str>
        """
        return self._companyUrl

    def dependencies(self):
        """
        Returns the dependencies associated with this builder.
        
        :return     [<str>, ..]
        """
        return self._dependencies

    def description(self):
        """
        Returns the description associated with this builder.
        
        :return     <str>
        """
        return self._description

    def distributionName(self):
        """
        Returns the name to be used in the setup distribution within
        python's setup tools for this builder.
        
        :return     <str>
        """
        if self._distributionName:
            return self._distributionName
        else:
            return self.name()

    def distributionPath(self):
        """
        Returns the name to be used in the setup distribution within
        python's setup tools for this builder.
        
        :return     <str>
        """
        return self._distributionPath

    def doxfile(self):
        """
        Returns the dox file for this builder.
        
        :return     <str>
        """
        return self._doxfile

    def environment(self):
        """
        Returns the environment variables for this builder.
        
        :return     {<str> key: <str> value, ..}
        """
        return self._environment

    def executableExcludes(self):
        """
        Returns the exclude packages for this executable.
        
        :return     [<str>, ..]
        """
        return self._executableExcludes

    def executableData(self):
        """
        Returns a list of the executable data that will be collected for this
        pyinstaller.
        
        :return     [(<str> type, {<str> option: <str> value})]
        """
        return self._executableData

    def productName(self):
        """
        Returns the folder for the executable this builder will generate.
        
        :return     <str>
        """
        if self._productName:
            return self._productName
        else:
            return self.name()

    def executableName(self):
        """
        Returns the name for the executable this builder will generate.
        
        :return     <str>
        """
        if self._executableName:
            return self._executableName
        else:
            return self.name()

    def executableCliName(self):
        """
        Returns the name for the executable this builder will generate.
        
        :return     <str>
        """
        return self._executableCliName

    def executablePath(self):
        """
        Returns the default executable path for this builder.
        
        :return     <str>
        """
        return self._executablePath

    def executableOption(self, key, default=''):
        """
        Returns the executable option for given key to the inptued value.
        
        :param      key | <str>
                    default | <variant>
        """
        return self._executableOptions.get(key, default)

    def keywords(self):
        """
        Returns the keywords associated with this builder.
        
        :return     <str>
        """
        return self._keywords

    # noinspection PyMethodMayBeStatic
    def generatePlugins(self, basepath):
        for root, folders, files in os.walk(basepath):
            plugs = []

            if '__plugins__.py' not in files:
                continue

            modfiles = filter(lambda x: x.endswith('.py'), files)
            modfiles = map(lambda x: x.replace('.py', ''), modfiles)

            pkg = projex.packageFromPath(root)
            modules = filter(lambda x: x not in ('__init__', '__plugins__'), modfiles)
            packages = filter(lambda x: '{0}/{1}/__init__.py'.format(root, x),
                              folders)

            names = modules + packages

            if pkg:
                toc = ["'{0}.{1}'".format(pkg, name) for name in names]
            else:
                toc = ["'{0}'".format(name) for name in names]

            # generate the table of contents
            toc.sort()
            text = '__toc__ = [{0}]'.format(',\n'.join(toc).strip())
            f = open(os.path.join(root, '__plugins__.py'), 'w')
            f.write(text)
            f.close()

    # noinspection PyMethodMayBeStatic
    def generateDocumentation(self, outpath='.'):
        """
        Generates the documentation for this builder in the output path.
        
        :param      outpath | <str>
        """
        pass

    def generateExecutable(self, outpath='.', signed=False):
        """
        Generates the executable for this builder in the output path.
        
        :param      outpath | <str>
        """
        if not (self.runtime() or self.specfile()):
            return True

        if not self.distributionPath():
            return True

        if os.path.exists(self.distributionPath()):
            shutil.rmtree(self.distributionPath())

        if os.path.isfile(self.sourcePath()):
            basepath = os.path.normpath(os.path.dirname(self.sourcePath()))
        else:
            basepath = os.path.normpath(self.sourcePath())

        # store the plugin table of contents
        self.generatePlugins(basepath)

        # generate the specfile if necessary
        specfile = self.specfile()
        # generate the spec file options
        opts = {
            'name': self.name(),
            'exname': self.executableName(),
            'product': self.productName(),
            'runtime': self.runtime(),
            'srcpath': self.sourcePath(),
            'buildpath': self.buildPath(),
            'hookpaths': ',\n'.join(wrap_str(self.hookPaths())),
            'hiddenimports': ',\n'.join(wrap_str(self.hiddenImports())),
            'distpath': self.distributionPath(),
            'platform': sys.platform,
            'excludes': ',\n'.join(wrap_str(self.executableExcludes()))
        }

        if not specfile:
            datasets = []
            for typ, data in self.executableData():
                if typ == 'tree':
                    args = {
                        'path': data[0],
                        'prefix': data[1],
                        'excludes': ','.join(wrap_str(data[2]))
                    }

                    datasets.append(templ.SPECTREE.format(**args))

                else:
                    args = {}
                    args.update(data)
                    args.setdefault('type', typ)
                    datasets.append(templ.SPECDATA.format(**args))

            opts['datasets'] = '\n'.join(datasets)

            opts.update(self._executableOptions)

            if self.executableCliName():
                opts['cliname'] = self.executableCliName()
                opts['collect'] = templ.SPECFILE_CLI.format(**opts)
            else:
                opts['collect'] = templ.SPECFILE_COLLECT.format(**opts)

            if opts['onefile']:
                data = templ.SPECFILE_ONEFILE.format(**opts)
            else:
                data = templ.SPECFILE.format(**opts)

            # generate the spec file for building
            specfile = os.path.join(self.buildPath(), self.name() + '.spec')
            f = open(specfile, 'w')
            f.write(data)
            f.close()

        cmd = os.path.expandvars(self.executableOption('cmd'))
        success = cmdexec(cmd.format(spec=specfile)) == 0
        if signed:
            binfile = os.path.join(opts['distpath'],
                                   opts['product'],
                                   opts['exname'] + '.exe')
            self.sign(binfile)

        return success

    def generateRevision(self):
        """
        Generates the revision file for this builder.
        """
        revpath = self.sourcePath()
        if not os.path.exists(revpath):
            return

        # determine the revision location
        revfile = os.path.join(revpath, self.revisionFilename())
        mode = ''
        # test for svn revision
        try:
            args = ['svn', 'info', revpath]
            proc = subprocess.Popen(args, stdout=subprocess.PIPE)
            mode = 'svn'
        except WindowsError:
            try:
                args = ['git', 'rev-parse', 'HEAD', revpath]
                proc = subprocess.Popen(args, stdout=subprocess.PIPE)
                mode = 'git'
            except WindowsError:
                return

        # process SVN revision
        rev = None

        if mode == 'svn':
            for line in proc.stdout:
                data = re.match('^Revision: (\d+)', line)
                if data:
                    rev = int(data.group(1))
                    break

        if rev is not None:
            try:
                f = open(revfile, 'w')
                f.write('__revision__ = {0}\n'.format(rev))
                f.close()
            except IOError:
                pass

    # noinspection PyTypeChecker
    def generateInstaller(self, outpath='.', signed=False):
        """
        Generates the installer for this builder.
        
        :param      outpath | <str>
        """
        log.info('Generating Installer....')

        # generate the options for the installer
        opts = {
            'name': self.name(),
            'exname': self.executableName(),
            'version': self.version(),
            'company': self.company(),
            'language': self.language(),
            'license': self.license(),
            'platform': sys.platform,
            'product': self.productName(),
            'outpath': self.outputPath(),
            'instpath': self.installPath(),
            'instname': self.installName(),
            'buildpath': self.buildPath(),
            'srcpath': self.sourcePath(),
            'nsis_exe': os.environ['NSIS_EXE'],
            'signed': '',
            'signcmd': ''
        }

        basetempl = ''
        if self.runtime() and os.path.exists(self.distributionPath()):
            opts['compilepath'] = os.path.join(self.distributionPath(), self.executableName())
            basetempl = templ.NSISAPP

        elif os.path.isfile(self.sourcePath()):
            opts['compilepath'] = self.sourcePath()
            opts['install'] = templ.NSISMODULE.format(**opts)
            basetempl = templ.NSISLIB

        else:
            opts['compilepath'] = self.sourcePath()
            opts['install'] = templ.NSISPACKAGE.format(**opts)
            basetempl = templ.NSISLIB

        # sign the uninstaller
        if signed and self.signcmd():
            cmd = self.signcmd().format(filename='', cert=self.certificate())
            cmd = os.path.expandvars(cmd)
            cmd = cmd.replace('""', '')

            opts['signed'] = '!define SIGNED'
            opts['signcmd'] = cmd

        opts.update(self._installerOptions)

        # expand the plugin paths
        pre_section_plugins = []
        post_section_plugins = []
        install_plugins = []
        uninstall_plugins = []

        for filename in self.installerOption('pre_section_plugins', []):
            with open(filename, 'r') as f:
                pre_section_plugins.append(f.read().format(**opts))

        for filename in self.installerOption('post_section_plugins', []):
            with open(filename, 'r') as f:
                post_section_plugins.append(f.read().format(**opts))

        for filename in self.installerOption('install_section_plugins', []):
            with open(filename, 'r') as f:
                install_plugins.append(f.read().format(**opts))

        for filename in self.installerOption('uninstall_section_plugins', []):
            with open(filename, 'r') as f:
                uninstall_plugins.append(f.read().formst(**opts))

        opts['install_plugins'] = '\n'.join(install_plugins)
        opts['uninstall_plugins'] = '\n'.join(uninstall_plugins)
        opts['pre_section_plugins'] = '\n'.join(pre_section_plugins)
        opts['post_section_plugins'] = '\n'.join(post_section_plugins)
        opts['choose_directory'] = templ.NSISCHOOSEDIRECTORY if opts['choose_dir'] else ''

        req_license = self._installerOptions.pop('require_license_approval', False)
        if req_license:
            opts['require_license_approval'] = templ.NSISLICENSERADIO
        else:
            opts['require_license_approval'] = ''

        outfile = os.path.join(os.path.abspath(outpath), 'autogen.nsi')
        opts['__file__'] = outfile

        # update the additional directories
        addtl = []
        for directory, source in self._installDirectories.items():
            directory = os.path.expandvars(directory.format(**opts))
            directory = os.path.normpath(directory)

            if source:
                source = os.path.expandvars(source.format(**opts))
                source = os.path.abspath(source)

                addtl.append('    SetOutPath "{0}"'.format(directory))
                addtl.append('    File /nonfatal /r "{0}"'.format(source))
            else:
                addtl.append('    CreateDirectory "{0}"'.format(directory))

        opts['addtl_commands'] = '\n'.join(addtl)
        data = basetempl.format(**opts)

        # create the output file
        f = open(outfile, 'w')
        f.write(data)
        f.close()

        installerfile = os.path.join(self.outputPath(), self.installName())
        installerfile += '-{0}.exe'.format(sys.platform)

        # run the installer
        cmd = os.path.expandvars(self.installerOption('cmd'))
        success = cmdexec(cmd.format(script=outfile))

        # sign the installer
        if signed:
            self.sign(installerfile)

        log.info('Executing installer...')
        cmdexec(installerfile)

    def generateSetupFile(self, outpath='.', egg=False):
        """
        Generates the setup file for this builder.
        """
        outpath = os.path.abspath(outpath)
        outfile = os.path.join(outpath, 'setup.py')

        opts = {
            'name': self.name(),
            'distname': self.distributionName(),
            'version': self.version(),
            'author': self.author(),
            'author_email': self.authorEmail(),
            'keywords': self.keywords(),
            'license': self.license(),
            'brief': self.brief(),
            'description': self.description(),
            'url': self.companyUrl()
        }

        wrap_dict = lambda x: map(lambda k: "r'{0}': [{1}]".format(k[0],
                                                                   ',\n'.join(wrap_str(k[1]))),
                                  x.items())

        opts['dependencies'] = ',\n'.join(wrap_str(self.dependencies()))
        opts['classifiers'] = ',\n'.join(wrap_str(self.classifiers()))

        if os.path.isfile(self.sourcePath()):
            basepath = os.path.normpath(os.path.dirname(self.sourcePath()))
        else:
            basepath = os.path.normpath(self.sourcePath())

        self.generatePlugins(basepath)

        exts = set()
        for root, folders, files in os.walk(basepath):
            for file_ in files:
                _, ext = os.path.splitext(file_)
                if ext not in ('.py', '.pyc', '.pyo'):
                    exts.add('*' + ext)

        exts = list(exts)
        text = templ.SETUPFILE.format(**opts)

        # generate the file
        if not os.path.exists(outfile):
            f = open(outfile, 'w')
            f.write(text)
            f.close()

        # generate the manifest file
        manfile = os.path.join(outpath, 'MANIFEST.in')
        if not os.path.exists(manfile):
            f = open(manfile, 'w')
            f.write('include *.md *.txt *.ini *.cfg *.rst\n')
            f.write('recursive-include {0} {1}\n'.format(self.name(), ' '.join(exts)))
            f.close()

        # generate the egg
        if egg:
            cmd = 'cd {0} && $PYTHON setup.py bdist_egg'.format(outpath)
            cmd = os.path.expandvars(cmd)
            cmdexec(cmd)

    def generateZipFile(self, outpath='.'):
        """
        Generates the zip file for this builder.
        """
        fname = self.installName() + '.zip'
        outfile = os.path.abspath(os.path.join(outpath, fname))

        # clears out the exiting archive
        if os.path.exists(outfile):
            try:
                os.remove(outfile)
            except OSError:
                log.warning('Could not remove zipfile: %s', outfile)
                return False

        # generate the zip file
        zfile = zipfile.ZipFile(outfile, 'w')

        # zip up all relavent fields from the code base
        if os.path.isfile(self.sourcePath()):
            zfile.write(self.sourcePath(), os.path.basename(self.sourcePath()))
        else:
            basepath = os.path.abspath(os.path.join(self.sourcePath(), '..'))
            baselen = len(basepath) + 1
            for root, folders, filenames in os.walk(basepath):
                # ignore hidden folders
                if '.svn' in root or '.git' in root:
                    continue

                # ignore setuptools build info
                part = root[baselen:].split(os.path.sep)[0]
                if part in ('build', 'dist') or part.endswith('.egg-info'):
                    continue

                # include files
                for filename in filenames:
                    ext = os.path.splitext(filename)[1]
                    if ext in self.ignoreFileTypes():
                        continue

                    arcroot = root[baselen:].replace('\\', '/')
                    arcname = os.path.join(arcroot, filename)
                    log.info('Archiving %s...', arcname)
                    zfile.write(os.path.join(root, filename), arcname)

        zfile.close()
        return True

    def hiddenImports(self):
        """
        Returns a list of the hidden imports that are associated with this
        builder.  This is used with PyInstaller when generating a build.
        
        :return     [<str>, ..]
        """
        return self._hiddenImports

    def hookPaths(self):
        """
        Returns the path that contains additional hooks for this builder.
        This provides the root location that PyInstaller will use when
        generating installater information.
        
        :return     [<str>, ..]
        """
        return self._hookPaths

    def ignoreFileTypes(self):
        """
        Returns the file types to ignore for this builder.
        
        :return     [<str>, ..]
        """
        return self._ignoreFileTypes

    def installName(self):
        """
        Returns the name for the installer this builder will generate.
        
        :return     <str>
        """
        opts = {'name': self.name(), 'version': self.version()}
        if self.revision():
            opts['revision'] = '.{0}'.format(self.revision())
        else:
            opts['revision'] = ''

        if self._installName:
            return self._installName.format(**opts)
        else:
            return '{name}-{version}{revision}'.format(**opts)

    def installPath(self):
        """
        Returns the default installation path for this builder.
        
        :return     <str>
        """
        return self._installPath

    def installerOption(self, key, default=''):
        """
        Returns the installer option for given key to the inptued value.
        
        :param      key | <str>
                    default | <variant>
        """
        return self._installerOptions.get(key, default)

    def name(self):
        """
        Returns the name for this builder.
        
        :return     <str>
        """
        return self._name

    def language(self):
        """
        Returns the language associated with this builder.
        
        :return     <str>
        """
        return self._language

    def license(self):
        """
        Returns the license for this builder.
        
        :return     <str>
        """
        return self._license

    def licenseFile(self):
        """
        Returns the license file for this builder.
        
        :return     <str>
        """
        if self._licenseFile:
            return self._licenseFile
        elif self._license:
            f = projex.resources.find('licenses/{0}.txt'.format(self.license()))
            return f
        else:
            return ''

    def loadXml(self, xdata, filepath=''):
        """
        Loads properties from the xml data.
        
        :param      xdata | <xml.etree.ElementTree.Element>
        """
        # build options
        opts = {'platform': sys.platform}

        mkpath = lambda x: _mkpath(filepath, x, **opts)

        # lookup environment variables
        xenv = xdata.find('environment')
        if xenv is not None:
            env = {}
            log.info('loading environment...')
            for xkey in xenv:
                text = xkey.text
                if text:
                    env[xkey.tag] = os.path.expandvars(text)
                else:
                    env[xkey.tag] = ''

            self.setEnvironment(env)

        # lookup general settings
        xsettings = xdata.find('settings')
        if xsettings is not None:
            for xsetting in xsettings:
                key = xsetting.tag
                val = xsetting.text
                attr = '_' + key
                if hasattr(self, attr):
                    setattr(self, attr, val)

        # lookup options
        xoptions = xdata.find('options')
        if xoptions is not None:
            options = 0
            for xopt in xoptions:
                key = xopt.tag
                value = xopt.text

                if value.lower() == 'true':
                    try:
                        options |= Builder.Options[key]
                    except KeyError:
                        continue

            self._options = options

        # lookup path options
        xpaths = xdata.find('paths')
        if xpaths is not None:
            for xpath in xpaths:
                key = xpath.tag
                path = xpath.text

                if key.endswith('Paths'):
                    path = map(mkpath, path.split(';'))
                else:
                    path = mkpath(path)

                setattr(self, '_' + key, path)

        # lookup executable options
        xexe = xdata.find('executable')
        if xexe is not None:
            exe_tags = {'runtime': '_runtime',
                        'exe': '_executableName',
                        'cli': '_executableCliName',
                        'product': '_productName'}

            for tag, prop in exe_tags.items():
                xtag = xexe.find(tag)
                if xtag is not None:
                    value = xtag.text
                    if value.startswith('.'):
                        value = mkpath(value)

                    setattr(self, prop, value)

            # load exclude options
            xexcludes = xexe.find('excludes')
            if xexcludes is not None:
                excludes = []
                for xexclude in xexcludes:
                    excludes.append(xexclude.text)
                self.setExecutableExcludes(excludes)

            # load build data
            xexedata = xexe.find('data')
            if xexedata is not None:
                data = []
                for xentry in xexedata:
                    if xentry.tag == 'tree':
                        path = xentry.get('path', '')
                        if path:
                            path = mkpath(path)
                        else:
                            path = self.sourcePath()

                        prefix = xentry.get('prefix', os.path.basename(path))
                        excludes = xentry.get('excludes', '').split(';')

                        if excludes:
                            data.append(('tree', (path, prefix, excludes)))
                    else:
                        for xitem in xentry:
                            data.append((xentry.tag, xitem.attrs))

                self.setExecutableData(data)

            # load hidden imports
            xhiddenimports = xexe.find('hiddenimports')
            if xhiddenimports is not None:
                imports = []
                for ximport in xhiddenimports:
                    imports.append(ximport.text)
                self.setHiddenImports(imports)

            # load options
            xopts = xexe.find('options')
            if xopts is not None:
                for xopt in xopts:
                    if xopt.text.startswith('.'):
                        value = mkpath(xopt.text)
                    else:
                        value = xopt.text
                    self._executableOptions[xopt.tag] = value

        # lookup installer options
        xinstall = xdata.find('installer')
        if xinstall is not None:
            install_tags = {'name': '_installName'}

            for tag, prop in install_tags.items():
                xtag = xinstall.find(tag)
                if xtag is not None:
                    value = xtag.text
                    if value.startswith('.'):
                        value = mkpath(value)
                    setattr(self, prop, value)

            xopts = xinstall.find('options')
            if xopts is not None:
                for xopt in xopts:
                    if xopt.text.startswith('.'):
                        value = mkpath(xopt.text)
                    else:
                        value = xopt.text

                    self._installerOptions[xopt.tag] = value

            xdirectories = xinstall.find('additional_directories')
            if xdirectories is not None:
                for xdir in xdirectories:
                    self._installDirectories[xdir.get('path')] = xdir.get('source', '')

    def loadYaml(self, ydata, filepath=''):
        """
        Loads properties from the yaml data.
        
        :param      ydata | <dict>
        """
        # build options
        opts = {'platform': sys.platform}

        mkpath = lambda x: _mkpath(filepath, x, **opts)

        # lookup environment variables
        env = {}
        for key, text in ydata.get('environment', {}).items():
            if text:
                env[key] = os.path.expandvars(text)
            else:
                env[key] = ''

        self.setEnvironment(env)

        # lookup general settings
        for key, val in ydata.get('settings', {}).items():
            attr = '_' + key
            if hasattr(self, attr):
                setattr(self, attr, val)

        # lookup options
        yoptions = ydata.get('options')
        if yoptions is not None:
            options = 0
            for key, value in yoptions.items():
                if value:
                    try:
                        options |= Builder.Options[key]
                    except KeyError:
                        continue

            self._options = options

        # lookup path options
        for key, path in ydata.get('paths', {}).items():
            if key.endswith('Paths'):
                path = map(mkpath, path.split(';'))
            else:
                path = mkpath(path)

            setattr(self, '_' + key, path)

        # lookup executable options
        yexe = ydata.get('executable')
        if yexe is not None:
            exe_tags = {'runtime': '_runtime',
                        'exe': '_executableName',
                        'cli': '_executableCliName',
                        'product': '_productName'}

            for tag, prop in exe_tags.items():
                if tag in yexe:
                    value = yexe.pop(tag)
                    if value.startswith('.'):
                        value = mkpath(value)

                    setattr(self, prop, value)

            # load exclude options
            self.setExecutableExcludes(yexe.get('excludes', []))

            # load build data
            yexedata = yexe.get('data', {})
            if yexedata:
                data = []
                for key, value in yexedata.items():
                    if key == 'tree':
                        path = value.get('path', '')
                        if path:
                            path = mkpath(path)
                        else:
                            path = self.sourcePath()

                        prefix = value.get('prefix', os.path.basename(path))
                        excludes = value.get('excludes', '').split(';')

                        if excludes:
                            data.append(('tree', (path, prefix, excludes)))

                    else:
                        for item in value:
                            data.append((key, item))

                self.setExecutableData(data)

            # load hidden imports
            self.setHiddenImports(yexe.get('hiddenimports', []))

            # load options
            for key, value in yexe.get('options', {}).items():
                value = nstr(value)
                if value.startswith('.'):
                    value = mkpath(value)
                self._executableOptions[key] = value

        # lookup installer options
        yinstall = ydata.get('installer')
        if yinstall is not None:
            install_tags = {'name': '_installName'}

            for tag, prop in install_tags.items():
                if tag in yinstall:
                    value = yinstall.pop(tag, None)
                    if value.startswith('.'):
                        value = mkpath(value)
                    setattr(self, prop, value)

            for key, value in yinstall.get('options', {}).items():
                if type(value) in (unicode, str) and value.startswith('.'):
                    value = mkpath(value)

                self._installerOptions[key] = value

            for path in yinstall.get('additional_directories', []):
                self._installDirectories[path.get('path', '')] = path.get('source', '')

    def options(self):
        """
        Returns the build options for this instance.
        
        :return     <Builder.Options>
        """
        return self._options

    def outputPath(self):
        """
        Returns the output path for this builder.
        
        :return     <str>
        """
        return self._outputPath

    def resourcePath(self):
        """
        Returns the path for generating the revision information.
        
        :return     <str>
        """
        return self._resourcePath

    def revision(self):
        """
        Returns the revision associated with this builder instance.
        
        :return     <str>
        """
        return self._revision

    def revisionFilename(self):
        """
        Returns the filename that will be generated for automatic
        revision tracking.
        
        :return     <str>
        """
        return self._revisionFilename

    def runtime(self):
        """
        Returns the runtime script for this executable.
        
        :return     <str>
        """
        return self._runtime

    def setAuthor(self, author):
        """
        Returns the author associated with this builder.
        
        :param      author | <str>
        """
        self._author = author

    def setAuthorEmail(self, email):
        """
        Returns the author email associated with this builder.
        
        :param      email | <str>
        """
        self._authorEmail = email

    def setBrief(self, brief):
        """
        Returns the brief associated with this builder.
        
        :param      brief | <str>
        """
        self._brief = brief

    def setBuildPath(self, buildPath):
        """
        Sets the build path for this instance to the given path.
        
        :param      buildPath | <str>
        """
        self._buildPath = buildPath

    def setCertificate(self, cert):
        """
        Sets the signing certificate file for this builder.
        
        :param     cert | <str>
        """
        self._certificate = cert

    def setClassifiers(self, classifiers):
        """
        Returns the classifiers associated with this builder.
        
        :param      classifiers | [<str>, ..]
        """
        self._classifiers = classifiers

    def setCompany(self, company):
        """
        Returns the company associated with this builder.
        
        :param      company | <str>
        """
        self._company = company

    def setCompanyUrl(self, companyUrl):
        """
        Returns the company url associated with this builder.
        
        :param      companyUrl | <str>
        """
        self._companyUrl = companyUrl

    def setDistributionName(self, distname):
        """
        Sets the distribution name associated with this builder.
        
        :param      distname | <str>
        """
        self._distributionName = distname

    def setDistributionPath(self, distpath):
        """
        Sets the distribution path associated with this builder.
        
        :param      distpath | <str>
        """
        self._distributionPath = distpath

    def setDependencies(self, dependencies):
        """
        Returns the dependencies associated with this builder.
        
        :param      dependencies | [<str>, ..]
        """
        self._dependencies = dependencies

    def setDescription(self, description):
        """
        Returns the description associated with this builder.
        
        :param      description | <str>
        """
        self._description = description

    def setDoxfile(self, doxfile):
        """
        Sets the dox file for the builder.
        
        :param      doxfile | <str>
        """
        self._doxfile = doxfile

    def setEnvironment(self, environ):
        """
        Sets the environment for this builder to the inputted environment.
        
        :param      environ | {<str> key: <str> value, ..}
        """
        self._environment = environ

    def setExecutableExcludes(self, excludes):
        """
        Sets the exclude packages for this executable.
        
        :param     excludes | [<str>, ..]
        """
        self._executableExcludes = excludes

    def setExecutableData(self, data):
        """
        Sets a list of the executable data that will be collected for this
        pyinstaller.
        
        :param      data | [(<str> type, {<str> option: <str> value})]
        """
        self._executableData = data

    def setProductName(self, product):
        """
        Sets the folder for the executable this builder will generate.
        
        :param     folder | <str>
        """
        self._productName = product

    def setExecutableName(self, name):
        """
        Sets the name for the executable for this builder to the
        given name.
        
        :param      name | <str>
        """
        self._executableName = name

    def setExecutableCliName(self, name):
        """
        Sets the name for the executable for this builder to the
        given name.
        
        :param      name | <str>
        """
        self._executableCliName = name

    def setExecutablePath(self, path):
        """
        Sets the exectuable path for this builder to the given path.
        
        :param      path | <str>
        """
        self._executablePath = path

    def setExecutableOption(self, key, value):
        """
        Sets the executable option for given key to the inptued value.
        
        :param      key | <str>
                    value | <str>
        """
        self._executableOptions[key] = value

    def setHiddenImports(self, imports):
        """
        Sets the hidden imports for this builder to the given list of imports.
        
        :param      imports | [<str>, ..]
        """
        self._hiddenImports = imports

    def setHookPaths(self, paths):
        """
        Sets the location for the hooks path for additional PyInstaller hook
        information.
        
        :param      path | <str>
        """
        self._hookPaths = paths

    def setIgnoreFileTypes(self, ftypes):
        """
        Sets the file types to ignore for this builder.
        
        :param      ftypes | [<str>, ..]
        """
        self._ignoreFileTypes = ftypes

    def setInstallName(self, name):
        """
        Sets the name for the installer for this builder to the
        given name.
        
        :param      name | <str>
        """
        self._installName = name

    def setInstallPath(self, path):
        """
        Sets the installation path for this builder to the given path.
        
        :param      path | <str>
        """
        self._installPath = path

    def setInstallerOption(self, key, value):
        """
        Sets the installer option for given key to the inptued value.
        
        :param      key | <str>
                    value | <str>
        """
        self._installerOptions[key] = value

    def setKeywords(self, keywords):
        """
        Returns the keywords associated with this builder.
        
        :param      keywords | <str>
        """
        self._keywords = keywords

    def setLanguage(self, language):
        """
        Sets the language is associated with this builder.
        
        :param      language | <str>
        """
        self._language = language

    def setLicense(self, license_):
        """
        Returns the license associated with this builder.
        
        :param      license_ | <str>
        """
        self._license = license_

    def setLicenseFile(self, filename):
        """
        Sets the filename for the license file that will be included
        with the build system.
        
        :param      filename | <str>
        """
        self._licenseFile = filename

    def setName(self, name):
        """
        Sets the name for this instance.
        
        :param      name | <str>
        """
        self._name = name

    def setOptions(self, options):
        """
        Sets the options for this builder instance.
        
        :param      options | <Builder.Options>
        """
        self._options = options

    def setOutputPath(self, outpath):
        """
        Sets the output path for this builder.
        
        :param      outpath | <str>
        """
        self._outputPath = outpath

    def setResourcePath(self, path):
        """
        Sets the path for the resources for this builder.
        
        :param      path | <str>
        """
        self._resourcePath = path

    def setRevision(self, rev):
        """
        Sets the revision information for this builder.
        
        :param      rev | <str>
        """
        self._revision = rev

    def setRevisionFilename(self, filename):
        """
        Sets the revision filename for this instance.
        
        :param      filename | <str>
        """
        self._revisionFilename = filename

    def setRuntime(self, runtime):
        """
        Sets the runtime script for this builder to the given path.  This is
        used in conjunction with generateExecutable to determine what paths
        to use for building a runtime file.
        
        :param      runtime | <str>
        """
        self._runtime = runtime

    def setSigncmd(self, cmd):
        """
        Sets the command required for the signature of this tool.  It should
        accept 2 keyword format variables: filename and cert.
        
        :param      cmd | <str>
        """
        self._signcmd = cmd

    def setSpecfile(self, specfile):
        """
        Sets the specfile for the builder for this instance.
        
        :param      specfile | <str>
        """
        self._specfile = specfile

    def setSourcePath(self, path):
        """
        Sets the path for the revision for this builder object.
        
        :param      path | <str>
        """
        self._sourcePath = path

    def setVersion(self, version):
        """
        Sets the version information for this builder.
        
        :param      version | <str>
        """
        self._version = version

    def signcmd(self):
        """
        Returns the sign tool command to be run when signing files.
        
        :return     <str>
        """
        return self._signcmd

    def sign(self, filename):
        """
        Signs the filename with the certificate associated with this builder.
        
        :param      filename | <str>
        
        :return     <bool> | success
        """
        sign = self.signcmd()
        certificate = self.certificate()
        if not sign:
            log.error('No signcmd defined.')
            return False
        elif not certificate and '{cert}' in sign:
            log.error('No sign certificated defined.')
            return False

        log.info('Signing {0}...'.format(filename))
        sign = os.path.expandvars(sign)
        filename = os.path.expandvars(filename)
        cert = os.path.expandvars(certificate)

        # let the previous process finish fully, or we might get some file errors
        time.sleep(2)
        return cmdexec(sign.format(filename=filename, cert=cert)) == 0

    def specfile(self):
        """
        Returns the specfile for generating pyInstaller information.
        
        :return     <str>
        """
        return self._specfile

    def sourcePath(self):
        """
        Returns the path for generating the revision information.
        
        :return     <str>
        """
        return self._sourcePath

    def version(self):
        """
        Returns the version associated with this builder.
        
        :return     <str>
        """
        return self._version

    @staticmethod
    def plugin(name, module=''):
        """
        Returns the plugin for the given name.  By default, the
        base Builder instance will be returned.
        
        :param      name | <str>
        """
        if module:
            mod = projex.importfile(module)
            if mod:
                return getattr(mod, nstr(name), None)

        return Builder._plugins.get(nstr(name))

    @staticmethod
    def register(plugin, name=None):
        """
        Registers the given builder as a plugin to the system.
        
        :param      plugin | <subclass of PackageBuilder>
                    name   | <str> || None
        """
        if name is None:
            name = plugin.__name__

        Builder._plugins[nstr(name)] = plugin

    @classmethod
    def fromXml(cls, xdata, filepath=''):
        """
        Generates a new builder from the given xml data and then
        loads its information.
        
        :param      xdata | <xml.etree.ElementTree.Element>
        
        :return     <Builder> || None
        """
        builder = cls()
        builder.loadXml(xdata, filepath=filepath)
        return builder

    @classmethod
    def fromYaml(cls, ydata, filepath=''):
        """
        Generates a new builder from the given yaml data and then
        loads its information.
        
        :param      ydata | <dict>
        
        :return     <Builder> || None
        """
        builder = cls()
        builder.loadYaml(ydata, filepath=filepath)
        return builder

    @staticmethod
    def fromFile(filename):
        """
        Parses the inputted xml file information and generates a builder
        for it.
        
        :param      filename | <str>
        
        :return     <Builder> || None
        """
        xdata = None
        ydata = None

        # try parsing an XML file
        try:
            xdata = ElementTree.parse(filename).getroot()
        except StandardError:
            xdata = None

        if xdata is None:
            # try parsing a yaml file
            if yaml:
                with open(filename, 'r') as f:
                    text = f.read()

                try:
                    ydata = yaml.load(text)
                except StandardError:
                    return None
            else:
                log.warning('Could not process yaml builder!')

        # load a yaml definition
        if type(ydata) == dict:
            typ = ydata.get('type')
            module = ydata.get('module')
            builder = Builder.plugin(typ, module)
            if builder:
                return builder.fromYaml(ydata, os.path.dirname(filename))
            else:
                log.warning('Could not find builder: {0}'.format(typ))

        # load an xml definition
        elif xdata is not None:
            typ = xdata.get('type')
            module = xdata.get('module')
            builder = Builder.plugin(typ, module)
            if builder:
                return builder.fromXml(xdata, os.path.dirname(filename))
            else:
                log.warning('Could not find builder: {0}'.format(typ))

        return None


# ----------------------------------------------------------------------

class PackageBuilder(Builder):
    """ A builder for an individual package. """

    def __init__(self, pkg):
        super(PackageBuilder, self).__init__()

        # set build information from the package
        filepath = getattr(pkg, '__file__', '')
        if '__init__' in filepath:
            srcpath = os.path.dirname(filepath)
            product = pkg.__name__
        else:
            if filepath.endswith('.pyc'):
                filepath = filepath[:-1]

            srcpath = filepath
            product = os.path.basename(srcpath)

        rscpath = os.path.join(srcpath, '..', '..', 'resources')
        buildpath = os.path.join(srcpath, '..', '.build')
        distpath = os.path.join(srcpath, '..', '.dist')
        outpath = os.path.join(srcpath, '..', '.bin', sys.platform)

        instpath = os.path.dirname(sys.executable)
        instpath = os.path.join(instpath, 'Lib', 'site-packages')

        self.setProductName(product)
        self.setDistributionPath(os.path.abspath(distpath))
        self.setSourcePath(os.path.abspath(srcpath))
        self.setResourcePath(os.path.abspath(rscpath))
        self.setBuildPath(os.path.abspath(buildpath))
        self.setOutputPath(os.path.abspath(outpath))
        self.setInstallPath(instpath)

        if hasattr(pkg, '__bdist_name__'):
            self.setName(getattr(pkg, '__bdist_name__', ''))
        else:
            self.setName(getattr(pkg, '__name__', ''))

        self.setVersion(getattr(pkg, '__version__', '0.0'))
        self.setRevision(getattr(pkg, '__revision__', ''))
        self.setAuthor(getattr(pkg, '__maintainer__', ''))
        self.setAuthorEmail(getattr(pkg, '__email__', ''))
        self.setDescription(getattr(pkg, '__doc__', ''))
        self.setBrief(getattr(pkg, '__brief__', ''))
        self.setLicense(getattr(pkg, '__license__', ''))
        self.setCompany(getattr(pkg, '__company__', ''))
        self.setCompanyUrl(getattr(pkg, '__company_url__', ''))

    @classmethod
    def fromXml(cls, xdata, filepath=''):
        """
        Generates a new builder from the given xml data and then
        loads its information.
        
        :param      xdata | <xml.etree.ElementTree.Element>
        
        :return     <Builder> || None
        """
        module = None
        pkg_data = xdata.find('package')
        if pkg_data is not None:
            path = pkg_data.find('path').text
            name = pkg_data.find('name').text

            if filepath:
                path = os.path.join(filepath, path)

            path = os.path.abspath(path)
            sys.path.insert(0, path)
            sys.modules.pop(name, None)

            try:
                __import__(name)
                module = sys.modules[name]
            except (ImportError, KeyError):
                return None
        else:
            return None

        # generate the builder
        builder = cls(module)
        builder.loadXml(xdata, filepath=filepath)
        return builder

    @classmethod
    def fromYaml(cls, ydata, filepath=''):
        """
        Generates a new builder from the given xml data and then
        loads its information.
        
        :param      ydata | <xml.etree.ElementTree.Element>
        
        :return     <Builder> || None
        """
        module = None
        pkg_data = ydata.get('package')
        if pkg_data is not None:
            path = pkg_data.get('path', '')
            name = pkg_data.get('name', '')

            if filepath:
                path = os.path.join(filepath, path)

            path = os.path.abspath(path)
            sys.path.insert(0, path)
            sys.modules.pop(name, None)

            try:
                __import__(name)
                module = sys.modules[name]
            except (ImportError, KeyError):
                return None
        else:
            return None

        # generate the builder
        builder = cls(module)
        builder.loadYaml(ydata, filepath=filepath)
        return builder


class ApplicationBuilder(PackageBuilder):
    def __init__(self, pkg):
        super(ApplicationBuilder, self).__init__(pkg)

        self.setOptions(self.Options.GenerateDocs |
                        self.Options.GenerateExecutable |
                        self.Options.GenerateInstaller)


class SignedApplicationBuilder(ApplicationBuilder):
    def __init__(self, pkg):
        super(ApplicationBuilder, self).__init__(pkg)

        self.setOptions(self.Options.GenerateDocs |
                        self.Options.GenerateExecutable |
                        self.Options.GenerateInstaller |
                        self.Options.Signed)


Builder.register(PackageBuilder)
Builder.register(ApplicationBuilder)
Builder.register(SignedApplicationBuilder)


def build_cmd():
    if len(sys.argv) < 2:
        print 'usage: projex/xbuild/builder [buildfile] (--no-remote)'
        sys.exit(0)

    xml = None
    ydata = None

    # load environment settings
    try:
        xml = ElementTree.parse(sys.argv[1]).getroot()
    except StandardError:
        with open(sys.argv[1], 'r') as f:
            try:
                ydata = yaml.load(f.read())
            except StandardError:
                ydata = None

    env = {}
    if xml is not None:
        xenv = xml.find('environment')
        if xenv is not None:
            for xentry in xenv:
                k, v = (xentry.tag, xentry.text)
                env[k] = os.path.expandvars(v)

    elif type(ydata) == dict:
        for k, v in ydata.get('environment', {}).items():
            if v is None:
                v = ''

            env[k] = os.path.expandvars(v)

    for k, v in env.items():
        os.environ[k] = v

    # run this build in another environment
    if '--no-remote' not in sys.argv and \
       'PYTHON' in env and \
       env['PYTHON'] != sys.executable:
        cmd = '{0} {1} {2} --no-remote'.format(env['PYTHON'], __file__, sys.argv[1])
        log.info('starting remote python process...')
        log.info(cmd)
        result = cmdexec(cmd)
        sys.exit(result)
    else:
        # create the builder
        builder = Builder.fromFile(sys.argv[1])
        if builder:
            builder.build()
            sys.exit(0)
        sys.exit(1)


if __name__ == '__main__':
    logging.basicConfig()
    log.setLevel(logging.INFO)
    build_cmd()


