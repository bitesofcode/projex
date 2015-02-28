""" 
Defines a building system for Python code.  This combines documentation
generation, installer logic (using pyInstaller) and distribution
(using NSIS for windows) and setuptools for python installation structure.
"""

from .builder import *