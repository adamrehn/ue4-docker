import argparse, getpass, humanfriendly, json, os, shutil, sys, tempfile, time
from .infrastructure import *
from .version import __version__
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
	
	# Verify that we aren't trying to build Windows containers under Windows 10 when in Linux container mode (or vice versa)
	# (Note that we don't bother performing this check when we're just copying Dockerfiles to an output directory)
	if config.layoutDir is None:
		dockerPlatform = DockerUtils.info()['OSType'].lower()
		if config.containerPlatform == 'windows' and dockerPlatform == 'linux':
			logger.error('Error: cannot build Windows containers when Docker Desktop is in Linux container', False)
			logger.error('mode. Use the --linux flag if you want to build Linux containers instead.', False)
			sys.exit(1)
		elif config.containerPlatform == 'linux' and dockerPlatform == 'windows':
			logger.error('Error: cannot build Linux containers when Docker Desktop is in Windows container', False)
			logger.error('mode. Remove the --linux flag if you want to build Windows containers instead.', False)
			sys.exit(1)
	
	# Create an auto-deleting temporary directory to hold our build context
	with tempfile.TemporaryDirectory() as tempDir:
		
		# Copy our Dockerfiles to the temporary directory
		contextOrig = join(os.path.dirname(os.path.abspath(__file__)), 'dockerfiles')
		contextRoot = join(tempDir, 'dockerfiles')
		shutil.copytree(contextOrig, contextRoot)
		
		# Create the builder instance to build the Docker images
		builder = ImageBuilder(contextRoot, config.containerPlatform, logger, config.rebuild, config.dryRun, config.layoutDir, config.opts, config.combine)
		
		# Resolve our main set of tags for the generated images
		mainTags = ['{}{}-{}'.format(config.release, config.suffix, config.prereqsTag), config.release + config.suffix]
		
		# Print the command-line invocation that triggered this build, masking any supplied passwords
		args = ['*******' if config.args.password is not None and arg == config.args.password else arg for arg in sys.argv]
		logger.info('COMMAND-LINE INVOCATION:', False)
		logger.info(str(args), False)
		
		# Print the details of the Unreal Engine version being built
		logger.info('UNREAL ENGINE VERSION SETTINGS:')
		logger.info('Custom build:  {}'.format('Yes' if config.custom == True else 'No'), False)
		if config.custom == True:
			logger.info('Custom name:   ' + config.release, False)
		else:
			logger.info('Release:       ' + config.release, False)
		logger.info('Repository:    ' + config.repository, False)
		logger.info('Branch/tag:    ' + config.branch + '\n', False)
		
		# Determine if we are using a custom version for ue4cli or conan-ue4cli
		if config.ue4cliVersion is not None or config.conanUe4cliVersion is not None:
			logger.info('CUSTOM PACKAGE VERSIONS:', False)
			logger.info('ue4cli:        {}'.format(config.ue4cliVersion if config.ue4cliVersion is not None else 'default'), False)
			logger.info('conan-ue4cli:  {}\n'.format(config.conanUe4cliVersion if config.conanUe4cliVersion is not None else 'default'), False)
		
		# Report any advanced configuration options that were specified
		if len(config.opts) > 0:
			logger.info('ADVANCED CONFIGURATION OPTIONS:', False)
			for key, value in sorted(config.opts.items()):
				logger.info('{}: {}'.format(key, json.dumps(value)), False)
			print('', file=sys.stderr, flush=True)
		
		# Determine if we are building Windows or Linux containers
		if config.containerPlatform == 'windows':
			
			# Provide the user with feedback so they are aware of the Windows-specific values being used
			logger.info('WINDOWS CONTAINER SETTINGS', False)
			logger.info('Isolation mode:               {}'.format(config.isolation), False)
			logger.info('Base OS image tag:            {}'.format(config.basetag), False)
			logger.info('Host OS:                      {}'.format(WindowsUtils.systemString()), False)
			logger.info('Memory limit:                 {}'.format('No limit' if config.memLimit is None else '{:.2f}GB'.format(config.memLimit)), False)
			logger.info('Detected max image size:      {:.0f}GB'.format(DockerUtils.maxsize()), False)
			logger.info('Visual Studio:                {}'.format(config.visualStudio), False)
			logger.info('Directory to copy DLLs from:  {}\n'.format(config.dlldir), False)

			# Verify that the specified base image tag is not a release that has reached End Of Life (EOL)
			if not config.ignoreEOL and WindowsUtils.isEndOfLifeWindowsVersion(config.basetag):
				logger.error('Error: detected EOL base OS image tag: {}'.format(config.basetag), False)
				logger.error('This version of Windows has reached End Of Life (EOL), which means', False)
				logger.error('Microsoft no longer supports or maintains container base images for it.', False)
				logger.error('You will need to use a base image tag for a supported version of Windows.', False)
				sys.exit(1)

			# Verify that the host OS is not a release that is blacklisted due to critical bugs
			if config.ignoreBlacklist == False and WindowsUtils.isBlacklistedWindowsVersion() == True:
				logger.error('Error: detected blacklisted host OS version: {}'.format(WindowsUtils.systemString()), False)
				logger.error('', False)
				logger.error('This version of Windows contains one or more critical bugs that', False)
				logger.error('render it incapable of successfully building UE4 container images.', False)
				logger.error('You will need to use an older or newer version of Windows.', False)
				logger.error('', False)
				logger.error('For more information, see:', False)
				logger.error('https://unrealcontainers.com/docs/concepts/windows-containers', False)
				sys.exit(1)

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
				logger.error('https://docs.microsoft.com/en-us/virtualization/windowscontainers/manage-containers/container-storage#storage-limits')
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
		
		# Determine if we need to prompt for credentials
		if config.dryRun == True:
			
			# Don't bother prompting the user for any credentials during a dry run
			logger.info('Performing a dry run, `docker build` commands will be printed and not executed.', False)
			username = ''
			password = ''
			
		elif config.layoutDir is not None:
			
			# Don't bother prompting the user for any credentials when we're just copying the Dockerfiles to a directory
			logger.info('Copying generated Dockerfiles to: {}'.format(config.layoutDir), False)
			username = ''
			password = ''
			
		elif builder.willBuild('ue4-source', mainTags) == False:
			
			# Don't bother prompting the user for any credentials if we're not building the ue4-source image
			logger.info('Not building the ue4-source image, no Git credentials required.', False)
			username = ''
			password = ''
			
		else:
			
			# Retrieve the Git username and password from the user when building the ue4-source image
			print('\nRetrieving the Git credentials that will be used to clone the UE4 repo')
			username = _getUsername(config.args)
			password = _getPassword(config.args)
			print()
		
		# If resource monitoring has been enabled, start the resource monitoring background thread
		resourceMonitor = ResourceMonitor(logger, config.args.interval)
		if config.args.monitor == True:
			resourceMonitor.start()
		
		# Start the HTTP credential endpoint as a child process and wait for it to start
		endpoint = CredentialEndpoint(username, password)
		endpoint.start()
		
		try:
			
			# Keep track of our starting time
			startTime = time.time()
			
			# If we're copying Dockerfiles to an output directory then make sure it exists and is empty
			if config.layoutDir is not None:
				if os.path.exists(config.layoutDir):
					shutil.rmtree(config.layoutDir)
				os.makedirs(config.layoutDir)
			
			# Keep track of the images we've built
			builtImages = []
			
			# Compute the build options for the UE4 build prerequisites image
			# (This is the only image that does not use any user-supplied tag suffix, since the tag always reflects any customisations)
			prereqsArgs = ['--build-arg', 'BASEIMAGE=' + config.baseImage]
			if config.containerPlatform == 'windows':
				prereqsArgs = prereqsArgs + [
					'--build-arg', 'HOST_BUILD=' + str(WindowsUtils.getWindowsBuild()),
					'--build-arg', 'VISUAL_STUDIO_BUILD_NUMBER=' + config.visualStudioBuildNumber,
				]
			
			# Build or pull the UE4 build prerequisites image (don't pull it if we're copying Dockerfiles to an output directory)
			if config.layoutDir is None and config.pullPrerequisites == True:
				builder.pull('adamrehn/ue4-build-prerequisites:{}'.format(config.prereqsTag))
			else:
				builder.build('adamrehn/ue4-build-prerequisites', [config.prereqsTag], config.platformArgs + prereqsArgs)
				builtImages.append('ue4-build-prerequisites')
			
			# If we're using build secrets then pass the Git username and password to the UE4 source image as secrets
			secrets = {}
			if config.opts.get('use_build_secrets', False) == True:
				secrets = {
					'username': username,
					'password': password
				}
			
			# Build the UE4 source image
			prereqConsumerArgs = ['--build-arg', 'PREREQS_TAG={}'.format(config.prereqsTag)]
			credentialArgs = [] if len(secrets) > 0 else endpoint.args()
			ue4SourceArgs = prereqConsumerArgs + [
				'--build-arg', 'GIT_REPO={}'.format(config.repository),
				'--build-arg', 'GIT_BRANCH={}'.format(config.branch),
				'--build-arg', 'VERBOSE_OUTPUT={}'.format('1' if config.verbose == True else '0')
			]
			builder.build('ue4-source', mainTags, config.platformArgs + ue4SourceArgs + credentialArgs, secrets)
			builtImages.append('ue4-source')
			
			# Build the UE4 Engine source build image, unless requested otherwise by the user
			ue4BuildArgs = prereqConsumerArgs + [
				'--build-arg', 'TAG={}'.format(mainTags[1]),
				'--build-arg', 'NAMESPACE={}'.format(GlobalConfiguration.getTagNamespace())
			]
			if config.noEngine == False:
				builder.build('ue4-engine', mainTags, config.platformArgs + ue4BuildArgs)
				builtImages.append('ue4-engine')
			else:
				logger.info('User specified `--no-engine`, skipping ue4-engine image build.')
			
			# Build the minimal UE4 CI image, unless requested otherwise by the user
			buildUe4Minimal = config.noMinimal == False
			if buildUe4Minimal == True:
				builder.build('ue4-minimal', mainTags, config.platformArgs + config.exclusionFlags + ue4BuildArgs + config.uatBuildFlags)
				builtImages.append('ue4-minimal')
			else:
				logger.info('User specified `--no-minimal`, skipping ue4-minimal image build.')
			
			# Build the full UE4 CI image, unless requested otherwise by the user
			buildUe4Full = buildUe4Minimal == True and config.noFull == False
			if buildUe4Full == True:
				
				# If custom version strings were specified for ue4cli and/or conan-ue4cli, use them
				infrastructureFlags = []
				if config.ue4cliVersion is not None:
					infrastructureFlags.extend(['--build-arg', 'UE4CLI_VERSION={}'.format(config.ue4cliVersion)])
				if config.conanUe4cliVersion is not None:
					infrastructureFlags.extend(['--build-arg', 'CONAN_UE4CLI_VERSION={}'.format(config.conanUe4cliVersion)])
				
				# Build the image
				builder.build('ue4-full', mainTags, config.platformArgs + ue4BuildArgs + infrastructureFlags)
				builtImages.append('ue4-full')
			else:
				logger.info('Not building ue4-minimal or user specified `--no-full`, skipping ue4-full image build.')
			
			# If we are generating Dockerfiles then include information about the options used to generate them
			if config.layoutDir is not None:
				
				# Determine whether we generated a single combined Dockerfile or a set of Dockerfiles
				if config.combine == True:
					
					# Generate a comment to place at the top of the single combined Dockerfile
					lines = ['This file was generated by ue4-docker version {} with the following options:'.format(__version__), '']
					lines.extend(['- {}: {}'.format(key, json.dumps(value)) for key, value in sorted(config.opts.items())])
					lines.extend(['', 'This Dockerfile combines the steps for the following images:', ''])
					lines.extend(['- {}'.format(image) for image in builtImages])
					comment = '\n'.join(['# {}'.format(line) for line in lines])
					
					# Inject the comment at the top of the Dockerfile, being sure to place it after any `escape` parser directive
					dockerfile = join(config.layoutDir, 'combined', 'Dockerfile')
					dockerfileContents = FilesystemUtils.readFile(dockerfile)
					if dockerfileContents.startswith('# escape'):
						newline = dockerfileContents.index('\n')
						dockerfileContents = dockerfileContents[0:newline+1] + '\n' + comment + '\n\n' + dockerfileContents[newline+1:]
					else:
						dockerfileContents = comment + '\n\n' + dockerfileContents
					FilesystemUtils.writeFile(dockerfile, dockerfileContents)
					
				else:
					
					# Create a JSON file to accompany the set of generated Dockerfiles
					FilesystemUtils.writeFile(join(config.layoutDir, 'generated.json'), json.dumps({
						'version': __version__,
						'images': builtImages,
						'opts': config.opts
					}, indent=4, sort_keys=True))
			
			# Report the total execution time
			endTime = time.time()
			logger.action('Total execution time: {}'.format(humanfriendly.format_timespan(endTime - startTime)))
			
			# Stop the resource monitoring background thread if it is running
			resourceMonitor.stop()
			
			# Stop the HTTP server
			endpoint.stop()
		
		except (Exception, KeyboardInterrupt) as e:
			
			# One of the images failed to build
			logger.error('Error: {}'.format(e))
			resourceMonitor.stop()
			endpoint.stop()
			sys.exit(1)
