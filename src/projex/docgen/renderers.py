import distutils.dir_util
import logging
import os
import re
import shutil
import sys
import zipfile

from xml.etree import ElementTree

import projex.text
from projex import makotext
from projex.wikitext import UrlHandler
from projex.docgen import EXTERNALS

log = logging.getLogger(__name__)

#----------------------------------------------------------------------

class DoxUrlHandler(UrlHandler):
    def __init__(self, source):
        super(UrlHandler, self).__init__()
        
        self._source = source

    def resolve(self, key):
        """
        Resolves the inputed path to a url.
        
        :param      key | <str>
        
        :return     <str>
        """
        path = self._source.relpath(key)
        if not path:
            return self.resolveClass(key)
        return (path, path != '')

    def resolveClass(self, key):
        """
        Resolves the path location to a given class.
        
        :param      key | <str>
        
        :return     <str>
        """
        key = re.sub('^subclass of ', '', key)
        modname, _, clsname = key.rpartition('.')
        
        if type(self._source).__name__ in ('ClassInspector', 'ModuleInspector'):
            if not modname:
                cls = getattr(self._source.object(), clsname, None)
                if cls is not None:
                    key = cls
            else:
                module = sys.modules.get(modname)
                if module:
                    cls = getattr(module, clsname, None)
                    if cls is not None:
                        key = cls
        
        path = self._source.relpath(key)
        if not path:
            for page in self._source.project().pages():
                if type(page).__name__ == 'ClassInspector' and \
                   page.object().__name__ == key:
                    path = self._source.relpath(page)
                    break
        
        # lookup from global external expressions
        if not path:
            try:
                key = key.__name__
            except AttributeError:
                pass
            
            for expr, route in EXTERNALS.items():
                match = re.match(expr, str(key))
                if match:
                    path = route.format(match.group(1))
                    break
        
        return (path, path != '')

    def resolveImage(self, key):
        """
        Resolves a wikitext image.
        """
        path = self._source.relpath('static:img/{0}'.format(key))
        return (path, path != '')

#----------------------------------------------------------------------

class Renderer(object):
    _plugins = {}
    
    def __init__(self, project):
        self._project = project
        self._options = {}

    def option(self, name, default=None):
        """
        Returns the value for the inputed option for this renderer.
        
        :param      name    | <str>
                    default | <variant>
        """
        return self._options.get(name, default)

    def options(self):
        """
        Returns the options that are associated with this renderer.
        
        :return     <dict>
        """
        return self._options

    def export(self, basepath):
        """
        Exports this project out to a given filepath.
        
        :param      basepath | <str>
        
        :return     <bool> | success
        """
        raise NotImplementedError

    def project(self):
        """
        Returns the project associated with this renderer.
        
        :return     <projex.docgen.DoxProject>
        """
        return self._project

    def render(self, page, scope=''):
        """
        Renders the current page and scope information.
        
        :return     <str>
        """
        raise NotImplementedError

    def setOptions(self, options):
        """
        Sets the options for this renderer to the inputed list.
        
        :param      options | <dict>
        """
        self._options = options

    @classmethod
    def extension(cls):
        return '.html'

    @staticmethod
    def create(project, format):
        """
        Creates a new renderer for the inputed project with the given format.
        
        :param      project | <projex.docgen.DoxProject>
                    format  | <str>
        
        :return     <Renderer> || None
        """
        try:
            return Renderer._plugins[str(format)](project)
        except KeyError:
            return None

    @staticmethod
    def register(format, cls):
        """
        Registers the inputed renderer class with the given format.
        
        :param      format | <str>
                    cls    | <subclass of Renderer>
        """
        Renderer._plugins[str(format)] = cls

#----------------------------------------------------------------------

class HtmlRenderer(Renderer):
    def export(self, basepath, xdkpath=''):
        """
        Exports this project out to a given filepath.
        
        :param      basepath | <str>
        
        :return     <bool> | success
        """
        proj = self.project()
        
        # export the page information
        for page in proj.pages():
            # export all the scopes for the given page
            for scope in page.scopes():
                outpath = page.filepath(scope=scope)
                if not outpath:
                    continue

                outpath = os.path.join(basepath, outpath)
                if not os.path.exists(os.path.dirname(outpath)):
                    os.makedirs(os.path.dirname(outpath))

                text = self.render(page, scope)
                
                f = open(outpath, 'w')
                f.write(text)
                f.close()

        # export the theme information
        themepath = os.path.join(basepath, '_static', proj.theme())
        distutils.dir_util.copy_tree(proj.themepath(), themepath)
        
        rscroot = os.path.join(proj.basepath(), 'resources')
        staticpath = os.path.join(basepath, '_static')
        for rscname in os.listdir(rscroot):
            if rscname != 'themes':
                fpath = os.path.join(rscroot, rscname)
                tpath = os.path.join(staticpath, rscname)
                if os.path.isdir(fpath):
                    distutils.dir_util.copy_tree(fpath, tpath)
                else:
                    shutil.copyfile(fpath, tpath)

        # export the toc contents
        toc = proj.toc()
        fname = os.path.join(basepath, 'toc.xml')
        projex.text.xmlindent(toc)
        tree = ElementTree.ElementTree(toc)
        tree.write(fname)

        # generate the XDK file
        basename = projex.text.underscore(proj.title()) + '.xdk'
        if not xdkpath:
            xdkpath = os.path.join(basepath, basename)
        zfile = zipfile.ZipFile(xdkpath, 'w')
        
        for path, folders, files in os.walk(basepath):
            if '.svn' in path:
                continue
            
            arcpath = path.replace(basepath, '')
            for filename in files:
                if filename == basename:
                    continue
                
                arcfilename = os.path.join(arcpath, filename)
                zfile.write(os.path.join(path, filename),
                            os.path.join(arcpath, filename))
        
        zfile.close()

        return True

    def render(self, page, scope=''):
        """
        Renders the current page and scope information.
        
        :return     <str>
        """
        # create the url handler for the wikitext
        handler = DoxUrlHandler(page)
        handler.setCurrent()
        
        log.info('Rendering page: {0}...'.format(page.sourcefile()))
        
        # generate the options for this project
        opts = {}
        opts['source'] = page
        opts['project'] = self.project()
        opts['renderer'] = self
        
        # include additional page rendering options
        paths = [os.path.join(self.project().basepath(), 'pages')]
        
        # determine the template for this exported file
        templ_name = page.pageType()
        if scope:
            templ_name += '_' + scope
        templ_name += '.mako'
        
        templ = self.project().template(templ_name)
        text = makotext.renderfile(templ, opts, templatePaths=paths)
        
        DoxUrlHandler._current = None
        return text

#----------------------------------------------------------------------


class MakoRenderer(Renderer):
    def export(self, basepath, xdkpath=''):
        """
        Exports this project out to a given filepath.
        
        :param      basepath | <str>
        
        :return     <bool> | success
        """
        proj = self.project()
        
        # export the page information
        for page in proj.pages():
            # export all the scopes for the given page
            for scope in page.scopes():
                outpath = page.filepath(scope=scope)
                if not outpath:
                    continue

                outpath = os.path.join(basepath, outpath)
                if not os.path.exists(os.path.dirname(outpath)):
                    os.makedirs(os.path.dirname(outpath))

                text = self.render(page, scope)
                outpath = outpath.replace('.html', '.mako')
                
                f = open(outpath, 'w')
                f.write(text)
                f.close()

        return True

    def render(self, page, scope=''):
        """
        Renders the current page and scope information.
        
        :return     <str>
        """
        # create the url handler for the wikitext
        handler = DoxUrlHandler(page)
        handler.setCurrent()
        
        log.info('Rendering page: {0}...'.format(page.sourcefile()))
        
        # generate the options for this project
        opts = {}
        opts['source'] = page
        opts['project'] = self.project()
        opts['renderer'] = self
        
        # include additional page rendering options
        paths = [os.path.join(self.project().basepath(), 'pages')]
        
        # determine the template for this exported file
        templ_name = page.pageType()
        if scope:
            templ_name += '_' + scope
        templ_name += '.mako'
        
        templ = self.project().template(templ_name)
        text = makotext.renderfile(templ, opts, templatePaths=paths)
        
        DoxUrlHandler._current = None
        return text

#----------------------------------------------------------------------

Renderer.register('html', HtmlRenderer)
Renderer.register('mako', MakoRenderer)