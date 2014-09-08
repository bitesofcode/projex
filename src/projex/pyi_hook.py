""" Defines the hook required for the PyInstaller to use projex with it. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'

__all__ = ['hiddenimports', 'datas']

import os
import projex.pyi

hiddenimports, datas = projex.pyi.collect(os.path.dirname(__file__))
hiddenimports.append('smtplib')