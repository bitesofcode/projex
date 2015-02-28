""" Looks up resource files from the folder. """

import os.path

BASE_PATH = os.path.dirname(__file__)


def find(relpath):
    """
    Returns the resource based on the inputted relative path.
    
    :param      relpath  |  <str>
    
    :return     <str>
    """
    return os.path.join(BASE_PATH, relpath)