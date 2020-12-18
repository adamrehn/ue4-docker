from .infrastructure import Logger, PrettyPrinting
from .diagnostics import *
import sys

def diagnostics():
	
	# The diagnostics that can be run
	DIAGNOSTICS = {
		'all': allDiagnostics(),
		'8gig': diagnostic8Gig(),
		'maxsize': diagnosticMaxSize(),
		'network': diagnosticNetwork()
	}
	
	# Create our logger to generate coloured output on stderr
	logger = Logger(prefix='[{} diagnostics] '.format(sys.argv[0]))
	
	# Parse the supplied command-line arguments
	stripped = list([arg for arg in sys.argv if arg.strip('-') not in ['h', 'help']])
	args = {
		'help':       len(sys.argv) > len(stripped),
		'diagnostic': stripped[1] if len(stripped) > 1 else None,
	}
	
	# If a diagnostic name has been specified, verify that it is valid
	if args['diagnostic'] is not None and args['diagnostic'] not in DIAGNOSTICS:
		logger.error('Error: unrecognised diagnostic "{}".'.format(args['diagnostic']), False)
		sys.exit(1)
	
	# Determine if we are running a diagnostic
	if args['help'] == False and args['diagnostic'] is not None:
		
		# Run the diagnostic
		diagnostic = DIAGNOSTICS[args['diagnostic']]
		logger.action('Running diagnostic: "{}"'.format(diagnostic.getName()), False)
		passed = diagnostic.run(logger, stripped[2:])
		
		# Print the result
		if passed == True:
			logger.action('Diagnostic result: passed', False)
		else:
			logger.error('Diagnostic result: failed', False)
	
	# Determine if we are displaying the help for a specific diagnostic
	elif args['help'] == True and args['diagnostic'] is not None:
		
		# Display the help for the diagnostic
		diagnostic = DIAGNOSTICS[args['diagnostic']]
		print('{} diagnostics {}'.format(sys.argv[0], args['diagnostic']))
		print(diagnostic.getName() + '\n')
		print(diagnostic.getDescription())
	
	else:
		
		# Print usage syntax
		print('Usage: {} diagnostics DIAGNOSTIC\n'.format(sys.argv[0]))
		print('Runs diagnostics to detect issues with the host system configuration\n')
		print('Available diagnostics:')
		PrettyPrinting.printColumns([
			(diagnostic, DIAGNOSTICS[diagnostic].getName())
			for diagnostic in DIAGNOSTICS
		])
		print('\nRun `{} diagnostics DIAGNOSTIC --help` for more information on a diagnostic.'.format(sys.argv[0]))
