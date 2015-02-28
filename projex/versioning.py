""" Defines common and useful methods for version comparison. """

import re

from .sorting import natural as vercmp
from . import errors


def validate(version, comparison):
    """
    Returns whether or not the version for this plugin satisfies the
    inputted expression.  The expression will follow the dependency
    declaration rules associated with setuptools in Python.  More
    information can be found at
    
    [https://pythonhosted.org/setuptools/setuptools.html#declaring-dependencies]
    
    :param      version     | <str>
                expression  | <str>
    
    :return     <bool>
    """
    # match any
    if not comparison:
        return True
    
    # loop through all available
    opts = comparison.split(',')
    expr = re.compile('(==|!=|<=|>=|<|>)(.*)')
    for opt in opts:
        try:
            test, value = expr.match(opt.strip()).groups()
        except StandardError:
            raise errors.InvalidVersionDefinition(opt)
        
        value = value.strip()
        
        # test for an exact match
        if test == '==':
            if value == version:
                return True
        
        # test for negative exact matches
        elif test == '!=':
            if value == version:
                return False
        
        # test for range conditions
        elif test == '<':
            if vercmp(version, value) != -1:
                return False
        elif test == '<=':
            if vercmp(version, value) not in (-1, 0):
                return False
        elif test == '>':
            if vercmp(value, version) != -1:
                return False
        elif test == '>=':
            if vercmp(value, version) not in (-1, 0):
                return False
    
    return True