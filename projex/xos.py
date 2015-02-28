"""
Provides additional cross platform functionality to the existing
python os module.
"""

import os
import sys


def appdataPath(appname):
    """
    Returns the generic location for storing application data in a cross
    platform way.
    
    :return     <str>
    """
    # determine Mac OS appdata location
    if sys.platform == 'darwin':
        # credit: MHL
        try:
            from AppKit import NSSearchPathForDirectoriesInDomains
            # NSApplicationSupportDirectory = 14
            # NSUserDomainMask = 1
            # True for expanding the tilde into a fully qualified path
            basepath = NSSearchPathForDirectoriesInDomains(14, 1, True)
            return os.path.join(basepath[0], appname)
        
        except (ImportError, AttributeError, IndexError):
            basepath = os.path.expanduser("~/Library/Application Support")
            return os.path.join(basepath, appname)
    
    # determine Windows OS appdata location
    elif sys.platform == 'win32':
        return os.path.join(os.environ.get('APPDATA'), appname)
    
    # determine Linux OS appdata location
    else:
        return os.path.expanduser(os.path.join('~', '.' + appname))