""" Compiles and defines commonly used regular expressions. """

from .text import nativestring as nstr

# ------------------------------------------------------------------------------

EMAIL = r'^[\w\-_\.]+@\w+\.\w+$'
EMAIL_HELP = r'Requires email to contain only letters, numbers, ' \
             r'dashes, underscores, and periods.  Must be in the ' \
             r'format of "address@domain.type"'

PASSWORD = r'^[\w\.\-_@#$%^&+=]{5,10}$'
PASSWORD_HELP = r'Passwords must be between 5-10 characters long, contain ' \
                r'at least 1 letter, 1 number, and 1 special character, ' \
                r'like a period or underscore.'

DATETIME = r'(?P<month>\d{1,2})[\/\-\:\.](?P<day>\d{1,2})[\/\-\:\.]' \
           r'(?P<year>\d{2,4}) (?P<hour>\d{1,2})\:(?P<min>\d{2}):?' \
           r'(?P<second>\d{2})?\s?(?P<ap>[ap]m?)?'

DATE = r'(?P<month>\d{1,2})[\/\-\:\.](?P<day>\d{1,2})[\/\-\:\.]' \
       r'(?P<year>\d{2,4})'

TIME = r'(?P<hour>\d{1,2})\:(?P<min>\d{2})\:?' \
       r'(?P<second>\d{2})?\s?(?P<ap>[ap]m?)?'


def fromSearch(text):
    """
    Generates a regular expression from 'simple' search terms.
    
    :param      text | <str>
    
    :usage      |>>> import projex.regex
                |>>> projex.regex.fromSearch('*cool*')
                |'^.*cool.*$'
                |>>> projex.projex.fromSearch('*cool*,*test*')
                |'^.*cool.*$|^.*test.*$'
    
    :return     <str>
    """
    terms = []
    for term in nstr(text).split(','):
        # assume if no *'s then the user wants to search anywhere as keyword
        if '*' not in term:
            term = '*%s*' % term

        term = term.replace('*', '.*')
        terms.append('^%s$' % term)

    return '|'.join(terms)