from .base import DiagnosticBase
from .diagnostic_8gig import diagnostic8Gig
from .diagnostic_20gig import diagnostic20Gig
from .diagnostic_maxsize import diagnosticMaxSize
from .diagnostic_network import diagnosticNetwork

class allDiagnostics(DiagnosticBase):
	
	def getName(self):
		'''
		Returns the human-readable name of the diagnostic
		'''
		return 'Run all available diagnostics'
	
	def getDescription(self):
		'''
		Returns a description of what the diagnostic does
		'''
		return 'This diagnostic runs all available diagnostics in sequence.'
	
	def run(self, logger, args=[]):
		'''
		Runs the diagnostic
		'''
		
		# Run all available diagnostics in turn, storing the results
		results = []
		diagnostics = [diagnostic8Gig(), diagnostic20Gig(), diagnosticMaxSize(), diagnosticNetwork()]
		for index, diagnostic in enumerate(diagnostics):
			
			# Run the diagnostic and report its result
			logger.info('[all] Running individual diagnostic: "{}"'.format(diagnostic.getName()), True)
			results.append(diagnostic.run(logger))
			logger.info('[all] Individual diagnostic result: {}'.format('passed' if results[-1] == True else 'failed'), False)
			
			# Print a newline after the last diagnostic has run
			if index == len(diagnostics) - 1:
				print()
		
		# Only report success if all diagnostics succeeded
		return False not in results
