""" 
Defines the builder class for building versions.
"""

# define authorship information
__authors__ = ['Eric Hulser']
__author__ = ','.join(__authors__)
__credits__ = []
__copyright__ = 'Copyright (c) 2011-2016'
__license__ = 'MIT'

__maintainer__ = 'Eric Hulser'
__email__ = 'eric.hulser@gmail.com'

if __name__ == '__main__':
    import logging

    # setup the logging information
    logging.basicConfig()
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    # run the build system with command line arguments
    from projex.xbuild.builder import build_cmd

    build_cmd()

