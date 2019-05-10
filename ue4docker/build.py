import argparse, getpass, humanfriendly, os, shutil, sys, tempfile, time
from .infrastructure import *
from os.path import join

def _getCredential(args, name, envVar, promptFunc):
	
	# Check if the credential was specified via the command-line
	if getattr(args, name, None) is not None:
		print('Using {} specified via `-{}` command-line argument.'.format(name, name))
		return getattr(args, name)
	
	# Check if the credential was specified via an environment variable
	if envVar in os.environ:
		print('Using {} specified via {} environment variable.'.format(name, envVar))
		return os.environ[envVar]
	
	# Fall back to prompting the user for the value
	return promptFunc()

def _getUsername(args):
	return _getCredential(args, 'username', 'UE4DOCKER_USERNAME', lambda: input("Username: "))

def _getPassword(args):
	return _getCredential(args, 'password', 'UE4DOCKER_PASSWORD', lambda: getpass.getpass("Password: "))


def build():
	
	# Create our logger to generate coloured output on stderr
	logger = Logger(prefix='[{} build] '.format(sys.argv[0]))
	
	# Register our supported command-line arguments
	parser = argparse.ArgumentParser(prog='{} build'.format(sys.argv[0]))
	BuildConfiguration.addArguments(parser)
	
	# If no command-line arguments were supplied, display the help message and exit
	if len(sys.argv) < 2:
		parser.print_help()
		sys.exit(0)
	
	# Parse the supplied command-line arguments
	try:
		config = BuildConfiguration(parser, sys.argv[1:])
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
		builder = ImageBuilder(contextRoot, config.containerPlatform, logger)
		
		# Determine if we are building a custom version of UE4
		if config.custom == True:
			logger.info('CUSTOM ENGINE BUILD:', False)
			logger.info('Custom name:  ' + config.release, False)
			logger.info('Repository:   ' + config.repository, False)
			logger.info('Branch/tag:   ' + config.branch + '\n', False)
		
		# Determine if we are building Windows or Linux containers
		if config.containerPlatform == 'windows':
			
			# Provide the user with feedback so they are aware of the Windows-specific values being used
			logger.info('WINDOWS CONTAINER SETTINGS', False)
			logger.info('Isolation mode:               {}'.format(config.isolation), False)
			logger.info('Base OS image tag:            {} (host OS is {})'.format(config.basetag, WindowsUtils.systemStringShort()), False)
			logger.info('Memory limit:                 {}'.format('No limit' if config.memLimit is None else '{:.2f}GB'.format(config.memLimit)), False)
			logger.info('Detected max image size:      {:.0f}GB'.format(DockerUtils.maxsize()), False)
			logger.info('Directory to copy DLLs from:  {}\n'.format(config.dlldir), False)
			
			# Verify that the user is not attempting to build images with a newer kernel version than the host OS
			if WindowsUtils.isNewerBaseTag(config.hostBasetag, config.basetag):
				logger.error('Error: cannot build container images with a newer kernel version than that of the host OS!')
				sys.exit(1)
			
			# Check if the user is building a different kernel version to the host OS but is still copying DLLs from System32
			differentKernels = WindowsUtils.isInsiderPreview() or config.basetag != config.hostBasetag
			if config.pullPrerequisites == False and differentKernels == True and config.dlldir == config.defaultDllDir:
				logger.error('Error: building images with a different kernel version than the host,', False)
				logger.error('but a custom DLL directory has not specified via the `-dlldir=DIR` arg.', False)
				logger.error('The DLL files will be the incorrect version and the container OS will', False)
				logger.error('refuse to load them, preventing the built Engine from running correctly.', False)
				sys.exit(1)
			
			# Attempt to copy the required DLL files from the host system if we are building the prerequisites image
			if config.pullPrerequisites == False:
				for dll in WindowsUtils.requiredHostDlls(config.basetag):
					shutil.copy2(join(config.dlldir, dll), join(builder.context('ue4-build-prerequisites'), dll))
			
			# Ensure the Docker daemon is configured correctly
			requiredLimit = WindowsUtils.requiredSizeLimit()
			if DockerUtils.maxsize() < requiredLimit:
				logger.error('SETUP REQUIRED:')
				logger.error('The max image size for Windows containers must be set to at least {}GB.'.format(requiredLimit))
				logger.error('See the Microsoft documentation for configuration instructions:')
				logger.error('https://docs.microsoft.com/en-us/visualstudio/install/build-tools-container#step-4-expand-maximum-container-disk-size')
				logger.error('Under Windows Server, the command `{} setup` can be used to automatically configure the system.'.format(sys.argv[0]))
				sys.exit(1)
			
		elif config.containerPlatform == 'linux':
			
			# Determine if we are building CUDA-enabled container images
			capabilities = 'CUDA {} + OpenGL'.format(config.cuda) if config.cuda is not None else 'OpenGL'
			logger.info('LINUX CONTAINER SETTINGS', False)
			logger.info('Building GPU-enabled images compatible with NVIDIA Docker ({} support).\n'.format(capabilities), False)
		
		# Report which Engine components are being excluded (if any)
		logger.info('GENERAL SETTINGS', False)
		if len(config.excludedComponents) > 0:
			logger.info('Excluding the following Engine components:', False)
			for component in config.describeExcludedComponents():
				logger.info('- {}'.format(component), False)
		else:
			logger.info('Not excluding any Engine components.', False)
		
		# Determine if we are performing a dry run
		if config.dryRun == True:
			
			# Don't bother prompting the user for any credentials
			logger.info('Performing a dry run, `docker build` commands will be printed and not executed.', False)
			username = ''
			password = ''
			
		else:
			
			# Retrieve the Git username and password from the user
			print('\nRetrieving the Git credentials that will be used to clone the UE4 repo')
			username = _getUsername(config.args)
			password = _getPassword(config.args)
			print()
		
		# Start the HTTP credential endpoint as a child process and wait for it to start
		endpoint = CredentialEndpoint(username, password)
		endpoint.start()
		
		try:
			
			# Keep track of our starting time
			startTime = time.time()
			
			# Compute the build options for the UE4 build prerequisites image
			# (This is the only image that does not use any user-supplied tag suffix, since the tag always reflects any customisations)
			prereqsArgs = ['--build-arg', 'BASEIMAGE=' + config.baseImage]
			if config.containerPlatform == 'windows':
				prereqsArgs = prereqsArgs + ['--build-arg', 'HOST_VERSION=' + WindowsUtils.getWindowsBuild()]
			
			# Build or pull the UE4 build prerequisites image
			if config.pullPrerequisites == True:
				builder.pull('adamrehn/ue4-build-prerequisites:{}'.format(config.prereqsTag), config.rebuild, config.dryRun)
			else:
				builder.build('adamrehn/ue4-build-prerequisites', [config.prereqsTag], config.platformArgs + prereqsArgs, config.rebuild, config.dryRun)
			
			# Build the UE4 source image
			mainTags = ['{}{}-{}'.format(config.release, config.suffix, config.prereqsTag), config.release + config.suffix]
			prereqConsumerArgs = ['--build-arg', 'PREREQS_TAG={}'.format(config.prereqsTag)]
			ue4SourceArgs = prereqConsumerArgs + [
				'--build-arg', 'GIT_REPO={}'.format(config.repository),
				'--build-arg', 'GIT_BRANCH={}'.format(config.branch)
			]
			builder.build('ue4-source', mainTags, config.platformArgs + ue4SourceArgs + endpoint.args(), config.rebuild, config.dryRun)
			
			# Build the UE4 Engine source build image, unless requested otherwise by the user
			ue4BuildArgs = prereqConsumerArgs + [
				'--build-arg', 'TAG={}'.format(mainTags[1]),
				'--build-arg', 'NAMESPACE={}'.format(GlobalConfiguration.getTagNamespace())
			]
			if config.noEngine == False:
				builder.build('ue4-engine', mainTags, config.platformArgs + ue4BuildArgs, config.rebuild, config.dryRun)
			else:
				logger.info('User specified `--no-engine`, skipping ue4-engine image build.')
			
			# Build the minimal UE4 CI image, unless requested otherwise by the user
			buildUe4Minimal = config.noMinimal == False
			if buildUe4Minimal == True:
				builder.build('ue4-minimal', mainTags, config.platformArgs + config.exclusionFlags + ue4BuildArgs, config.rebuild, config.dryRun)
			else:
				logger.info('User specified `--no-minimal`, skipping ue4-minimal image build.')
			
			# Build the full UE4 CI image, unless requested otherwise by the user
			buildUe4Full = buildUe4Minimal == True and config.noFull == False
			if buildUe4Full == True:
				builder.build('ue4-full', mainTags, config.platformArgs + ue4BuildArgs, config.rebuild, config.dryRun)
			else:
				logger.info('Not building ue4-minimal or user specified `--no-full`, skipping ue4-full image build.')
			
			# Report the total execution time
			endTime = time.time()
			logger.action('Total execution time: {}'.format(humanfriendly.format_timespan(endTime - startTime)))
			
			# Stop the HTTP server
			endpoint.stop()
		
		except Exception as e:
			
			# One of the images failed to build
			logger.error('Error: {}'.format(e))
			endpoint.stop()
			sys.exit(1)
