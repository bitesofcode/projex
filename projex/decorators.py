""" Defines reusable base method decorators to be used throughout projex """

try:
    from functools import wraps
except ImportError:
    def wraps(func):
        return func

import hotshot
import hotshot.stats
import inspect
import os
import logging
import time

import projex
from projex import errors

# create the logger
logger = logging.getLogger(__name__)

# A
# ------------------------------------------------------------------------------


def abstractmethod(classname='', info=''):
    """
    Defines a particular method as being abstract.  Abstract methods are used \
    to define interfaces to classes, but signal developers that to use a \
    particular method, the class needs to be sub-classed and modified.
                
    :usage      |from projex.decorators import abstractmethod
                |
                |class A(object):
                |   @abstractmethod('A')
                |   def format( self ):
                |       print 'test'
                |
                |   def printout( self ):
                :       print 'new test'
    """

    def decorated(func):
        # noinspection PyUnusedLocal
        @wraps(func)
        def wrapped(*args, **kwds):
            frame = last_frame = None
            try:
                frame = inspect.currentframe()
                last_frame = frame.f_back
                fname = last_frame.f_code.co_filename
                func_file = func.func_code.co_filename

                opts = {
                    'func': func.__name__,
                    'line': last_frame.f_lineno,
                    'file': fname,
                    'class': classname,
                    'info': info,
                    'package': projex.packageFromPath(func_file),
                }

                msg = 'Abstract method called from %(file)s, line %(line)d.' \
                      '\n  %(package)s.%(class)s.%(func)s is abstract.' \
                      '  %(info)s' % opts

                raise NotImplementedError(msg)

            finally:
                del frame
                del last_frame

        wrapped.__name__ = getattr(func, '__name__', '')
        wrapped.__doc__ = ':warning  This method is abstract!  %s\n\n' % info
        if func.__doc__:
            wrapped.__doc__ += func.__doc__

        wrapped.__dict__.update(func.__dict__)
        wrapped.__dict__['func_type'] = 'abstract method'

        return wrapped

    return decorated


# D
# ------------------------------------------------------------------------------

def deprecatedmethod(classname='', info=''):
    """
    Defines a particular method as being deprecated - the 
    method will exist for backwards compatibility, but will 
    contain information as to how update code to become 
    compatible with the current system.
                
    Code that is deprecated will only be supported through the 
    end of a minor release cycle and will be cleaned during a 
    major release upgrade.
    
    :usage      |from projex.decorators import deprecated
                |
                |class A(object):
                |   @deprecatedmethod('A', 'Use A.printout instead')
                |   def format( self ):
                |       print 'test'
                |
                |   def printout( self ):
                :       print 'new test'
    """

    def decorated(func):
        @wraps(func)
        def wrapped(*args, **kwds):
            frame = last_frame = None
            try:
                frame = inspect.currentframe()
                last_frame = frame.f_back
                fname = last_frame.f_code.co_filename
                func_file = func.func_code.co_filename

                opts = {
                    'func': func.__name__,
                    'line': last_frame.f_lineno,
                    'file': fname,
                    'class': classname,
                    'info': info,
                    'package': projex.packageFromPath(func_file)
                }

                msg = 'Deprecated method called from %(file)s, line %(line)d.' \
                      '\n  %(package)s.%(class)s.%(func)s is deprecated.' \
                      '  %(info)s' % opts

                logger.warning(errors.DeprecatedMethodWarning(msg))

            finally:
                del frame
                del last_frame

            return func(*args, **kwds)

        wrapped.__name__ = func.__name__

        wrapped.__doc__ = ':warning  This method is deprecated!  %s\n\n' % info
        if func.__doc__:
            wrapped.__doc__ += func.__doc__

        wrapped.__dict__.update(func.__dict__)
        wrapped.__dict__['func_type'] = 'deprecated method'

        return wrapped

    return decorated


# P
# -----------------------------------------------------------------------------

def profiler(sorting=('tottime',), stripDirs=True,
             limit=20, path='', autoclean=True):
    """
    Creates a profile wrapper around a method to time out 
    all the  operations that it runs through.  For more 
    information, look into the hotshot Profile documentation 
    online for the built-in Python package.
    
    :param      sorting     <tuple> ( <key>, .. )
    :param      stripDirs   <bool>
    :param      limit       <int>
    :param      path        <str>
    :param      autoclean   <bool>
    
    :usage      |from projex.decorators import profiler
                |
                |class A:
                |   @profiler() # must be called as a method
                |   def increment(amount, count = 1):
                |       return amount + count
                |
                |a = A()
                |a.increment(10)
                |
    """

    def decorated(func):
        """ Wrapper function to handle the profiling options. """
        # create a call to the wrapping
        @wraps(func)
        def wrapped(*args, **kwds):
            """ Inner method for calling the profiler method. """
            # define the profile name
            filename = os.path.join(path, '%s.prof' % func.__name__)

            # create a profiler for the method to run through
            prof = hotshot.Profile(filename)
            results = prof.runcall(func, *args, **kwds)
            prof.close()

            # log the information about it
            stats = hotshot.stats.load(filename)

            if stripDirs:
                stats.strip_dirs()

            # we don't want to know about the arguments for this method
            stats.sort_stats(*sorting)
            stats.print_stats(limit)

            # remove the file if desired
            if autoclean:
                os.remove(filename)

            return results

        return wrapped

    return decorated


# R
# -----------------------------------------------------------------------------


def retrymethod(count, sleep=0):
    """
    Defines a decorator method to wrap a method with a retry mechanism.  The
    wrapped method will be attempt to be called the given number of times based
    on the count value, waiting the number of seconds defined by the sleep
    parameter.  If the throw option is defined, then the given error will
    be thrown after the final attempt fails.
    
    :param      count | <int>
                sleep | <int> | msecs
    """

    def decorated(func):
        @wraps(func)
        def wrapped(*args, **kwds):
            # do the retry options
            for i in range(count - 1):
                try:
                    return func(*args, **kwds)
                except StandardError:
                    pass

                if sleep:
                    time.sleep(sleep)

            # run as standard
            return func(*args, **kwds)

        return wrapped

    return decorated