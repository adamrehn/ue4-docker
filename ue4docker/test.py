from .infrastructure import DockerUtils, GlobalConfiguration, Logger
from container_utils import ContainerUtils, ImageUtils
import docker, os, platform, sys

def test():
	
	# Create our logger to generate coloured output on stderr
	logger = Logger(prefix='[{} test] '.format(sys.argv[0]))
	
	# Create our Docker API client
	client = docker.from_env()
	
	# Check that an image tag has been specified
	if len(sys.argv) > 1 and sys.argv[1].strip('-') not in ['h', 'help']:
		
		# Verify that the specified container image exists
		tag = sys.argv[1]
		image = GlobalConfiguration.resolveTag('ue4-full:{}'.format(tag) if ':' not in tag else tag)
		if DockerUtils.exists(image) == False:
			logger.error('Error: the specified container image "{}" does not exist.'.format(image))
			sys.exit(1)
		
		# Use process isolation mode when testing Windows containers, since running Hyper-V containers don't currently support manipulating the filesystem
		platform = ImageUtils.image_platform(client, image)
		isolation = 'process' if platform == 'windows' else None
		
		# Start a container to run our tests in, automatically stopping and removing the container when we finish
		logger.action('Starting a container using the "{}" image...'.format(image), False)
		container = ContainerUtils.start_for_exec(client, image, isolation=isolation)
		with ContainerUtils.automatically_stop(container):
			
			# Create the workspace directory in the container
			workspaceDir = ContainerUtils.workspace_dir(container)
			ContainerUtils.exec(container, ContainerUtils.shell_prefix(container) + ['mkdir ' + workspaceDir])
			
			# Copy our test scripts into the container
			testDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests')
			ContainerUtils.copy_from_host(container, testDir, workspaceDir)
			
			# Create a harness to invoke individual tests
			containerPath = ContainerUtils.path(container)
			pythonCommand = 'python' if ContainerUtils.container_platform(container) == 'windows' else 'python3'
			def runTest(script):
				logger.action('Running test "{}"...'.format(script), False)
				try:
					ContainerUtils.exec(container, [pythonCommand, containerPath.join(workspaceDir, script)], workdir=workspaceDir)
					logger.action('Passed test "{}"'.format(script), False)
				except RuntimeError as e:
					logger.error('Error: test "{}" failed!'.format(script))
					raise e from None
			
			# Run each of our tests in turn
			runTest('build-and-package.py')
			runTest('consume-external-deps.py')
			
			# If we've reached this point then all of the tests passed
			logger.action('All tests passed.', False)
	
	else:
		
		# Print usage syntax
		print('Usage: {} test TAG'.format(sys.argv[0]))
		print('Runs tests to verify the correctness of built container images\n')
		print('TAG should specify the tag of the ue4-full image to test.')
