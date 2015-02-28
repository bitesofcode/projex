# encoding: latin-1

""" Module for managing money information. """

import locale
import re
import urllib2

from .text import nativestring as nstr

_expr = re.compile('^(?P<symbol>[^\w\d-])?(?P<amount>[-\d,]+\.?\d*)\s*(?P<currency>.*)$')

_inited = False

DEFAULT = locale.getdefaultlocale()[0].split('_')[-1].lower()

SYMBOLS = {
    'USD': '$',
    'PND': '£',
    'JPY': '¥'
}

# basic info...use lookup to adjust for online usage
CURRENCIES = {
    'au': ('Australia', 'AUD'),
    'gb': ('Great Britain', 'PND'),
    'eu': ('European Union', 'EUR'),
    'jp': ('Japan', 'JPY'),
    'us': ('United States', 'USD'),
}


def currencies():
    """
    Returns a dictionary of currencies from the world.
    
    :return     {<str> geoname: (<str> country, <str> code), ..}
    """
    init()
    return CURRENCIES.copy()


def fromString(money):
    """
    Returns the amount of money based on the inputted string.
    
    :param      money   | <str>
    
    :return     (<double> amount, <str> currency)
    """
    result = _expr.match(money)
    if not result:
        return 0, DEFAULT

    data = result.groupdict()

    amount = float(data['amount'].replace(',', ''))

    if data['currency']:
        return amount, data['currency']

    # noinspection PyShadowingNames
    symbol = data['symbol']
    for key, value in SYMBOLS.items():
        if symbol == value:
            return amount, key

    return amount, DEFAULT


def init():
    """
    Initializes the currency list from the internet.
    
    :sa     lookup
    
    :return     <bool> | success
    """
    global _inited
    if _inited:
        return

    codes = lookup()
    if codes:
        _inited = True
        CURRENCIES.update(codes)
        return True
    return False


def lookup():
    """
    Initializes the global list of currencies from the internet
    
    :return     {<str> geoname: (<str> country, <str> symbol), ..}
    """
    global CURRENCIES
    url = 'http://download.geonames.org/export/dump/countryInfo.txt'
    try:
        data = urllib2.urlopen(url)
    except StandardError:
        return {}

    ccodes = {}
    for line in data.read().split('\n'):
        if line.startswith('#'):
            continue

        line = line.split('\t')
        try:
            geoname = line[0].lower()
            code = line[10]
            country = line[4]
        except IndexError:
            continue

        if not code:
            continue

        ccodes[geoname] = (country, code)

    return ccodes


# noinspection PyShadowingNames
def toString(amount, currency=None, rounded=None):
    """
    Converts the inputted amount of money to a string value.
    
    :param      amount         | <bool>
                currency       | <str>
                rounded        | <bool> || None
    
    :return     <str>
    """
    init()

    if currency is None:
        currency = DEFAULT

    if currency in CURRENCIES:
        symbol = SYMBOLS.get(CURRENCIES[currency][1])
    else:
        symbol = SYMBOLS.get(currency, '')

    # insert meaningful commas
    astr = nstr(int(abs(amount)))
    alen = len(astr)

    if len(astr) > 3:
        arange = range(alen, -1, -3)
        parts = reversed([astr[i - 3:i] for i in arange])
        astr = astr[:alen % 3] + ','.join(parts)
        astr = astr.strip(',')

    if amount < 0:
        astr = '-' + astr

    # use & force decimals when necessary
    if (amount % 1 or rounded is False) and rounded is True:
        astr += ('%0.2f' % (amount % 1)).lstrip('0')

    if not symbol:
        return astr + ' ' + CURRENCIES.get(currency, ('', ''))[1]

    return symbol + astr


def symbol(currency):
    """
    Returns the monetary symbol used for the given currency.
    
    :param      currency | <str.
    
    :return     <str>
    """
    init()
    if currency in CURRENCIES:
        return SYMBOLS.get(CURRENCIES[currency][1], '')
    return SYMBOLS.get(currency, '')