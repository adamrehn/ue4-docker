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
