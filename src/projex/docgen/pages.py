import inspect
import logging
import os
import re
import sys

from xml.etree import ElementTree

import projex
from projex import makotext
from projex.enum import enum
from projex import wikitext
from collections import OrderedDict
from projex.docgen import EXTERNALS

logger = logging.getLogger(__name__)

try:
    from xqt import QtCore
except ImportError:
    pass

MEMBER_KINDS = [
    'Module',
    'Class',
    'Variable',
    'Member',
    'Property',
    'Enum',
    'Function',
    'Method',
    'Signal',
    'Slot',
    'Abstract Method',
    'Class Method',
    'Static Method',
    'Deprecated Method',
    'Builtin',
]

MEMBER_PRIVACY = [
    '',
    'Public',
    'Imported Public',
    'Protected',
    'Imported Protected',
    'Private',
    'Imported Private',
]

SECTIONS = []
for privacy in MEMBER_PRIVACY:
    for kind in MEMBER_KINDS:
        SECTIONS.append(' '.join((privacy, kind)).strip())

#----------------------------------------------------------------------

class Member(object):
    def __init__(self, data, functionType='Method'):
        if type(data) == tuple:
            name = data[0]
            kind = data[1]
            cls = data[2]
            obj = data[3]
        else:
            name = data.name
            kind = data.kind
            cls = data.defining_class
            obj = data.object
            
        try:
            kind = data.object.func_type
        except AttributeError:
            pass
        
        qtype_docs = ''
        
        # strip out private member headers
        results = re.match('^(_\w+)(__.+)', name)
        if results:
            name = results.group(2)
        
        # determine the privacy level
        if name.startswith('__'):
            privacy = 'Private'
        elif name.startswith('_'):
            privacy = 'Protected'
        else:
            privacy = 'Public'
        
        # look for specific kind information
        if inspect.ismodule(obj):
            kind = 'Module'
        
        elif inspect.isclass(obj):
            kind = 'Class'

        elif kind == 'method':
            type_name = type(obj).__name__
            
            if type_name in ('pyqtSignal', 'Signal'):
                kind = 'Signal'
                try:
                    qtype_docs = QtCore.Signal.docs(obj)
                except:
                    qtype_docs = str(obj)
            
            elif type_name in ('pyqtSlot', 'Slot'):
                kind = 'Slot'
                try:
                    qtype_docs = QtCore.Slot.docs(obj)
                except:
                    qtype_docs = str(obj)
                
            elif type_name in ('pyqtProperty', 'Property'):
                kind = 'Property'
            elif name.startswith('__') and name.endswith('__'):
                kind = 'Builtin'
            else:
                kind = 'Method'
        
        elif isinstance(obj, staticmethod):
            kind = 'Static Method'
            obj = getattr(cls, name, None)

        elif isinstance(obj, classmethod):
            kind = 'Class Method'
            obj = getattr(cls, name, None)

        elif inspect.ismethod(obj) or inspect.ismethoddescriptor(obj):
            if name.startswith('__') and name.endswith('__'):
                kind = 'Builtin'
            else:
                kind = 'Method'

        elif inspect.isbuiltin(obj):
            kind = 'Variable'

        elif isinstance(obj, enum):
            kind = 'Enum'

        elif inspect.isfunction(obj) or callable(obj):
            if name.startswith('__') and name.endswith('__'):
                kind = 'Builtin'
            else:
                kind = functionType

        else:
            kind = 'Variable'
        
        # setup the property information
        self.name = name
        self.defining_class = cls
        self.object = obj
        self.kind = kind
        self.is_callable = callable(obj) and not inspect.isclass(obj)
        self.privacy = privacy
        self.qtype_docs = qtype_docs

    @property
    def args(self):
        obj = self.object
        try:
            opts = (obj, obj.im_func)
        except AttributeError:
            opts = (obj,)
        
        out = ''
        for opt in opts:
            try:
                out = inspect.formatargspec(*inspect.getargspec(self.object))
                break
            except TypeError:
                continue
        
            try:
                out = getattr(opt.im_func.func_args)
                break
            except AttributeError:
                continue
        
        if not out:
            try:
                out = self.object.func_args
            except AttributeError:
                out = '(...) [unknown]'
        
        # ignore default properties for class methods & instance methods
        if self.kind == 'Class Method':
            out = out.replace('(cls, ', '(')
            out = out.replace('(cls)', '()')
        
        elif self.kind == 'Method':
            out = out.replace('(self, ', '(')
            out = out.replace('(self)', '()')
        
        return out

    @property
    def reimpliments(self):
        return ''

    @property
    def reimplimented(self):
        return ''

    @property
    def section(self):
        return ' '.join((self.privacy, self.kind)).strip()

#----------------------------------------------------------------------

class DoxFolder(object):
    def __init__(self, project, **options):
        self._project = project
        self._title = options.get('title', '')
        self._parent = options.get('parent', None)
        self._module = options.get('module', '')
        self._modulePath = options.get('modulePath', '')
        self._order = options.get('order', 0)

    def basepath(self):
        return self.filepath()

    def children(self):
        """
        Returns a combination of the child pages and folders for this
        folder instance, sorted by their sort order.
        
        :return     [<DoxFolder> || <DoxPage>, ..]
        """
        out = self.folders() + self.pages()
        out.sort(key=lambda x: (x.order(), x.filepath()))
        return out

    def defaultpage(self):
        """
        Returns the default page associated with this folder.
        
        :return     <DoxPage> || None
        """
        first = None
        for page in sorted(self.pages(), key=lambda x: x.order()):
            if not first:
                first = page

            if page.filename('html') in ('__init__.html', 'index.html'):
                return page
        
        return first

    def filename(self):
        return projex.text.underscore(self.title())

    def filepath(self):
        """
        Returns the filepath that will be associated with this page on
        export.
        
        :return     <str>
        """
        parts = [self.filename()]
        for parent in self.hierarchy():
            parts.append(parent.filename())
        
        return os.path.join(*reversed(parts))

    def folderName(self):
        """
        Returns the page name associated with this page.
        
        :return     <str>
        """
        if self._title:
            parts = [projex.text.underscore(self._title)]
        else:
            parts = ['missing']
        
        for folder in self.hierarchy():
            parts.append(projex.text.underscore(folder.title()))
        
        return '.'.join(reversed(parts))

    def folders(self):
        """
        Returns a list of the child folders associated with this folder.
        
        :return     [<DoxFolder>, ..]
        """
        return self.project().subfolders(self)

    def hierarchy(self):
        """
        Returns the folder hierarchy for this page.
        
        :return     [<DoxFolder>, ..]
        """
        parent = self.parent()
        while parent:
            yield parent
            parent = parent.parent()

    def module(self):
        """
        Returns the module associated with this folder.
        
        :return     <str>
        """
        return self._module

    def modulePath(self):
        """
        Returns the relative path for this module.  If no path is supplied
        then the default PYTHONPATH will be used.
        
        :return     <str>
        """
        return self._modulePath

    def order(self):
        """
        Returns the order associated with this page.
        
        :return     <int>
        """
        return self._order

    def pages(self):
        """
        Returns the pages that are associated with this folder.
        
        :return     [<DoxPage>, ..]
        """
        return self.project().subpages(self)
    
    def pageName(self):
        page = self.defaultpage()
        if page:
            return page.pageName()
        return ''

    def parent(self):
        """
        Returns the parent folder for this instance.
        
        :return     <DoxFolder> || None
        """
        return self._parent

    def project(self):
        """
        Returns the project associated with this folder.
        
        :return     <DoxProject>
        """
        return self._project

    def remove(self):
        """
        Removes this page from the project.
        """
        self.project().removeFolder(self)

    def setModule(self, module):
        """
        Sets the module associated with this folder.
        
        :param      module | <str>
        """
        self._module = module

    def setModulePath(self, path):
        """
        Sets the relative path to this module.
        
        :param      path | <str>
        """
        self._modulePath = path

    def setParent(self, parent):
        """
        Sets the parent folder for this instance to the inputed folder.
        
        :param      parent | <DoxFolder> || None
        """
        self._parent = parent

    def setOrder(self, order):
        """
        Sets the order associated with this page.
        
        :param      order | <int>
        """
        self._order = order

    def title(self):
        """
        Returns the title for this folder.
        
        :return     <str> || None
        """
        return self._title

    def toXml(self, xparent):
        """
        Stores the data for this folder as XML
        
        :param      xparent | <xml.etree.ElementTree.Element>
        """
        if self._module:
            xinspect = ElementTree.SubElement(xparent, 'inspect')
            xinspect.set('name', self.title())
            xinspect.set('module', self._module)
            xinspect.set('path', self._modulePath)
        
        else:
            xfolder = ElementTree.SubElement(xparent, 'folder')
            xfolder.set('title', self._title)
            for child in self.children():
                child.toXml(xfolder)

    def toc(self, xparent, extension=''):
        """
        Returns the table of contents entry for this item.
        
        :param      xparent     | <xml.etree.ElementTree>
                    extension   | <str>
        
        :return     <xml.etree.ElementTree>
        """
        xml = ElementTree.SubElement(xparent, 'item')
        xml.set('title', self.title())
        
        try:
            xml.set('url', self.defaultpage().filepath(extension=extension))
        except AttributeError:
            pass
        
        for child in self.children():
            child.toc(xml, extension)
        
        return xml

#----------------------------------------------------------------------

class DoxPage(object):
    def __init__(self, project, **options):
        self._project = project
        self._parent = options.get('parent', None)
        self._title = options.get('title', '')
        self._pageName = options.get('pageName', '')
        self._pageType = options.get('pageType', 'wiki')
        self._filename = options.get('filename', '')
        self._sourcefile = options.get('sourcefile', '')
        self._scopes = options.get('scopes', {''})
        self._order = options.get('order', 0)

    def addScope(self, scope):
        """
        Adds the new scope for this page.
        
        :param      scope | <str>
        """
        self._scopes.add(scope)

    def basepath(self):
        parent = self.parent()
        if parent and '__init__' in self.filename():
            return os.path.join(parent.basepath(), self.title())
        elif '__init__' in self.filename():
            return self.title()
        elif parent:
            return parent.basepath()
        else:
            return ''

    def breadcrumbs(self):
        """
        Returns the breadcrumb links for this instance.
        
        :return     [<str>, ..]
        """
        parent = self.parent()
        if not parent:
            parent = self.project()
        
        name = self.title().split('.')[-1]
        parts = ['<a class="active">{0}</a>'.format(name)]
        
        for i, parent in enumerate(self.hierarchy()):
            name = parent.title().split('.')[-1]
            opts = [self.relpath(parent), name]
            parts.append('<a href="{0}">{1}</a>'.format(*opts))

        proj_title = self.project().title()
        if parts:
            opts = [self.relpath(self.project()), proj_title]
            parts.append('<a href="{0}">{1}</a>'.format(*opts))
        else:
            parts.append('<a class="static">{0}</a>'.format(proj_title))

        return list(reversed(parts))

    def children(self):
        """
        Returns a combination of the child pages and folders for this
        folder instance, sorted by their sort order.
        
        :return     [<DoxFolder> || <DoxPage>, ..]
        """
        return self.project().subpages(self)

    def defaultpage(self):
        return self

    def displayName(self):
        return self.title()

    def hierarchy(self):
        """
        Returns the folder hierarchy for this page.
        
        :return     [<DoxFolder> || <DoxPage>, ..]
        """
        parent = self.parent()
        while parent:
            yield parent
            parent = parent.parent()

    def filename(self, extension='', scope=''):
        """
        Returns the filename assocaited with this page.
        
        :param      extension | <str>
        """
        parts = []
        if self._filename:
            parts.append(self._filename)
        else:
            parts.append(projex.text.underscore(self.title()))

        if scope:
            parts.append(scope)
        
        if not extension:
            extension = self.project().currentExtension()

        return '-'.join(map(str, parts)) + extension

    def filepath(self, extension='', scope=''):
        """
        Returns the filepath that will be associated with this page on
        export.
        
        :return     <str>
        """
        return os.path.join(self.basepath(), self.filename(extension, scope))

    def folder(self):
        folder = self.parent()
        while folder and not isinstance(folder, DoxFolder):
            folder = folder.parent()
        return folder

    def order(self):
        """
        Returns the order associated with this page.
        
        :return     <int>
        """
        return self._order

    def parent(self):
        return self._parent

    def pageName(self):
        """
        Returns the page name associated with this page.
        
        :return     <str>
        """
        if self._pageName:
            return self._pageName
        
        if self._title:
            parts = [projex.text.underscore(self._title)]
        else:
            parts = ['missing']
        
        for item in self.hierarchy():
            if isinstance(item, DoxFolder):
                parts.append(projex.text.underscore(item.title()))
        
        return '.'.join(reversed(parts))

    def pageType(self):
        """
        Returns the page type associated with this instance.
        
        :return     <str>
        """
        return self._pageType

    def project(self):
        """
        Returns a project that is associated with this inspector object.
        
        :return     <projex.docgen.DoxProject>
        """
        return self._project

    def relpath(self, target, scope=''):
        """
        Generates a traversal from this page to the inputed target based on
        the hierarchy within the project.
        
        :param      target  | <str> || <variant>
                    scope   |  <str>
        
        :return     <str>
        """
        page = None
        target_path = ''
        incl_root = False
        
        # render a relative path to a folder
        if type(target).__name__ in ('DoxFolder', 'DoxProject'):
            page = target.defaultpage()

        # render a relative path to a page
        elif isinstance(target, DoxPage):
            page = target

        # render a relative path to a class
        elif inspect.isclass(target):
            clsname = target.__module__ + '.' + target.__name__
            page = self.project().page(clsname)
            
            # lookup external routes
            for expr, route in EXTERNALS.items():
                match = re.match(expr, clsname)
                if match:
                    return route.format(match.group(1))
        
        # render a relative path to a module
        elif inspect.ismodule(target):
            page = self.project().page(target.__name__)
        
        # render a path to a specific page or project path
        else:
            page = self.project().page(str(target))
            if not page:
                folder = self.project().folder(str(target))
                if folder:
                    page = folder.defaultpage()

            if not page:
                target_path = self.project().path(str(target))
        
        # generate the target path information
        basepath = self.project().basepath()
        curr_path = os.path.join(basepath, self.filepath())
        
        if not target_path and page:
            target_path = os.path.join(basepath, page.filepath(scope=scope))
        
        if not (curr_path and target_path):
            return ''
        
        if self.project().isPreviewMode():
            return 'file:///' + target_path
        
        curr_base, curr_name = os.path.split(curr_path)
        target_base, target_name = os.path.split(target_path)
        
        curr_base = os.path.join('.', curr_base)
        target_base = os.path.join('.', target_base)
        
        rel_base = os.path.relpath(target_base, curr_base)
        
        if rel_base == '.':
            output = target_name
        else:
            output = os.path.join(rel_base, target_name)
        
        return output.replace('\\', '/')

    def remove(self):
        """
        Removes this page from the project.
        """
        filename = self.sourcefile()
        if filename.endswith('.wiki'):
            try:
                os.remove(filename)
            except AttributeError:
                pass
        
        self.project().removePage(self)

    def scopes(self):
        """
        Returns a list of the valid scopes for this object.
        
        :return     [<str>, ..]
        """
        return list(self._scopes)

    def setOrder(self, order):
        """
        Sets the order associated with this page.
        
        :param      order | <int>
        """
        self._order = order

    def setPageName(self, name):
        """
        Sets the page name for this instance to the inputed name.
        
        :param      name | <str>
        """
        self._pageName = name

    def setParent(self, parent):
        """
        Sets the parent of this page.
        
        :param      parent | <DoxFolder> || <DoxPage> || None
        """
        self._parent = parent

    def setTitle(self, title):
        """
        Sets the title for this page to the inputed title.
        
        :param      title | <str>
        """
        self._title = title

    def sourcefile(self, relative=False):
        """
        Returns the source wiki file for this page.
        
        :return     <str>
        """
        if not self._sourcefile:
            basename = os.path.join(*self.pageName().split('.')) + '.wiki'
            if relative:
                return basename
            return os.path.join(self.project().basepath(), 'pages', basename)
        return self._sourcefile

    def title(self):
        """
        Returns the title associated with this page.
        
        :return     <str>
        """
        return self._title if self._title else self.pageName()

    def toXml(self, xparent):
        """
        Saves this page to XML
        
        :param      xparent | <xml.etree.ElementTree.Element>
        """
        xpage = ElementTree.SubElement(xparent, 'page')
        xpage.set('name', self._pageName)
        xpage.set('title', self._title)
        xpage.set('source', self._sourcefile)

    def toc(self, xparent, extension=''):
        """
        Returns the table of contents entry for this item.
        
        :param      xparent     | <xml.etree.ElementTree>
                    extension   | <str>
        
        :return     <xml.etree.ElementTree>
        """
        xml = ElementTree.SubElement(xparent, 'item')
        xml.set('title', self.title())
        xml.set('url', self.filepath(extension=extension))
        return xml

    def wikidocs(self, wikiStyle='basic'):
        """
        Renders this object out to HTML.
        """
        try:
            docs = open(self.sourcefile(), 'r').read()
        except AttributeError:
            return ''
        
        opts = {}
        opts['source'] = self
        opts['project'] = self.project()
        
        # include additional page rendering options
        paths = [os.path.join(self.project().basepath(), 'pages')]
        
        return wikitext.render(docs,
                               options=opts,
                               templatePaths=paths,
                               wikiStyle=wikiStyle)

#----------------------------------------------------------------------

class InspectionPage(DoxPage):
    def __init__(self, project, obj, **options):
        super(InspectionPage, self).__init__(project, **options)
        
        self._object = obj
        self._sections = {}
        self._members = []

    def brief(self):
        obj = self.object()
        
        try:
            docs = inspect.getdoc(obj)
        except AttributeError:
            docs = None

        if docs is None:
            try:
                docs = inspect.getcomments(obj)
            except AttributeError:
                docs = None

        if docs is None:
            docs = getattr(obj, '__doc__', '')

        if docs is None:
            return ''

        if len(docs) > 100:
            return docs[:100] + '...'

        return docs

    def collectMembers(self):
        """
        Collects all the members for this dox object and caches them.
        """
        # load all the items
        try:
            members = dict(inspect.getmembers(self.object()))
        except AttributeError:
            members = {}

        for key in dir(self.object()):
            if not key in members:
                try:
                    members[key] = getattr(self.object(), key, None)
                except AttributeError:
                    continue

        output = []
        for name, obj in sorted(members.items()):
            if inspect.isclass(self._object):
                func_type = 'Static Method'
            else:
                m_name = self._object.__name__
                try:
                    o_name = inspect.getmodule(obj).__name__
                except AttributeError:
                    continue
                
                if m_name not in o_name:
                    continue
                
                func_type = 'Function'

            output.append(Member((name, kind, None, obj), func_type))
        return output

    def inherits(self, section):
        """
        Returns the inheritance information for the section.
        
        :return     {<object> class: <int> count, ..}
        """
        return {}

    def members(self, section=None):
        """
        Collects the members for this object and returns them.
        
        :return     [<Member>, ..]
        """
        if not self._members:
            self._members = self.collectMembers()
        
        if section:
            return filter(lambda x: x.section == section, self._members)
        else:
            return self._members

    def name(self):
        """
        Returns the name for this object.
        
        :return     <str>
        """
        return self._name

    def object(self):
        """
        Returns the python object that is going to be rendered to the DOX
        file.
        
        :return     <variant>
        """
        return self._object

    def sections(self):
        """
        Returns a list of the defined sections for this object.
        
        :return     [<str>, ..]
        """
        sections = list({member.section for member in self.members()})
        sections.sort(key=SECTIONS.index)
        return sections

    def wikidocs(self, obj=None, wikiStyle='basic'):
        """
        Renders this object out to HTML.
        """
        if obj is None:
            obj = self.object()
        
        try:
            docs = inspect.getdoc(obj)
        except AttributeError:
            docs = None

        if docs is None:
            try:
                docs = inspect.getcomments(obj)
            except AttributeError:
                docs = None

        if docs is None:
            docs = getattr(obj, '__doc__', '')

        if docs is None:
            return ''

        if not docs:
            return 'No documentation found.'
        else:
            opts = {}
            opts['source'] = self
            opts['project'] = self.project()
            return wikitext.render(docs, options=opts, wikiStyle=wikiStyle)

#----------------------------------------------------------------------

class ClassInspector(InspectionPage):
    def __init__(self, project, cls, **options):
        if type(cls) in (str, unicode):
            mod, _, cls = cls.rpartition('.')
            __import__(mod)
            mod = sys.modules[mod]
            cls = getattr(mod, cls, None)

        self._all_members = []
        
        options.setdefault('pageType', 'class')
        options.setdefault('pageName', cls.__module__ + '.' + cls.__name__)
        options.setdefault('title', cls.__name__)
        options.setdefault('filename',
                           cls.__module__.split('.')[-1] + '-' + cls.__name__)
        
        super(ClassInspector, self).__init__(project, cls, **options)
        self.addScope('all')

    def allMembers(self):
        """
        Returns a list of all the members associated with this class object.
        
        :return     [<Member>, ..]
        """
        if not self._all_members:
            self.collectMembers()
        return self._all_members

    def bases(self):
        return self.object().__bases__

    def displayName(self):
        return self.object().__name__
    
    def inherits(self, section):
        output = OrderedDict()
        
        level = self.object().__bases__
        while level:
            next_level = set()
            for cls in level:
                next_level.update(cls.__bases__)
                count = len(filter(lambda x: x.defining_class == cls and \
                                             x.section == section, \
                                             self.allMembers()))
                if count:
                    output[cls] = count
            level = next_level
        
        return output
    def subclasses(self):
        out = []
        if self.project():
            for cls in self.project().pages(ClassInspector):
                if self.object() in cls.object().__bases__:
                    out.append(cls.object())
        return out

    def collectMembers(self):
        """
        Returns a list of members specific to this class.
        
        :return     [<Attribute>, ..]
        """
        # determine the class members
        try:
            members = inspect.classify_class_attrs(self.object())
        except AttributeError:
            members = []

        members = map(Member, members)
        self._all_members = members
        members = filter(lambda x: x.defining_class == self.object(), members)
        return members

#----------------------------------------------------------------------

class ModuleInspector(InspectionPage):
    def __init__(self, project, module, **options):
        if type(module) in (str, unicode):
            __import__(module)
            module = sys.modules[module]

        self._modulePath = ''

        options.setdefault('pageType', 'module')
        options.setdefault('pageName', module.__name__)
        options.setdefault('title', module.__name__.split('.')[-1])
        
        filename = os.path.basename(module.__file__).split('.')[0]
        options.setdefault('filename', filename)
        
        super(ModuleInspector, self).__init__(project, module, **options)
        self.addScope('source')

    def modulePath(self):
        return self._modulePath
    
    def setModulePath(self, path):
        self._modulePath = path
