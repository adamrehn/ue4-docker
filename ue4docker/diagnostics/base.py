import subprocess

class DiagnosticBase(object):
	
	def getName(self):
		'''
		Returns the human-readable name of the diagnostic
		'''
		raise NotImplementedError
	
	def getDescription(self):
		'''
		Returns a description of what the diagnostic does
		'''
		raise NotImplementedError
	
	def run(self, logger, args=[]):
		'''
		Runs the diagnostic
		'''
		raise NotImplementedError
	
	
	# Helper functionality for derived classes
	
	def _printAndRun(self, logger, prefix, command, check=False):
		'''
		Prints a command and then executes it
		'''
		logger.info(prefix + 'Run: {}'.format(command), False)
		subprocess.run(command, check=check)
