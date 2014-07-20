#!/usr/bin/python

""" Generic signal/slot callback system. """

# define authorship information
__authors__         = ['Eric Hulser']
__author__          = ','.join(__authors__)
__credits__         = []
__copyright__       = 'Copyright (c) 2011, Projex Software'
__license__         = 'LGPL'

# maintanence information
__maintainer__      = 'Projex Software'
__email__           = 'team@projexsoftware.com'
__all__             = [ 'abstractmethod', 'deprecatedmethod', 'profiler' ]

import inspect
import logging
import weakref

logger = logging.getLogger(__name__)

class Callback(object):
    def __init__(self, slot):
        self._callback_func_ref = None
        self._callback_self_ref = None
        
        if inspect.ismethod(slot):
            self._callback_func_ref = weakref.ref(slot.im_func)
            self._callback_self_ref = weakref.ref(slot.im_self)
        else:
            self._callback_func_ref = weakref.ref(slot)
    
    def __eq__(self, other):
        ref_cmp = (None, None)
        
        if isinstance(other, Callback):
            ref_cmp = (other._callback_func_ref, other._callback_self_ref)
        
        elif inspect.ismethod(other):
            ref_cmp = (weakref.ref(other.im_func), weakref.ref(other.im_self))
        
        else:
            ref_cmp = (weakref.ref(other), -1)
        
        return (self._callback_func_ref, self._callback_self_ref) == ref_cmp
    
    def __call__(self, *args):
        """
        Calls this callback with the inputed arguments by accessing its stored
        callback function and self arguments.
        
        :param      *args | <variant>
        """
        if self._callback_func_ref is None:
            return
        
        callback_func = self._callback_func_ref()
        
        # call a reference with a pointer
        if self._callback_self_ref is not None:
            callback_self = self._callback_self_ref()
            if callback_self is None:
                return
            
            return callback_func(callback_self, *args)
        else:
            return callback_func(*args)
    
    def isValid(self):
        """
        Checks to see if the callback pointers are still valid or not.
        
        :return     <bool>
        """
        if self._callback_func_ref is not None and self._callback_func_ref():
            if self._callback_self_ref is None or self._callback_self_ref():
                return True
        return False

#----------------------------------------------------------------------

class CallbackSet(object):
    def __init__(self):
        self._callbacks = {}
    
    def callbacks(self, signal):
        """
        Returns a list of the callbacks associated with a given key.
        
        :param      signal | <variant>
        
        :return     [<Callback>, ..]
        """
        return self._callbacks.get(signal, [])
    
    def clear(self, signal=None):
        """
        Clears either all the callbacks or the callbacks for a particular
        signal.
        
        :param      signal | <variant> || None
        """
        if signal is not None:
            self._callbacks.pop(signal, None)
        else:
            self._callbacks.clear()
    
    def connect(self, signal, slot):
        """
        Creates a new connection between the inputed signal and slot.
        
        :param      signal | <variant>
                    slot   | <callable>
        
        :return     <bool> | new connection created
        """
        if self.isConnected(signal, slot):
            return False
        
        callback = Callback(slot)
        self._callbacks.setdefault(signal, [])
        self._callbacks[signal].append(callback)
        return True
    
    def disconnect(self, signal, slot):
        """
        Breaks the connection between the inputed signal and the given slot.
        
        :param      signal | <variant>
                    slot   | <callable>
        
        :return     <bool> | connection broken
        """
        sig_calls = self._callbacks.get(signal, [])
        for callback in sig_calls:
            if callback == slot:
                sig_calls.remove(callback)
                return True
        return False
    
    def isConnected(self, signal, slot):
        """
        Returns if the given signal is connected to the inputed slot.
        
        :param      signal | <variant>
                    slot   | <callable>
        
        :return     <bool> | is connected
        """
        sig_calls = self._callbacks.get(signal, [])
        for callback in sig_calls:
            if callback == slot:
                return True
        return False
    
    def emit(self, signal, *args):
        """
        Emits the given signal with the inputed args.  This will go through
        its list of connected callback slots and call them.
        
        :param      signal | <variant>
                    *args  | variables
        """
        callbacks = self._callbacks.get(signal, [])
        new_callbacks = []
        for callback in callbacks:
            # clear out deleted pointers
            if not callback.isValid():
                continue
            
            new_callbacks.append(callback)
            
            try:
                callback(*args)
            except:
                logger.exception('Error occurred during callback.')
        
        self._callbacks[signal] = new_callbacks