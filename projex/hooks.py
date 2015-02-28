"""
The hooks module will provide an API to assigning multiple hooks to
Python's internal exception and logging calls.  This will utilize the
sys.excepthook method, and override the sys.stdout instance with a
printer wrapper while providing a queue based call to processing events.

Similar to the logging handling system, except works with the unknown
exceptions and printed values as well.

:usage      |>>> from projex import hooks
            |>>> def email_error(cls, error, trace):
            |...    error = hooks.formatExcept(cls, error, trace)
            |...    notify.sendEmail('me@domain.com',
            |...                     ['error@domain.com'],
            |...                     'Error Occurred',
            |...                     error)
            |>>> from xqt import QtGui
            |>>> def message_error(cls, error, trace):
            |...    QtGui.QMessageBox.critical(None, 'Error', error)
            |>>> # register exceptions
            |>>> hooks.messageExcept(message_error)
            |>>> hooks.registerExcept(email_error)
"""

import weakref
import sys
import traceback

_displayhooks = None
_excepthooks = None


class StreamHooks(object):
    """
    Basic class to wrap the sys stream system.
    """

    def __getattr__(self, key):
        try:
            return getattr(self.stream, key)
        except AttributeError:
            return getattr(sys.__stdout__, key)

    def __init__(self, stream):
        self.hooks = []
        self.stream = stream

    def write(self, text):
        new_hooks = []
        for hook_ref in self.hooks:
            hook = hook_ref()
            if hook:
                hook(text)
                new_hooks.append(hook_ref)

        self.hooks = new_hooks

        # write to the original stream
        try:
            self.stream.write(text)
        except StandardError:
            pass


# ----------------------------------------------------------------------

def displayhook(value):
    """
    Runs all of the registered display hook methods with the given value.
    Look at the sys.displayhook documentation for more information.
    
    :param      value | <variant>
    """
    global _displayhooks
    new_hooks = []

    for hook_ref in _displayhooks:
        hook = hook_ref()
        if hook:
            hook(value)
            new_hooks.append(hook_ref)

    _displayhooks = new_hooks

    sys.__displayhook__(value)


def excepthook(cls, error, trace):
    """
    Runs all of the registered exception hook methods with the given value.
    Look at the sys.excepthook documentation for more information.
    
    :param      cls     | <type>
                error   | <str>
                trace   | <traceback>
    """
    global _excepthooks
    new_hooks = []

    for hook_ref in _excepthooks:
        hook = hook_ref()
        if hook:
            hook(cls, error, trace)
            new_hooks.append(hook_ref)

    _excepthook = new_hooks
    sys.__excepthook__(cls, error, trace)


def formatExcept(cls, error, trace):
    """
    Formats the inputted class, error, and traceback information to the standard
    output commonly found in Python interpreters.
    
    :param      cls     | <type>
                error   | <str>
                trace   | <traceback>
    
    :return     <str>
    """
    clsname = cls.__name__ if cls else 'UnknownError'
    tb = 'Traceback (most recent call last):\n'
    tb += ''.join(traceback.format_tb(trace))
    tb += '{0}: {1}'.format(clsname, error)
    return tb


def registerDisplay(func):
    """
    Registers a function to the display hook queue to be called on hook.
    Look at the sys.displayhook documentation for more information.
    
    :param      func | <callable>
    """
    setup()
    ref = weakref.ref(func)
    if ref not in _displayhooks:
        _displayhooks.append(ref)


def registerExcept(func):
    """
    Registers a function to the except hook queue to be called on hook.
    Look at the sys.displayhook documentation for more information.
    
    :param      func | <callable>
    """
    setup()
    ref = weakref.ref(func)
    if ref not in _excepthooks:
        _excepthooks.append(ref)


def registerStdErr(func):
    """
    Registers a function to the print hook queue to be called on hook.
    This method will also override the current sys.stdout variable with a new
    <StreamHooks> instance.  This will preserve any current sys.stdout 
    overrides while providing a hookable class for linking multiple methods to.
    
    :param      func | <callable>
    """
    if not isinstance(sys.stderr, StreamHooks):
        sys.stderr = StreamHooks(sys.stderr)

    ref = weakref.ref(func)
    if ref not in sys.stderr.hooks:
        sys.stderr.hooks.append(ref)


def registerStdOut(func):
    """
    Registers a function to the print hook queue to be called on hook.
    This method will also override the current sys.stdout variable with a new
    <StreamHooks> instance.  This will preserve any current sys.stdout 
    overrides while providing a hookable class for linking multiple methods to.
    
    :param      func | <callable>
    """
    if not isinstance(sys.stdout, StreamHooks):
        sys.stdout = StreamHooks(sys.stdout)

    ref = weakref.ref(func)
    if ref not in sys.stdout.hooks:
        sys.stdout.hooks.append(ref)


def setup():
    """
    Initializes the hook queues for the sys module.  This method will
    automatically be called on the first registration for a hook to the system
    by either the registerDisplay or registerExcept functions.
    """
    global _displayhooks, _excepthooks
    if _displayhooks is not None:
        return

    _displayhooks = []
    _excepthooks = []

    # store any current hooks
    if sys.displayhook != sys.__displayhook__:
        _displayhooks.append(weakref.ref(sys.displayhook))

    if sys.excepthook != sys.__excepthook__:
        _excepthooks.append(weakref.ref(sys.excepthook))

    # replace the current hooks
    sys.displayhook = displayhook
    sys.excepthook = excepthook


def unregisterDisplay(func):
    """
    Un-registers a function from the display hook queue.
    Look at the sys.displayhook documentation for more information.
    
    :param      func | <callable>
    """
    try:
        _displayhooks.remove(weakref.ref(func))
    except ValueError:
        pass


def unregisterExcept(func):
    """
    Un-registers a function from the except hook queue.
    Look at the sys.displayhook documentation for more information.
    
    :param      func | <callable>
    """
    try:
        _excepthooks.remove(weakref.ref(func))
    except (AttributeError, ValueError):
        pass


def unregisterStdErr(func):
    """
    Un-registers a function from the print hook queue.
    Look at the sys.displayhook documentation for more information.
    
    :param      func | <callable>
    """
    try:
        sys.stderr.hooks.remove(weakref.ref(func))
    except (AttributeError, ValueError):
        pass


def unregisterStdOut(func):
    """
    Un-registers a function from the print hook queue.
    Look at the sys.displayhook documentation for more information.
    
    :param      func | <callable>
    """
    try:
        sys.stdout.hooks.remove(weakref.ref(func))
    except (AttributeError, ValueError):
        pass
