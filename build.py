#!/usr/bin/env python3
import argparse, getpass, os, shutil, sys
from os.path import join
from utils import *

# The default Windows Server Core base image tag
# (See <https://hub.docker.com/r/microsoft/windowsservercore/> for a list of valid tags)
DEFAULT_WINDOWS_BASETAG = '1803'

if __name__ == '__main__':
	
	# Create our logger to generate coloured output on stderr
	logger = Logger(prefix='[build.py] ')
	
	# Our supported command-line arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('release', help='UE4 release to build, in semver format (e.g. 4.19.0)')
	parser.add_argument('--linux', action='store_true', help='Build Linux container images under Windows')
	parser.add_argument('--rebuild', action='store_true', help='Rebuild images even if they already exist')
	parser.add_argument('--dry-run', action='store_true', help='Print `docker build` commands instead of running them')
	parser.add_argument('--no-package', action='store_true', help='Don\'t build the ue4-package image')
	parser.add_argument('--no-capture', action='store_true', help='Don\'t build the ue4-capture image')
	parser.add_argument('--random-memory', action='store_true', help='Use a random memory limit for Windows containers')
	parser.add_argument('--nvidia', action='store_true', help='Build GPU-enabled images for NVIDIA Docker under Linux')
	parser.add_argument('--cuda', action='store_true', help='Add CUDA support as well as OpenGL support when building NVIDIA Docker images')
	parser.add_argument('-isolation', default=None, help='Set the isolation mode to use for Windows containers (process or hyperv)')
	parser.add_argument('-basetag', default=DEFAULT_WINDOWS_BASETAG, help='Windows Server Core base image tag to use for Windows containers (default is ' + DEFAULT_WINDOWS_BASETAG + ')')
	parser.add_argument('-suffix', default='', help='Add a suffix to the tags of the built images')
	
	# If no command-line arguments were supplied, display the help message and exit
	if len(sys.argv) < 2:
		parser.print_help()
		sys.exit(0)
	
	# Parse the supplied command-line arguments
	args = parser.parse_args()
	try:
		config = BuildConfiguration(args)
	except RuntimeError as e:
		logger.error('Error: {}'.format(e))
		sys.exit(1)
	
	# Determine if we are building Windows or Linux containers
	if config.containerPlatform == 'windows':
		
		# Provide the user with feedback so they are aware of the Windows-specific values being used
		logger.info('WINDOWS CONTAINER SETTINGS', False)
		logger.info('Isolation mode:           {}'.format(config.isolation), False)
		logger.info('Base OS image tag:        ' + config.basetag, False)
		logger.info('Memory limit:             {:.2f}GB'.format(config.memLimit), False)
		logger.info('Detected max image size:  {:.0f}GB\n'.format(DockerUtils.maxsize()), False)
		
	elif config.containerPlatform == 'linux':
		
		# Determine if we are building GPU-enabled container images
		if config.nvidia == True or config.cuda == True:
			capabilities = 'CUDA + OpenGL' if config.cuda == True else 'OpenGL'
			logger.info('Building GPU-enabled images for use with NVIDIA Docker ({} support).\n'.format(capabilities), False)
	
	# If we are building Windows containers, ensure the Docker daemon is configured correctly
	if config.containerPlatform == 'windows' and DockerUtils.maxsize() < 200.0:
		logger.error('SETUP REQUIRED:')
		logger.error('The max image size for Windows containers must be set to at least 200GB.')
		logger.error('See the Microsoft documentation for configuration instructions:')
		logger.error('https://docs.microsoft.com/en-us/visualstudio/install/build-tools-container#step-4-expand-maximum-container-disk-size')
		sys.exit(1)
	
	# Determine if we are performing a dry run
	if config.dryRun == True:
		
		# Don't bother prompting the user for any credentials
		logger.info('Performing a dry run, `docker build` commands will be printed and not executed.', False)
		username = ''
		password = ''
		
	else:
		
		# Retrieve the Git username and password from the user
		print('Enter the Git credentials that will be used to clone the UE4 repo')
		username = input("Username: ")
		password = getpass.getpass("Password: ")
	
	# Start the HTTP credential endpoint as a child process and wait for it to start
	endpoint = CredentialEndpoint(username, password)
	endpoint.start()
	
	# Create the builder instance to build the Docker images
	contextRoot = join(os.path.dirname(os.path.abspath(__file__)), 'dockerfiles')
	builder = ImageBuilder(contextRoot, 'adamrehn/', config.containerPlatform, logger)
	
	# If we are building Windows containers, copy the required DirectSound and OpenGL DLL files from the host system
	if config.containerPlatform == 'windows':
		for dll in ['dsound.dll', 'opengl32.dll', 'glu32.dll']:
			shutil.copy2(join(os.environ['SystemRoot'], 'System32', dll), join(builder.context('ue4-build-prerequisites'), dll))
	
	try:
		
		# Build the UE4 build prerequisites image
		prereqsTag = 'latest' + config.suffix
		prereqsArgs = ['--build-arg', 'BASEIMAGE=' + config.baseImage]
		builder.build('ue4-build-prerequisites', prereqsTag, config.platformArgs + prereqsArgs, config.rebuild, config.dryRun)
		
		# Build the UE4 source image
		mainTag = config.release + config.suffix
		ue4SourceArgs = ['--build-arg', 'PREREQS_TAG={}'.format(prereqsTag), '--build-arg', 'GIT_TAG={}-release'.format(config.release)]
		builder.build('ue4-source', mainTag, config.platformArgs + ue4SourceArgs + endpoint.args(), config.rebuild, config.dryRun)
		
		# Build the UE4 build image
		ue4BuildArgs = ['--build-arg', 'TAG={}'.format(mainTag)]
		builder.build('ue4-build', mainTag, config.platformArgs + ue4BuildArgs, config.rebuild, config.dryRun)
		
		# Build the UE4 packaging image (for packaging Shipping builds of projects), unless requested otherwise by the user
		buildUe4Package = config.noPackage == False
		if buildUe4Package == True:
			builder.build('ue4-package', mainTag, config.platformArgs + ue4BuildArgs, config.rebuild, config.dryRun)
		else:
			logger.info('User specified `--no-package`, skipping ue4-package image build.')
		
		# Build the UE4Capture image (for capturing gameplay footage), unless requested otherwise by the user
		if buildUe4Package == True and config.noCapture == False and config.containerPlatform == 'linux' and config.nvidia == True:
			builder.build('ue4-capture', mainTag, config.platformArgs + ue4BuildArgs, config.rebuild, config.dryRun)
		else:
			logger.info('Not building NVIDIA Docker ue4-package or user specified `--no-capture`, skipping ue4-capture image build.')
		
		# Stop the HTTP server
		endpoint.stop()
	
	except:
		
		# One of the images failed to build
		endpoint.stop()
		sys.exit(1)
