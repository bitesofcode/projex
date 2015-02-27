#!/usr/bin/python

""" Looks up resource files from the folder. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = ['Eric Hulser']
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

# define version information (major,minor,maintanence)
__depends__        = []
__version_info__   = (0, 0, 0)
__version__        = '%i.%i.%i' % __version_info__

#------------------------------------------------------------------------------

import os.path

BASE_PATH = os.path.dirname(__file__)

def find( relpath ):
    """
    Returns the resource based on the inputed relative path.
    
    :param      relpath  |  <str>
    
    :return     <str>
    """
    return os.path.join( BASE_PATH, relpath )