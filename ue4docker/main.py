from .infrastructure import DarwinUtils, DockerUtils, Logger, PrettyPrinting, WindowsUtils
from .build import build
from .clean import clean
from .diagnostics_cmd import diagnostics
from .export import export
from .info import info
from .setup_cmd import setup
from .test import test
from .version_cmd import version
import logging, os, platform, sys

def _exitWithError(err):
	Logger().error(err)
	sys.exit(1)

def main():
	
	# Configure verbose logging if the user requested it
	# (NOTE: in a future version of ue4-docker the `Logger` class will be properly integrated with standard logging)
	if '-v' in sys.argv or '--verbose' in sys.argv:
		
		# Enable verbose logging
		logging.getLogger().setLevel(logging.DEBUG)
		
		# Filter out the verbose flag to avoid breaking commands that don't support it
		if not (len(sys.argv) > 1 and sys.argv[1] in ['build']):
			sys.argv = list([arg for arg in sys.argv if arg not in ['-v', '--verbose']])
	
	# Verify that Docker is installed
	installed, error = DockerUtils.installed()
	if installed == False:
		_exitWithError('Error: could not detect Docker daemon version. Please ensure Docker is installed.\n\nError details: {}'.format(error))
	
	# Under Windows, verify that the host is a supported version
	if platform.system() == 'Windows' and WindowsUtils.isSupportedWindowsVersion() == False:
		_exitWithError('Error: the detected version of Windows ({}) is not supported. Windows 10 / Windows Server version 1607 or newer is required.'.format(platform.win32_ver()[1]))
	
	# Under macOS, verify that the host is a supported version
	if platform.system() == 'Darwin' and DarwinUtils.isSupportedMacOsVersion() == False:
		_exitWithError('Error: the detected version of macOS ({}) is not supported. macOS {} or newer is required.'.format(DarwinUtils.getMacOsVersion(), DarwinUtils.minimumRequiredVersion()))
	
	# Our supported commands
	COMMANDS = {
		'build': {
			'function': build,
			'description': 'Builds container images for a specific version of UE4'
		},
		'clean': {
			'function': clean,
			'description': 'Cleans built container images'
		},
		'diagnostics': {
			'function': diagnostics,
			'description': 'Runs diagnostics to detect issues with the host system configuration'
		},
		'export': {
			'function': export,
			'description': 'Exports components from built container images to the host system'
		},
		'info': {
			'function': info,
			'description': 'Displays information about the host system and Docker daemon'
		},
		'setup': {
			'function': setup,
			'description': 'Automatically configures the host system where possible'
		},
		'test': {
			'function': test,
			'description': 'Runs tests to verify the correctness of built container images'
		},
		'version': {
			'function': version,
			'description': 'Prints the ue4-docker version number'
		}
	}
	
	# Truncate argv[0] to just the command name without the full path
	sys.argv[0] = os.path.basename(sys.argv[0])
	
	# Determine if a command has been specified
	if len(sys.argv) > 1:
		
		# Verify that the specified command is valid
		command = sys.argv[1]
		if command not in COMMANDS:
			print('Error: unrecognised command "{}".'.format(command), file=sys.stderr)
			sys.exit(1)
		
		# Invoke the command
		sys.argv = [sys.argv[0]] + sys.argv[2:]
		COMMANDS[command]['function']()
		
	else:
		
		# Print usage syntax
		print('Usage: {} COMMAND [OPTIONS]\n'.format(sys.argv[0]))
		print('Windows and Linux containers for Unreal Engine 4\n')
		print('Commands:')
		PrettyPrinting.printColumns([
			(command, COMMANDS[command]['description'])
			for command in COMMANDS
		])
		print('\nRun `{} COMMAND --help` for more information on a command.'.format(sys.argv[0]))
