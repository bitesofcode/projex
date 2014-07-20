""" 
Defines a building system for Python code.  This combines documentation
generation, installer logic (using pyInstaller) and distribution
(using NSIS for windows) and setuptools for python installation structure.
"""

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

from .builder import *