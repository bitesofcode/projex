"""
Defines useful thread locks.  Credit for this code goes to:

http://code.activestate.com/recipes/577803-reader-writer-lock-with-priority-for-writers/
"""

import datetime
import logging
import threading

log = logging.getLogger(__name__)


class _MutexSwitcher(object):
    """An auxiliary "light switch"-like object. The first thread turns on the
    "switch", the last one turns it off (see [1, sec. 4.2.2] for details)."""
    def __init__(self):
        self.__counter = 0
        self.__mutex = threading.Lock()

    def acquire(self, lock):
        self.__mutex.acquire()
        self.__counter += 1
        if self.__counter == 1:
            lock.acquire()
        self.__mutex.release()

    def release(self, lock):
        self.__mutex.acquire()
        self.__counter -= 1
        if self.__counter == 0:
            lock.release()
        self.__mutex.release()


class ReadWriteLock(object):
    """
    Allow for Read/Write locks which will allow multiple read access with only a single
    """
    def __init__(self):
        self.__read_switch = _MutexSwitcher()
        self.__write_switch = _MutexSwitcher()
        self.__no_readers = threading.Lock()
        self.__no_writers = threading.Lock()
        self.__readers_queue = threading.Lock()
        """A lock giving an even higher priority to the writer in certain
        cases (see [2] for a discussion)"""
    
    def reader_acquire(self):
        self.__readers_queue.acquire()
        self.__no_readers.acquire()
        self.__read_switch.acquire(self.__no_writers)
        self.__no_readers.release()
        self.__readers_queue.release()
    
    def reader_release(self):
        self.__read_switch.release(self.__no_writers)
    
    def writer_acquire(self):
        self.__write_switch.acquire(self.__no_readers)
        self.__no_writers.acquire()
    
    def writer_release(self):
        self.__no_writers.release()
        self.__write_switch.release(self.__no_readers)


class ReadLocker(object):
    def __init__(self, lock):
        self._lock = lock

    def __enter__(self):
        self._lock.reader_acquire()

    def __exit__(self, *args):
        self._lock.reader_release()


class WriteLocker(object):
    def __init__(self, lock, delay=None):
        self._lock = lock

    def __enter__(self):
        start = datetime.datetime.now()
        self._lock.writer_acquire()

    def __exit__(self, *args):
        self._lock.writer_release()