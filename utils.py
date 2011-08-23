#!/usr/bin/env python
#-*- coding:utf-8 -*-

import time


class max_time(object):
	""" Dekorator do testów wydajnościowych - oznaczony tym dekoratorem test
	zawodzi, jeżeli zostanie przekroczony dany czas podany w milisekundach. """

	def __init__(self, max_time_in_miliseconds):
		self.max_time = max_time_in_miliseconds
		
	def __call__(self, f):
	
		def result(test_case, *args, **kwargs):
			start_time = time.time()
			f(test_case, *args, **kwargs)
			end_time = time.time()
			
			delta_time_in_miliseconds = (end_time-start_time)*1000
			if delta_time_in_miliseconds > self.max_time:
				test_case.fail('Too long executing time  %.2f ms (max  %.2f ms).' % (delta_time_in_miliseconds, self.max_time))
				
		return result


		
