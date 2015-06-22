""" Defines an interface for turning methods into command line interface \
    options using optparse.
    
    :usage      |# /path/to/package/cli.py
                |
                |from projex import cli
                |
                |@cli.climethod
                |def testing():
                |   print 'here'
"""

import inspect
import logging
import sys

from .text import nativestring as nstr
from optparse import OptionParser

logger = logging.getLogger(__name__)

PROGRAM_NAME = '%prog'
PARSER_CLASS = OptionParser

# ------------------------------------------------------------------------------


class climethod(object):
    """
    Creates a wrapper for generating command line interface methods within \
    a cli package.  This wrapper will allow the developer to map methods \
    in a module to the optparse module.
    
    :param      usage | <str>
    """

    def __init__(self, func=None):
        self.__name__ = ''
        self.__doc__ = ''
        self.func = None
        self.interface = None
        self.cmd_args = []
        self.cmd_opts = {'help': False}
        self.short_keys = {'h': 'help'}

        if func is not None:
            self.setfunc(func)

    def setfunc(self, func):
        # initialize the function linking
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
        self.func = func

        # process the optional arguments and keywords
        args, varargs, keywords, defaults = inspect.getargspec(func)

        if not defaults:
            defaults = []

        if defaults:
            keymap = args[-len(defaults):]
            for i, key in enumerate(keymap):
                letter = 0
                short = key[letter]
                while True:
                    if short not in self.short_keys:
                        self.short_keys[short] = key
                        break

                    letter += 1
                    try:
                        short = key[letter]
                    except IndexError:
                        break

                self.cmd_opts[key] = defaults[i]

    def __call__(self, *args, **kwds):
        # used as the wrapper call
        if self.func is None and len(args) == 1 and inspect.isfunction(args[0]):
            self.setfunc(args[0])
            return self

        elif self.func is None:
            raise NotImplementedError

        # used as the caller
        return self.func(*args, **kwds)

    def usage(self):
        """
        Returns the usage string for this method.
        
        :return     <str>
        """
        arg_list = ' '.join(self.cmd_args).upper()
        name = self.interface.name()
        return '%s [options] %s %s' % (name, self.__name__, arg_list)

    def parser(self):
        """
        Creates a parser for the method based on the documentation.
        
        :return     <OptionParser>
        """
        usage = self.usage()
        if self.__doc__:
            usage += '\n' + nstr(self.__doc__)

        parse = PARSER_CLASS(usage=usage)

        shorts = {v: k for k, v in self.short_keys.items()}
        for key, default in self.cmd_opts.items():
            # default key, cannot be duplicated
            if key == 'help':
                continue

            try:
                short = '-' + shorts[key]
            except KeyError:
                short = ''

            if default is True:
                action = 'store_false'
            elif default is False:
                action = 'store_true'
            else:
                action = 'store'

            # add the option
            parse.add_option(short, '--%s' % key, action=action, default=default)

        return parse

    def run(self, argv):
        """
        Parses the inputted options and executes the method.
        
        :param      argv | [<str>, ..]
        """
        (opts, args) = self.parser().parse_args(argv)
        func_args = args[args.index(self.__name__) + 1:]
        func_kwds = opts.__dict__

        return self.__call__(*func_args, **func_kwds)


# ----------------------------------------------------------------------

class cliignore(object):
    def __init__(self, func):
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
        self.func = func
        self.interface = None

        self.short_keys = {}

    def __call__(self, *args, **kwds):
        return self.func(*args, **kwds)


#-------------------------------------------------------------------------------

class Interface(object):
    def __init__(self, name, scope=None):
        if scope is None:
            scope = {}

        self._name = name
        self._scope = scope

    def process(self, argv):
        """
        Processes the inputted arguments within this object's scope.
        
        :return     <int>
        """
        return globals()['process'](argv, self._scope, self)

    def register(self, obj, autogenerate=False):
        """
        Registers the inputted object to this scope.
        
        :param      obj | <module> || <function> || <climethod>
        """
        scope = self._scope

        # register a module
        if type(obj).__name__ == 'module':
            for key, value in vars(obj).items():
                # register a climethod
                if isinstance(value, climethod):
                    value.interface = self
                    scope[key] = value

                # register a function
                elif inspect.isfunction(value) and autogenerate:
                    meth = climethod(value)
                    meth.interface = self
                    scope[key] = meth

        # register a climethod
        elif isinstance(obj, climethod):
            obj.interface = self
            scope[obj.__name__] = obj

        # register a function
        elif inspect.isfunction(obj) and autogenerate:
            meth = climethod(obj)
            meth.interface = self
            scope[meth.__name__] = meth

    def name(self):
        """
        Returns the name associated with this command line interface.
        
        :return     <str>
        """
        return self._name

    def setName(self, name):
        """
        Sets the name associated with this command line interface.
        
        :param      name | <str>
        """
        self._name = name


#-------------------------------------------------------------------------------

def command(argv, scope):
    """
    Looks up a particular command from the inputted arguments for the given \
    scope.
    
    :param      argv    | [<str>, ..]
                scope   | <dict>
    
    :return     <climethod> || None
    """
    if inspect.ismodule(scope):
        scope = vars(scope)

    for cmd in scope.values():
        if not isinstance(cmd, climethod):
            continue

        if cmd.__name__ in argv:
            return cmd
    return None


def commands(scope):
    """
    Looks up all climethod instances from the inputted scope.
    
    :return     [<climethod>, ..]
    """
    if inspect.ismodule(scope):
        scope = vars(scope)

    return [cmd for cmd in scope.values() if isinstance(cmd, climethod)]


def generate(module):
    """
    Generates a new interface from the inputted module.
    
    :param      module | <module>
    
    :return     <Interface>
    """
    inter = Interface(PROGRAM_NAME)
    inter.register(module, True)
    return inter


def parser(scope, usage=''):
    """
    Generates a default parser for the inputted scope.
    
    :param      scope    | <dict> || <module>
                usage    | <str>
                callable | <str>
    
    :return     <OptionParser>
    """
    subcmds = []
    for cmd in commands(scope):
        subcmds.append(cmd.usage())

    if subcmds:
        subcmds.sort()
        usage += '\n\nSub-Commands:\n  '
        usage += '\n  '.join(subcmds)

    parse = PARSER_CLASS(usage=usage)
    parse.prog = PROGRAM_NAME
    return parse


def process(argv, scope, interface=None):
    """
    Processes any commands within the scope that matches the inputted arguments.
    If a subcommand is found, then it is run, and the system exists with the 
    return value from the command.
    
    :param      argv    | [<str>, ..]
                scope   | <dict>
    
    :return     (<dict> options, <tuple> arguments)
    """
    cmd = command(argv, scope)
    if cmd:
        sys.exit(cmd.run(argv))

    name = PROGRAM_NAME
    if interface:
        name = interface.name()

    _parser = parser(scope, '{0} [options] [<subcommand>] [<arg>]'.format(name))
    options, args = _parser.parse_args(argv)
    return options.__dict__, args
