#!/usr/bin/env python3
import argparse, getpass, os, shutil, sys
from os.path import join
from utils import *

if __name__ == '__main__':
	
	# Create our logger to generate coloured output on stderr
	logger = Logger(prefix='[build.py] ')
	
	# Our supported command-line arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('release', help='UE4 release to build, in semver format (e.g. 4.19.0) or "custom" for a custom repo and branch')
	parser.add_argument('--linux', action='store_true', help='Build Linux container images under Windows')
	parser.add_argument('--rebuild', action='store_true', help='Rebuild images even if they already exist')
	parser.add_argument('--dry-run', action='store_true', help='Print `docker build` commands instead of running them')
	parser.add_argument('--no-package', action='store_true', help='Don\'t build the ue4-package image')
	parser.add_argument('--no-capture', action='store_true', help='Don\'t build the ue4-capture image')
	parser.add_argument('--random-memory', action='store_true', help='Use a random memory limit for Windows containers')
	parser.add_argument('--nvidia', action='store_true', help='Build GPU-enabled images for NVIDIA Docker under Linux')
	parser.add_argument('--cuda', action='store_true', help='Add CUDA support as well as OpenGL support when building NVIDIA Docker images')
	parser.add_argument('-repo', default=None, help='Set the custom git repository to clone when "custom" is specified as the release value')
	parser.add_argument('-branch', default=None, help='Set the custom branch/tag to clone when "custom" is specified as the release value')
	parser.add_argument('-isolation', default=None, help='Set the isolation mode to use for Windows containers (process or hyperv)')
	parser.add_argument('-basetag', default=None, help='Windows Server Core base image tag to use for Windows containers (default is the host OS version)')
	parser.add_argument('-dlldir', default=None, help='Set the directory to copy required Windows DLLs from (default is the host System32 directory)')
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
	
	# Create the builder instance to build the Docker images
	contextRoot = join(os.path.dirname(os.path.abspath(__file__)), 'dockerfiles')
	builder = ImageBuilder(contextRoot, 'adamrehn/', config.containerPlatform, logger)
	
	# Determine if we are building a custom version of UE4
	if config.release == 'custom':
		logger.info('CUSTOM ENGINE BUILD:', False)
		logger.info('Repository:  ' + config.repository, False)
		logger.info('Branch/tag:  ' + config.branch + '\n', False)
	
	# Determine if we are building Windows or Linux containers
	if config.containerPlatform == 'windows':
		
		# Provide the user with feedback so they are aware of the Windows-specific values being used
		logger.info('WINDOWS CONTAINER SETTINGS', False)
		logger.info('Isolation mode:               {}'.format(config.isolation), False)
		logger.info('Base OS image tag:            {} (host OS is {})'.format(config.basetag, config.hostRelease), False)
		logger.info('Memory limit:                 {:.2f}GB'.format(config.memLimit), False)
		logger.info('Detected max image size:      {:.0f}GB'.format(DockerUtils.maxsize()), False)
		logger.info('Directory to copy DLLs from:  {}\n'.format(config.dlldir), False)
		
		# Verify that the user is not attempting to build images with a newer kernel version than the host OS
		if WindowsUtils.isNewerBaseTag(config.hostBasetag, config.basetag):
			logger.error('Error: cannot build container images with a newer kernel version than that of the host OS!')
			sys.exit(1)
		
		# Check if the user is building a different kernel version to the host OS but is still copying DLLs from System32
		differentKernels = WindowsUtils.isInsiderPreview(config.hostRelease) or config.basetag != config.hostBasetag
		if differentKernels == True and config.dlldir == config.defaultDllDir:
			logger.error('Error: building images with a different kernel version than the host,', False)
			logger.error('but a custom DLL directory has not specified via the `-dlldir=DIR` arg.', False)
			logger.error('The DLL files will be the incorrect version and the container OS will', False)
			logger.error('refuse to load them, preventing the built Engine from running correctly.', False)
			sys.exit(1)
		
		# Attempt to copy the required DirectSound and OpenGL DLL files from the host system
		for dll in ['dsound.dll', 'opengl32.dll', 'glu32.dll']:
			shutil.copy2(join(config.dlldir, dll), join(builder.context('ue4-build-prerequisites'), dll))
		
		# Ensure the Docker daemon is configured correctly
		if DockerUtils.maxsize() < 200.0:
			logger.error('SETUP REQUIRED:')
			logger.error('The max image size for Windows containers must be set to at least 200GB.')
			logger.error('See the Microsoft documentation for configuration instructions:')
			logger.error('https://docs.microsoft.com/en-us/visualstudio/install/build-tools-container#step-4-expand-maximum-container-disk-size')
			sys.exit(1)
		
	elif config.containerPlatform == 'linux':
		
		# Determine if we are building GPU-enabled container images
		if config.nvidia == True or config.cuda == True:
			capabilities = 'CUDA + OpenGL' if config.cuda == True else 'OpenGL'
			logger.info('Building GPU-enabled images for use with NVIDIA Docker ({} support).\n'.format(capabilities), False)
	
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
	
	try:
		
		# Build the UE4 build prerequisites image
		prereqsTag = 'latest' + config.suffix
		prereqsArgs = ['--build-arg', 'BASEIMAGE=' + config.baseImage]
		builder.build('ue4-build-prerequisites', prereqsTag, config.platformArgs + prereqsArgs, config.rebuild, config.dryRun)
		
		# Build the UE4 source image
		mainTag = config.release + config.suffix
		ue4SourceArgs = [
			'--build-arg', 'PREREQS_TAG={}'.format(prereqsTag),
			'--build-arg', 'GIT_REPO={}'.format(config.repository),
			'--build-arg', 'GIT_BRANCH={}'.format(config.branch)
		]
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
	
	except Exception as e:
		
		# One of the images failed to build
		logger.error('Error: {}'.format(e))
		endpoint.stop()
		sys.exit(1)
