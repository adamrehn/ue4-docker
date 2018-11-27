from .infrastructure import DarwinUtils, DockerUtils, Logger, PrettyPrinting, WindowsUtils
from .build import build
from .clean import clean
from .export import export
from .info import info
from .setup_cmd import setup
from .version_cmd import version
import os, platform, sys

def _exitWithError(err):
	Logger().error(err)
	sys.exit(1)

def main():
	
	# Verify that Docker is installed
	if DockerUtils.installed() == False:
		_exitWithError('Error: could not detect Docker daemon version. Please ensure Docker is installed.')
	
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
