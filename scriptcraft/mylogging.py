#!/usr/bin/env python
#-*- coding:utf-8 -*-


"""Simple wrapper for logging module.

To initialize, call init_logging. At the end call shutdown_logging.

The module provide timing (see log_on_enter function).
"""


__all__ = [
    'init_logging',
    'log',
    'log_exception',
    'log_on_enter',
    'log_error_callback',
    'shutdown_logging',
]


from collections import defaultdict
from functools import partial, wraps
import logging
import logging.handlers
import time as time_module



LOGGING_FORMAT = ('%(asctime)-15s  '
                  '%(levelname)-9s '
                  '%(message)s')
LOG_INDENT_PATTERN = '   '
LOG_FILENAME = '.scriptcraft.log'


_initialisated = False


def init_logging(lvl='info'):
    """ Init logging. Log in file and on console."""
    global _indent_depth, _timing_data, _initialisated
    _indent_depth = 0

    lvl = _validate_level(lvl)
    if lvl == logging.DEBUG:
        _timing_data = defaultdict(list) # { string key : list of executing times }
    else:
        _timing_data = None
    logger = logging.getLogger('')
    logger.setLevel(lvl)
    formatter = logging.Formatter(LOGGING_FORMAT)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=LOG_FILENAME,
        maxBytes=1024*1024,
        mode='a',
        backupCount=2)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    _initialisated = True

    log('STARTING APPLICATION', lvl='info')


def log_error_callback(cls, ex, traceback):
    """ Special handler for tkinter.

    Using:
    >>> root = Tk()
    >>> root.report_callback_exception = log_error_callback

    """

    log_exception("unhandled exception!")


def log_exception(title="Exception!"):
    global _initialisated
    if _initialisated:
        logging.exception(title)


def log(msg, lvl='debug'):
    global _initialisated
    if _initialisated:
        _log(_validate_level(lvl), msg, '')


def log_on_enter(msg, lvl='debug', mode='log'):
    """ Decorator and context manager.

    Optional argument 'mode' can be 'log', 'time' or 'only time'.

    - If mode is 'only time', no logging message is created.

    - If mode is 'time' or 'only time' and logging was initialized
    with debug level then calling shutdown_logging provides some data
    about time consumed by decorated function or wrapped code by with
    statement.

    """

    assert mode in ('log', 'time', 'only time')

    level = _validate_level(lvl)
    time = mode in ('time', 'only time')
    log_this = mode in ('log', 'time')

    class result(object):
        def __enter__(self): # context manager use case
            global _indent_depth, _initialisated
            if _initialisated:
                if log_this:
                    _log(level, msg)
                    _indent_depth += 1
                if time:
                    self.started_time = time_module.time()

        def __exit__(self, *args): # context manager use case
            # args is [type, value, traceback] or []
            global _indent_depth, _timing_data, _initialisated
            if _initialisated:
                if _timing_data is not None and time:
                    delta_time = (time_module.time() - self.started_time) * 1000
                    _timing_data[msg].append(delta_time)
                if log_this:
                    _indent_depth -= 1

        def __call__(self, f): # decorator use case
            @ wraps(f)
            def wraper(*args, **kwargs):
                self.__enter__()
                try:
                    return f(*args, **kwargs)
                finally:
                    self.__exit__()
            return wraper

    return result()


def shutdown_logging():
    """ Print some statistical data about time consumed by timed code."""

    global _initialisated
    assert _initialisated, 'First you have to call init_logging.'

    if _timing_data is not None:
        log('TIMING INFO')
        log('%5s %8s  %6s   %6s   %6s    %s' % ('calls', 'total', 'avg', 'min', 'max', 'title'))
        for key, times in sorted(_timing_data.items()):
            calls = len(times)
            total = sum(times)/1000
            average = sum(times)/len(times)
            min_time = min(times)
            max_time = max(times)
            msg = '%5d %8.2fs %6.1fms %6.1fms %6.1fms  %s' % \
              (calls, total, average, min_time, max_time, key)
            log(msg)


def _log(lvl, msg, category=''):
    global _indent_depth
    msg = (LOG_INDENT_PATTERN*_indent_depth) + msg
    logging.log(lvl, msg)


def _validate_level(lvl):
    switch = {'debug':logging.DEBUG,
              'info':logging.INFO,
              'warning':logging.WARNING,
              'error':logging.ERROR,
              'critical':logging.CRITICAL}
    assert lvl in switch
    level = switch[lvl]
    return level

