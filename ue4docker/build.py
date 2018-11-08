#!/usr/bin/env python3
import argparse, getpass, os, shutil, sys, tempfile
from .infrastructure import *
from os.path import join

def build():
	
	# Create our logger to generate coloured output on stderr
	logger = Logger(prefix='[{} build] '.format(sys.argv[0]))
	
	# Our supported command-line arguments
	parser = argparse.ArgumentParser(prog='{} build'.format(sys.argv[0]))
	parser.add_argument('release', help='UE4 release to build, in semver format (e.g. 4.19.0) or "custom" for a custom repo and branch')
	parser.add_argument('--linux', action='store_true', help='Build Linux container images under Windows')
	parser.add_argument('--rebuild', action='store_true', help='Rebuild images even if they already exist')
	parser.add_argument('--dry-run', action='store_true', help='Print `docker build` commands instead of running them')
	parser.add_argument('--no-minimal', action='store_true', help='Don\'t build the ue4-minimal image')
	parser.add_argument('--no-full', action='store_true', help='Don\'t build the ue4-full image')
	parser.add_argument('--no-cache', action='store_true', help='Disable Docker build cache')
	parser.add_argument('--random-memory', action='store_true', help='Use a random memory limit for Windows containers')
	parser.add_argument('--cuda', action='store_true', help='Add CUDA support as well as OpenGL support when building Linux containers')
	parser.add_argument('-repo', default=None, help='Set the custom git repository to clone when "custom" is specified as the release value')
	parser.add_argument('-branch', default=None, help='Set the custom branch/tag to clone when "custom" is specified as the release value')
	parser.add_argument('-isolation', default=None, help='Set the isolation mode to use for Windows containers (process or hyperv)')
	parser.add_argument('-basetag', default=None, help='Windows Server Core base image tag to use for Windows containers (default is the host OS version)')
	parser.add_argument('-dlldir', default=None, help='Set the directory to copy required Windows DLLs from (default is the host System32 directory)')
	parser.add_argument('-suffix', default='', help='Add a suffix to the tags of the built images')
	parser.add_argument('-m', default=None, help='Override the default memory limit under Windows (also overrides --random-memory)')
	
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
	
	# Verify that Docker is installed
	if DockerUtils.installed() == False:
		logger.error('Error: could not detect Docker version. Please ensure Docker is installed.')
		sys.exit(1)
	
	# Create an auto-deleting temporary directory to hold our build context
	with tempfile.TemporaryDirectory() as tempDir:
		
		# Copy our Dockerfiles to the temporary directory
		contextOrig = join(os.path.dirname(os.path.abspath(__file__)), 'dockerfiles')
		contextRoot = join(tempDir, 'dockerfiles')
		shutil.copytree(contextOrig, contextRoot)
		
		# Create the builder instance to build the Docker images
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
			
			# Determine if we are building CUDA-enabled container images
			capabilities = 'CUDA + OpenGL' if config.cuda == True else 'OpenGL'
			logger.info('Building GPU-enabled images compatible with NVIDIA Docker ({} support).\n'.format(capabilities), False)
		
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
			prereqConsumerArgs = ['--build-arg', 'PREREQS_TAG={}'.format(prereqsTag)]
			ue4SourceArgs = prereqConsumerArgs + [
				'--build-arg', 'GIT_REPO={}'.format(config.repository),
				'--build-arg', 'GIT_BRANCH={}'.format(config.branch)
			]
			builder.build('ue4-source', mainTag, config.platformArgs + ue4SourceArgs + endpoint.args(), config.rebuild, config.dryRun)
			
			# Build the UE4 Engine source build image
			ue4BuildArgs = ['--build-arg', 'TAG={}'.format(mainTag)]
			builder.build('ue4-engine', mainTag, config.platformArgs + ue4BuildArgs, config.rebuild, config.dryRun)
			
			# Build the minimal UE4 CI image, unless requested otherwise by the user
			buildUe4Minimal = config.noMinimal == False
			if buildUe4Minimal == True:
				builder.build('ue4-minimal', mainTag, config.platformArgs + ue4BuildArgs + prereqConsumerArgs, config.rebuild, config.dryRun)
			else:
				logger.info('User specified `--no-minimal`, skipping ue4-minimal image build.')
			
			# Build the full UE4 CI image, unless requested otherwise by the user
			buildUe4Full = buildUe4Minimal == True and config.noFull == False
			if buildUe4Full == True:
				builder.build('ue4-full', mainTag, config.platformArgs + ue4BuildArgs, config.rebuild, config.dryRun)
			else:
				logger.info('Not building ue4-minimal or user specified `--no-full`, skipping ue4-full image build.')
			
			# Stop the HTTP server
			endpoint.stop()
		
		except Exception as e:
			
			# One of the images failed to build
			logger.error('Error: {}'.format(e))
			endpoint.stop()
			sys.exit(1)
