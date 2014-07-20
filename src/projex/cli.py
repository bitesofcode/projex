#!/usr/bin/python

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

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'
__all__             = [ 'abstractmethod', 'deprecatedmethod', 'profiler' ]

import inspect
import logging
import sys

from optparse import OptionParser

logger = logging.getLogger(__name__)

PROGRAM_NAME    = '%prog'
PARSER_CLASS    = OptionParser

#------------------------------------------------------------------------------

class climethod(object):
    """
    Creates a wrapper for generating command line interface methods within \
    a cli package.  This wrapper will allow the developer to map methods \
    in a module to the optparse module.
    
    :param      usage | <str>
    """
    def __init__( self, func ):
        self.__name__ = func.__name__
        self.__doc__  = func.__doc__
        self.func     = func
        
        self.short_keys = {}
        
    def __call__(self, *args, **kwds):
        return self.func(*args, **kwds)
    
    def usage( self ):
        """
        Returns the usage string for this method.
        
        :return     <str>
        """
        args, varargs, keywords, defaults = inspect.getargspec(self.func)
        
        if ( not defaults ):
            defaults = []
        
        arg_list = ' '.join(args[:-len(defaults)]).upper()
        return '%s [options] %s %s' % (PROGRAM_NAME, self.__name__, arg_list)
    
    def parser( self ):
        """
        Creates a parser for the method based on the documentation.
        
        :return     <OptionParser>
        """
        usage = self.usage() + '\n' + str(self.__doc__)
        
        parser = PARSER_CLASS(usage = usage)
        
        args, varargs, keywords, defaults = inspect.getargspec(self.func)
        
        if ( defaults ):
            keymap      = args[-len(defaults):]
            processed   = ['h']
            
            for i, key in enumerate(keymap):
                if ( key in self.short_keys ):
                    short_key = self.short_keys[key]
                else:
                    letter      = 0
                    short       = key[letter]
                    not_found   = False
                    
                    while ( short in processed ):
                        letter += 1
                        if ( letter == len(key) ):
                            not_found = True
                            break
                            
                        short = key[letter]
                    
                    if ( not_found ):
                        short_key = ''
                    else:
                        processed.append(short)
                        short_key = '-%s' % short
                
                default = defaults[i]
                if ( default == True ):
                    action = 'store_false'
                elif ( default == False ):
                    action = 'store_true'
                else:
                    action = 'store'
                    
                
                parser.add_option(short_key, 
                                  '--%s' % key, 
                                  action = action,
                                  default = default)
        
        return parser
    
    def run( self, argv ):
        """
        Parses the inputed options and executes the method.
        
        :param      argv | [<str>, ..]
        """
        (opts, args)    = self.parser().parse_args(argv)
        func_args       = args[args.index(self.__name__)+1:]
        func_kwds       = opts.__dict__
        
        try:
            return self.__call__(*func_args, **func_kwds)
            
        except TypeError, e:
            logger.error(e)
            return 1

#-------------------------------------------------------------------------------

class Interface(object):
    def __init__( self, scope ):
        self._scope = scope
    
    def process( self, argv ):
        """
        Processes the inputed arguments within this object's scope.
        
        :return     <int>
        """
        return globals()['process'](argv, self._scope)

#-------------------------------------------------------------------------------

def command( argv, scope ):
    """
    Looks up a particular command from the inputed arguments for the given \
    scope.
    
    :param      argv    | [<str>, ..]
                scope   | <dict>
    
    :return     <climethod> || None
    """
    if ( inspect.ismodule(scope) ):
        scope = vars(scope)
    
    for cmd in scope.values():
        if ( not isinstance(cmd, climethod) ):
            continue
            
        if ( cmd.__name__ in argv ):
            return cmd
    return None

def commands( scope ):
    """
    Looks up all climethod instances from the inputed scope.
    
    :return     [<climethod>, ..]
    """
    if ( inspect.ismodule(scope) ):
        scope = vars(scope)
        
    return [cmd for cmd in scope.values() if isinstance(cmd, climethod)]

def generate( module ):
    """
    Generates a new interface from the inputed module.
    
    :param      module | <module>
    
    :return     <Interface>
    """
    scope = {}
    for value in vars(module).values():
        if ( inspect.isfunction(value) ):
            meth = climethod(value)
            scope[meth.__name__] = meth
        elif ( type(value) == climethod ):
            scope[value.__name__] = value
    
    return Interface(scope)
    
def parser( scope, usage = '' ):
    """
    Generates a default parser for the inputed scope.
    
    :param      scope    | <dict> || <module>
                usage    | <str>
                callable | <str>
    
    :return     <OptionParser>
    """
    subcmds = []
    for cmd in commands(scope):
        subcmds.append(cmd.usage())
    
    if ( subcmds ):
        subcmds.sort()
        usage += '\n\nSub-Commands:\n  '
        usage += '\n  '.join(subcmds)
    
    parser = PARSER_CLASS(usage = usage)
    parser.prog = PROGRAM_NAME
    return parser

def process( argv, scope ):
    """
    Processes any commands within the scope that matches the inputed arguments.
    If a subcommand is found, then it is run, and the system exists with the 
    return value from the command.
    
    :param      argv    | [<str>, ..]
                scope   | <dict>
    
    :return     (<dict> options, <tuple> arguments)
    """
    cmd = command(argv, scope)
    if ( cmd ):
        sys.exit(cmd.run(argv))
    
    _parser = parser(scope, '%prog [options] [<subcommand>] [<arg>]')
    options, args = _parser.parse_args(argv)
    return (options.__dict__, args)