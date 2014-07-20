"""  """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# define global class mappers
EXTERNALS = {}
EXTERNALS['.*\.?Qt\w+\.(Q[A-Z].*)'] = 'http://qt-project.org/doc/qt-4.8/{0}.html'

from projex.docgen.project import *
from projex.docgen.pages import *
from projex.docgen.renderers import *