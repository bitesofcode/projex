""" 
Defines the build setup errors.
"""

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

class XBuildError(StandardError):
    pass

# I
#----------------------------------------------------------------------

class InvalidBuildPath(XBuildError):
    def __init__(self, buildpath):
        msg = '{0} is not a valid build path'.format(buildpath)
        XBuildError.__init__(self, msg)