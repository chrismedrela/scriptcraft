#!/usr/bin/env python
#-*- coding:utf-8 -*-

__all__ = [
    'anything',
    'Const',
    'copy_if_an_instance_given',
    'distance',
    'max_time',
    'memoized',
    'on_error_do',
    'on_error_return',
    'datafile_path',
    'skip',
    'TemporaryFileSystem',
]

from functools import partial, wraps
import os, shutil
import pkg_resources
import time
import traceback



def on_error_return(errors, return_value):
    """ Decorator. Surround function calling with try-except clause.
    If an exception from 'errors' list occurs during executing function,
    return 'return_value'.

    Example
    >>> @ on_error_return ((IOError,), None)
        def f():
            ...

    """

    def inner(f):
        @ wraps(f)
        def wraper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except errors as ex:
                traceback.print_exc(ex)
                return return_value

        return wraper
    return inner


def on_error_do(errors, function):
    """ Decorator. Surround function calling with try-except clause.
    If an exception from 'errors' list occurs during executing function,
    execute 'function' with the exception as an argument.

    Example
    >>> @ on_error ((IOError,),
                    do=lambda exception: my_except_clause())
        def f():
            ...

    """

    def inner(f):
        @ wraps(f)
        def wraper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except errors as error:
                return function(error)

        return wraper
    return inner


def datafile_path(relative_path):
    """ Return absolute path to datafile. The root directory for given
    relative path is scriptcraft directory. An example of valid
    filename: "graphic/base.png"."""
    #relative_path = os.path.join('scriptcraft', relative_path)
    absolute_path = pkg_resources.resource_filename('scriptcraft', relative_path)
    return absolute_path

def copy_if_an_instance_given(f):
    """ Decorator. Use with method __new__ of classes inheriting namedtuple.
    Allow to make a copy instance by passing it as an only argument.

    What's more, if you implement __deepcopy__ like this:

      def __deepcopy__(self, memo):
          c = MyClass(self)
          return c

    you can use deepcopy on your classes inheriting namedtuple with your own
    implementation of __new__ method.

    """

    @ wraps(f)
    def wraper(cls, *args, **kwargs):
        if len(args) == 1 and type(args[0]) == cls and len(kwargs) == 0:
            self = args[0]
            l = [getattr(self, field) for field in cls._fields]
            return cls.__bases__[0].__new__(cls, *l)

        return f(cls, *args, **kwargs)

    return wraper


def distance(p1, p2):
    """ Return distance between p1=(x1,y1) and p2=(x2,y2). Use town metric. """
    return abs(p1[0]-p2[0]) + abs(p1[1]-p2[1])


def skip(f):
    def wrapped(*args, **kwargs):
        pass
    return wrapped


class memoized(object):
    """Decorator that caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned, and
    not re-evaluated.
    """
    def __init__(self, func):
        self.func = func
        self.cache = {}
    def __call__(self, *args):
        try:
            return self.cache[args]
        except KeyError:
            value = self.func(*args)
            self.cache[args] = value
            return value
        except TypeError:
            # uncachable -- for instance, passing a list as an argument.
            # Better to not cache than to blow up entirely.
            return self.func(*args)
    def __repr__(self):
        """Return the function's docstring."""
        return self.func.__doc__
    def __get__(self, obj, objtype):
        """Support instance methods."""
        return partial(self.__call__, obj)


class _Anything(object):
    def __eq__(self, other):
        return True
anything = _Anything()


def Const(name):
    return str(name)


TURN_OFF_EFFICIENCY_TESTS = False
class max_time(object):
    """ Dekorator do testów wydajnościowych - oznaczony tym dekoratorem test
    zawodzi, jeżeli zostanie przekroczony dany czas podany w milisekundach. """

    def __init__(self, max_time_in_miliseconds, repeat=1):
        self.max_time = max_time_in_miliseconds
        self.repeat = repeat


    def __call__(self, f):

        def result(test_case, *args, **kwargs):
            times = []
            for _ in xrange(self.repeat):
                start_time = time.time()
                f(test_case, *args, **kwargs)
                end_time = time.time()

                delta_time_in_miliseconds = (end_time-start_time)*1000
                times.append(delta_time_in_miliseconds)

            average = sum(times)/self.repeat
            if average > self.max_time and not TURN_OFF_EFFICIENCY_TESTS:
                formated_times = ", ".join(map(lambda t: "%.2f ms" % t, times))
                test_case.fail('Too long average executing time  %.2f ms (max  %.2f ms); times: %s.' % \
                    (average, self.max_time, formated_times))

        return result


class TemporaryFileSystem(object):
    def __init__(self, main_folder):
        self.main_folder = main_folder
        self._temporary_files = []
        self._temporary_folders = []
        self.create_folder_if_necessary('') # create main folder

    def write_file(self, file_path, data):
        file_path = os.path.join(self.main_folder, file_path)
        assert not os.path.exists(file_path)
        self._temporary_files.append(file_path)
        with open(file_path, 'w') as s:
            s.write(data)

    def read_file(self, file_path):
        file_path = os.path.join(self.main_folder, file_path)
        with open(file_path, 'r') as s:
            return s.read()

    def create_folder_if_necessary(self, path):
        path = os.path.join(self.main_folder, path)
        self._temporary_folders.append(path)
        if not os.path.exists(path):
            os.mkdir(path)
        else:
            assert os.path.isdir(path), 'Oops! "%s" is not a folder.' % path

    def exists_file_or_folder(self, path):
        path = os.path.join(self.main_folder, path)
        return os.path.exists(path)

    def delete_files_and_folders(self):
        for file in self._temporary_files:
            if os.path.exists(file):
                os.remove(file)
        self._temporary_files = []

        for folder in self._temporary_folders:
            if os.path.exists(folder):
                assert folder != 'scriptcraft'
                shutil.rmtree(folder)
        self._temporary_folders = []
