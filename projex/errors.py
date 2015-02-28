""" Defines the common error classes used by the projex packages. """

import logging
import sys

from .text import nativestring as nstr

ERROR_MESSAGE = """\
%(levelname)s: %(type)s Error occurred:
    * logger: %(name)s
    * module: %(filename)s
    * from: %(pathname)s
    * function: %(funcName)s
    * exception info: %(exc_info)s

"""


class ProjexErrorHandler(logging.Handler):
    """ Custom class for handling error exceptions via the logging system,
        based on the logging level. """

    def emit(self, record):
        """ 
        Throws an error based on the information that the logger reported,
        given the logging level.
        
        :param      record: <logging.LogRecord>
        """
        if not logging.raiseExceptions:
            return

        logger = logging.getLogger(record.name)

        # raise an exception based on the error logging
        if logger.level <= record.levelno:
            err = record.msg[0]
            if not isinstance(err, Exception):
                err = ProjexError(nstr(record.msg))

            # log the traceback info
            data = record.__dict__.copy()
            data['type'] = type(err).__name__
            msg = ERROR_MESSAGE % data
            sys.stderr.write(msg)
            raise err


class ProjexError(StandardError):
    """ Base Error class for all projex errors. """
    pass


class ProjexWarning(Warning):
    """ Base Warning class for all projex warnings. """
    pass


# A
# ------------------------------------------------------------------------------

class AbstractMethodWarning(ProjexWarning):
    """ Thrown when an abstract method is attempted to be called. """
    pass


class AddonAlreadyExists(ProjexError):
    """ Raised when an addon is registered to the same scope in the AddonManager """

    def __init__(self, cls, name, addon):
        msg = 'Cannot register {0}.  {1} is already a registered key of {2}'
        msg = msg.format(addon, name, cls)
        super(AddonAlreadyExists, self).__init__(msg)


# D
#------------------------------------------------------------------------------

class DependencyNotFoundError(ProjexError):
    """ Thrown when a dependent module is attempted to be imported. """

    def __init__(self, dep):
        ProjexError.__init__(self, 'Missing dependency: %s' % dep)


class DeprecatedMethodWarning(ProjexWarning, DeprecationWarning):
    """ Thrown when a deprecated method is attempted to be called when in
        high debug mode. """
    pass


class DocumentationError(ProjexError):
    """ Thrown during the docgen process. """
    pass


# F
#------------------------------------------------------------------------------

class FilepathNotFoundError(ProjexError):
    """ Thrown when a filepath lookup is not found. """

    def __init__(self, filepath):
        msg = 'The filepath "%s" was not found.' % filepath
        ProjexError.__init__(self, msg)


class FileReadError(ProjexError):
    """ Thrown when reading a file is not successful. """

    def __init__(self, filepath):
        msg = '%s\nError reading file: "%s"' % filepath
        ProjexError.__init__(self, msg)


# I
#------------------------------------------------------------------------------

class ImproperXmlFormatError(ProjexError):
    """ Thrown when the XML file cannot be parsed. """

    def __init__(self, location):
        msg = '"%s" contains improperly formatted xml data.' % location
        ProjexError.__init__(self, msg)


class InvalidVersionDefinition(ProjexError):
    pass


# N
#------------------------------------------------------------------------------

class NotifyError(ProjexError):
    """ Thrown when the notification system fails. """

    def __init__(self, error):
        ProjexError.__init__(self, 'NotifyError: %s.\n\n' % error)


# P
#------------------------------------------------------------------------------

class PluginImportError(ProjexError):
    """ Thrown when a python plugin for one of the systems fails to load. """

    def __init__(self, module):
        err = 'Error importing plugin: %s' % module
        ProjexError.__init__(self, '\n\n'.join(err))
