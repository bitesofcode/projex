"""
Defines a URL mapping system to control how the wiki text will handle different
URLs.
"""

import logging
from projex.text import nativestring as nstr

logger = logging.getLogger(__name__)


class UrlHandler(object):
    """ 
    Defines a url handler class that can be used when the wiki system
    attempts to render out a url.  It will take a wiki style key for a url 
    and lookup the proper http url to the target.
    """
    _current = None

    def __init__(self):
        self._rootUrl = ''
        self._staticUrl = ''
        self._replaceWikiSuffix = True

    def replaceWikiSuffix(self):
        """
        Returns whether or not the .wiki format should be replaced with a
        .html format.
        
        :return     <bool>
        """
        return self._replaceWikiSuffix

    # noinspection PyMethodMayBeStatic
    def resolve(self, key):
        """
        Resolves the inputted wiki key to a url path.  This method should \
        return a url and whether or not the page exists.
        
        :param      key     | <str>
        
        :return     (<str> url, <bool> exists)
        """
        logger.debug('Key not found: ', key)
        return '', False

    # noinspection PyMethodMayBeStatic
    def resolveClass(self, cls):
        """
        Resolves a pointer to a class reference - this will be in the form
        of <package>.<className> and should return the documentation for the
        module and class.
        
        :param      cls | <str>
        
        :return     <str>
        """
        logger.debug('Class not found', cls)
        return '', False

    # noinspection PyMethodMayBeStatic
    def resolveImage(self, key):
        """
        Resolves the image path for the inputted key to a valid URL.
        
        :param      key | <str>
        
        :return     (<str> url, <bool> exists)
        """
        logger.debug('Key not found', key)
        return '', False

    def rootUrl(self):
        """
        Returns the root url for the handler.
        
        :return     <str>
        """
        return self._rootUrl

    def staticUrl(self):
        """
        Returns the static url for this handler.
        
        :return     <str>
        """
        if not self._staticUrl:
            return self._rootUrl + '/_static'
        return self._staticUrl

    def setCurrent(self):
        """
        Sets this handler as the current global instance.
        """
        UrlHandler._current = self

    def setReplaceWikiSuffix(self, state):
        """
        Sets whether or not the .wiki format should be replaced with a
        .html format.
        
        :param      state | <bool>
        """
        self._replaceWikiSuffix = state

    def setRootUrl(self, url):
        """
        Sets the root url for the url handler to the inputted url.
        
        :param      url | <str>
        """
        self._rootUrl = nstr(url)

    def setStaticUrl(self, url):
        """
        Sets the static url for the handler to the inputted url.
        
        :param      url | <str>
        """
        self._staticUrl = nstr(url)

    @staticmethod
    def current():
        """
        Returns the current global url handler.
        
        :return     <UrlHandler>
        """
        if not UrlHandler._current:
            UrlHandler._current = UrlHandler()
        return UrlHandler._current
