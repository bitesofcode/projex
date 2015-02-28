
class MultiContext(object):
    """ Support entering and exiting of multiple python contexts """
    def __init__(self, *contexts):
        self._contexts = contexts

    def __enter__(self):
        for context in self._contexts:
            context.__enter__()

    def __exit__(self, *args):
        for context in self._contexts:
            context.__exit__(*args)