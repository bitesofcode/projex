"""
Defines iteration utilities
"""

import itertools


def batch(iterable, length):
    """
    Returns a series of iterators across the inputted iterable method,
    broken into chunks based on the inputted length.
    
    :param      iterable | <iterable>  | (list, tuple, set, etc.)
                length   | <int> 
    
    :credit    http://en.sharejs.com/python/14362
    
    :return     <generator>
    
    :usage      |>>> import projex.iters
                |>>> for batch in projex.iters.batch(range(100), 10):
                |...    print list(batch)
                |[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
                |[10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
                |[20, 21, 22, 23, 24, 25, 26, 27, 28, 29]
                |[30, 31, 32, 33, 34, 35, 36, 37, 38, 39]
                |[40, 41, 42, 43, 44, 45, 46, 47, 48, 49]
                |[50, 51, 52, 53, 54, 55, 56, 57, 58, 59]
                |[60, 61, 62, 63, 64, 65, 66, 67, 68, 69]
                |[70, 71, 72, 73, 74, 75, 76, 77, 78, 79]
                |[80, 81, 82, 83, 84, 85, 86, 87, 88, 89]
                |[90, 91, 92, 93, 94, 95, 96, 97, 98, 99]
    """
    source_iter = iter(iterable)
    while True:
        batch_iter = itertools.islice(source_iter, length)
        yield itertools.chain([batch_iter.next()], batch_iter)


def group(iterable):
    """
    Creates a min/max grouping for the inputted list of numbers.  This
    will shrink a list into the group sets that are available.
    
    :param      iterable | <iterable> | (list, tuple, set, etc.)
    
    :return     <generator> [(<int> min, <int> max), ..]
    """
    numbers = sorted(list(set(iterable)))
    for _, grouper in itertools.groupby(numbers, key=lambda i, c=itertools.count(): i - next(c)):
        subset = list(grouper)
        yield subset[0], subset[-1]

