""" Defines commonly used sorting methods for lists. """

import re
from .text import nativestring as nstr

EXPR_NATURAL = re.compile('([^\d]*)(\d*)')
EXPR_VERSIONAL = re.compile('([^\d]*)([\.]?\d*)')


def natural(a, b):
    """
    Sorts the inputted items by their natural order, trying to extract a \
    number from them to sort by.
    
    :param      a       <str>
                b       <str>
    
    :return     <int> 1 || 0 || -1
    
    :usage      |>>> from projex import sorting
                |>>> a = [ 'test1', 'test2', 'test10', 'test20', 'test09' ]
                |>>> a.sort()
                |>>> print a
                |['test09', 'test1', 'test10', 'test2', 'test20']
                |>>> a.sort( sorting.natural )
                |>>> print a
                |['test1', 'test2', 'test09', 'test10', 'test20']
    """
    stra = nstr(a).lower()
    strb = nstr(b).lower()

    # test to see if the two are identical
    if stra == strb:
        return 0

    # look up all the pairs of items
    aresults = EXPR_NATURAL.findall(stra)
    bresults = EXPR_NATURAL.findall(strb)

    # make sure we have the same number of results
    bcount = len(bresults)
    for i in range(len(aresults)):
        # make sure we don't exceed the number of elements in b
        if bcount <= i:
            break

        atext, anum = aresults[i]
        btext, bnum = bresults[i]

        # compare the text components
        if atext != btext:
            return cmp(atext, btext)

        if not anum:
            anum = 0
        if not bnum:
            bnum = 0

        # compare the numeric components
        anum = int(anum)
        bnum = int(bnum)
        if anum != bnum:
            return cmp(anum, bnum)

    # b has less characters than a, so should sort before
    return 1


def versional(a, b):
    """
    Sorts the inputted items by their natural order, trying to extract a \
    number from them to sort by.
    
    :param      a       <str>
                b       <str>
    
    :return     <int> 1 || 0 || -1
    
    :usage      |>>> from projex import sorting
                |>>> a = [ 'test-1.1.2', 'test-1.02', 'test-1.2', 'test-1.18' ]
                |>>> a.sort()
                |>>> print a
                |['test-1.02', 'test-1.1.2', 'test-1.18', 'test-1.2']
                |>>> a.sort( sorting.natural )
                |>>> print a
                |['test-1.1.2', 'test-1.02', 'test-1.2', 'test-1.18']
                |>>> a.sort( sorting.versional )
                |>>> print a
                |['test-1.1.2', 'test-1.02', 'test-1.18', 'test-1.2']
    """
    stra = nstr(a).lower()
    strb = nstr(b).lower()

    # look up all the pairs of items
    aresults = EXPR_VERSIONAL.findall(stra)
    bresults = EXPR_VERSIONAL.findall(strb)

    # make sure we have the same number of results
    bcount = len(bresults)
    for i in range(len(aresults)):
        # make sure we don't exceed the number of elements in b
        if bcount <= i:
            break

        atext, anum = aresults[i]
        btext, bnum = bresults[i]

        # compare the text components
        if atext != btext:
            return cmp(atext, btext)

        if not anum:
            anum = 0
        if not bnum:
            bnum = 0

        # compare the numeric components
        if atext == '.':
            anum = int(float('.' + anum) * 10000)
            bnum = int(float('.' + bnum) * 10000)
        else:
            anum = int(anum)
            bnum = int(bnum)

        if anum != bnum:
            return cmp(anum, bnum)

    # b has less characters than a, so should sort before
    return 1