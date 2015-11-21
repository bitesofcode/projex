"""
Function editing utilities
"""

def extract_keywords(func):
    """
    Parses the keywords from the given function.

    :param      func | <function>
    """
    if hasattr(func, 'im_func'):
        func = func.im_func

    try:
        return func.func_code.co_varnames[-len(func.func_defaults):]
    except (TypeError, ValueError, IndexError):
        return tuple()