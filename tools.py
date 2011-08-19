#!/usr/bin/env python
#-*- coding:utf-8 -*-

import copy

class recordtype(type):
	"""
	Like namedtuple, but instances are mutable.
	
	Has methods:
	 __init__
	 __str__
	 __repr__ -- __str__ is the same
	 copy -- it is *not* deep copy
	 
	"""
	
	def __new__(cls, name, args=(), extra_args={}, bases=(), doc=None):
		"""
		Arguments:
		 name -- name of structure
		 args -- list of strings; it describes required atributes of record
		 extra_args -- dictionary with strings as keys and any objects as values;
		  it describes optional atributes of record; values of the dictionary
		  describes default values of the atributes
		 bases -- list of base classes
		 doc -- doc string
		 
		"""
		def init(self, **kwargs):
			#assert all(map(lambda k: k in args or k in extra_args, kwargs.keys())), 'not known keyword argument'
			
			self._name = name
			for i in args:
				try:
					v = kwargs[i]
				except KeyError:
					raise ValueError("No found %s argument" % i) 
				setattr(self, i, v)
			for k,v in extra_args.items():
				setattr(self, k, kwargs.get(k, v))
		def tostr(self):
			arg = ", ".join(map(lambda x: "%s=%s" % (x,repr(getattr(self, x))), args+extra_args.keys()))
			return "<%s: %s>" % (name, arg)
		def torepr(self):
			return str(self)
		def copy_func(self):
			return copy.copy(self)
	
		doc_string = '' if doc==None else doc
		attrs = {'__init__':init, '__str__':tostr, '__repr__':torepr, '__doc__':doc_string, 'copy':copy_func}
		return type(name, tuple(bases), attrs)
		
class Counter(object):
	"""
	Create counter.
	
	It counts from fvalue (optional argument of __init__).
	
	Each calling change internal counter with function inc (optional argument
	of __init__, defaultly incrementing) and return old value of counter.
	
	"""
	
	def __init__(self, fvalue=0, inc = lambda x: x + 1):
		self.inc = inc
		self.val = fvalue
	def __call__(self):
		old = self.val
		self.val = self.inc(self.val)
		return old		
		
def exception(name, base=None):
	""" Fast way for creating exceptions. """
	
	if base==None:
		base = (Exception,)
	return type(name, base, {})
	
def enum(how_much):
	enum.counter += how_much
	return range(enum.counter-how_much, enum.counter)
enum.counter = 12345

