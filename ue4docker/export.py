from .infrastructure import DockerUtils, PrettyPrinting
from .exports import *
import sys

def _notNone(items):
	return len([i for i in items if i is not None]) == len(items)

def _extractArg(args, index):
	return args[index] if len(args) > index else None

def _isHelpFlag(arg):
	return (arg.strip('-') in ['h', 'help']) == True

def _stripHelpFlags(args):
	return list([a for a in args if _isHelpFlag(a) == False])

def export():
	
	# The components that can be exported
	COMPONENTS = {
		'installed': {
			'function': exportInstalledBuild,
			'description': 'Exports an Installed Build of the Engine',
			'image': 'adamrehn/ue4-full',
			'help': 'Copies the Installed Build from a container to the host system.\nOnly supported under Linux for UE 4.21.0 and newer.'
		},
		'packages': {
			'function': exportPackages,
			'description': 'Exports conan-ue4cli wrapper packages',
			'image': 'adamrehn/ue4-full',
			'help':
				'Runs a temporary conan server inside a container and uses it to export the\ngenerated conan-ue4cli wrapper packages.\n\n' + 
				'Currently the only supported destination value is "cache", which exports\nthe packages to the Conan local cache on the host system.'
		}
	}
	
	# Parse the supplied command-line arguments
	stripped = _stripHelpFlags(sys.argv)
	args = {
		'help':        len(stripped) < len(sys.argv),
		'component':   _extractArg(stripped, 1),
		'tag':         _extractArg(stripped, 2),
		'destination': _extractArg(stripped, 3)
	}
	
	# If a component name has been specified, verify that it is valid
	if args['component'] is not None and args['component'] not in COMPONENTS:
		print('Error: unrecognised component "{}".'.format(args['component']), file=sys.stderr)
		sys.exit(1)
	
	# Determine if we are performing an export
	if args['help'] == False and _notNone([args['component'], args['tag'], args['destination']]):
		
		# Determine if the user specified an image and a tag or just a tag
		tag = args['tag']
		details = COMPONENTS[ args['component'] ]
		requiredImage = '{}:{}'.format(details['image'], tag) if ':' not in tag else tag
		
		# Verify that the required container image exists
		if DockerUtils.exists(requiredImage) == False:
			print('Error: the specified container image "{}" does not exist.'.format(requiredImage), file=sys.stderr)
			sys.exit(1)
		
		# Attempt to perform the export
		details['function'](requiredImage, args['destination'], stripped[4:])
		print('Export complete.')
	
	# Determine if we are displaying the help for a specific component
	elif args['help'] == True and args['component'] is not None:
		
		# Display the help for the component
		component = sys.argv[1]
		details = COMPONENTS[component]
		print('{} export {}'.format(sys.argv[0], component))
		print(details['description'] + '\n')
		print('Exports from image: {}:TAG\n'.format(details['image']))
		print(details['help'])
	
	else:
		
		# Print usage syntax
		print('Usage: {} export COMPONENT TAG DESTINATION\n'.format(sys.argv[0]))
		print('Exports components from built container images to the host system\n')
		print('Components:')
		PrettyPrinting.printColumns([
			(component, COMPONENTS[component]['description'])
			for component in COMPONENTS
		])
		print('\nRun `{} export COMPONENT --help` for more information on a component.'.format(sys.argv[0]))
