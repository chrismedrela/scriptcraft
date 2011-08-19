#!/usr/bin/env python
#-*- coding:utf-8 -*-
 
import shutil, os, subprocess
 
def bash_executor(command, input_files={}, output_files={}, input_data='', executing_folder='env'):
	"""
	Wykonuje polecenie basha command w wyizolowanym środowisku
	(tj. w osobnym folderze).
	
	Na wejście programu podaje input_data.
	
	Przed wykonaniem polecenia kopiuje pliki z input_files.keys()
	do input_files.values().
	
	Po wykonaniu polecenia kopiuje pliki z output_files.keys()
	do output_files.values() i sprząta po sobie. W przypadku niepowodzenia
	*nie* zgłasza błędów!
		
	executing_folder to folder, który ma zostać wyizolowany.
	* Ten folder musi istnieć! *

	"""
	
	# copy input files	
	for file_source, file_destination in input_files.items():
		shutil.copy(file_source, os.path.join(executing_folder, file_destination))
	
	# run command
	oldCwd = os.getcwd()
	os.chdir(executing_folder)
	process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	output, errors_output = process.communicate(input=input_data)
	exit_code = process.wait()
	os.chdir(oldCwd)
	
	# clean up
	try:
		for f in input_files.values():
			os.remove(os.path.join(executing_folder, f))
	except IOError:
		pass

	# copy output files
	try:
		for file_source, file_destination in output_files.items():
			shutil.copy(os.path.join(executing_folder, file_source), file_destination)
	except IOError:
		pass

	# finish
	return (output, errors_output, exit_code) 
