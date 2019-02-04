import docker, fnmatch, humanfriendly, itertools, json, os, platform, re
from .FilesystemUtils import FilesystemUtils

class DockerUtils(object):
	
	@staticmethod
	def installed():
		'''
		Determines if Docker is installed
		'''
		try:
			return DockerUtils.version() is not None
		except:
			return False
	
	@staticmethod
	def version():
		'''
		Retrieves the version string for the Docker daemon
		'''
		client = docker.from_env()
		return client.version()
	
	@staticmethod
	def info():
		'''
		Retrieves the system information as produced by `docker info`
		'''
		client = docker.from_env()
		return client.info()
	
	@staticmethod
	def exists(name):
		'''
		Determines if the specified image exists
		'''
		client = docker.from_env()
		try:
			image = client.images.get(name)
			return True
		except:
			return False
	
	@staticmethod
	def build(tags, context, args):
		'''
		Returns the `docker build` command to build an image
		'''
		tagArgs = [['-t', tag] for tag in tags]
		return ['docker', 'build'] + list(itertools.chain.from_iterable(tagArgs)) + [context] + args
	
	@staticmethod
	def pull(image):
		'''
		Returns the `docker pull` command to pull an image from a remote registry
		'''
		return ['docker', 'pull', image]
	
	@staticmethod
	def start(image, command, **kwargs):
		'''
		Starts a container in a detached state and returns the container handle
		'''
		client = docker.from_env()
		return client.containers.run(image, command, detach=True, **kwargs)
	
	@staticmethod
	def configFilePath():
		'''
		Returns the path to the Docker daemon configuration file under Windows
		'''
		return '{}\\Docker\\config\\daemon.json'.format(os.environ['ProgramData'])
	
	@staticmethod
	def getConfig():
		'''
		Retrieves and parses the Docker daemon configuration file under Windows
		'''
		configPath = DockerUtils.configFilePath()
		if os.path.exists(configPath) == True:
			with open(configPath) as configFile:
				return json.load(configFile)
		
		return {}
	
	@staticmethod
	def setConfig(config):
		'''
		Writes new values to the Docker daemon configuration file under Windows
		'''
		configPath = DockerUtils.configFilePath()
		with open(configPath, 'w') as configFile:
			configFile.write(json.dumps(config))
	
	@staticmethod
	def maxsize():
		'''
		Determines the configured size limit (in GB) for Windows containers
		'''
		if platform.system() != 'Windows':
			return -1
		
		config = DockerUtils.getConfig()
		if 'storage-opts' in config:
			sizes = [opt.replace('size=', '') for opt in config['storage-opts'] if 'size=' in opt]
			if len(sizes) > 0:
				return humanfriendly.parse_size(sizes[0]) / 1000000000
		
		# The default limit on image size is 20GB
		# (https://docs.microsoft.com/en-us/visualstudio/install/build-tools-container-issues)
		return 20.0
	
	@staticmethod
	def listImages(tagFilter = None, filters = {}):
		'''
		Retrieves the details for each image matching the specified filters
		'''
		
		# Retrieve the list of images matching the specified filters
		client = docker.from_env()
		images = client.images.list(filters=filters)
		
		# Apply our tag filter if one was specified
		if tagFilter is not None:
			images = [i for i in images if len(i.tags) > 0 and len(fnmatch.filter(i.tags, tagFilter)) > 0]
		
		return images
	
	@staticmethod
	def exec(container, command, **kwargs):
		'''
		Executes a command in a container returned by `DockerUtils.start()` and returns the output
		'''
		result, output = container.exec_run(command, **kwargs)
		if result is not None and result != 0:
			container.stop()
			raise RuntimeError(
				'Failed to run command {} in container. Process returned exit code {} with output: {}'.format(
					command,
					result,
					output
				)
			)
		
		return output
	
	@staticmethod
	def execMultiple(container, commands, **kwargs):
		'''
		Executes multiple commands in a container returned by `DockerUtils.start()`
		'''
		for command in commands:
			DockerUtils.exec(container, command, **kwargs)
	
	@staticmethod
	def injectPostRunMessage(dockerfile, platform, messageLines):
		'''
		Injects the supplied message at the end of each RUN directive in the specified Dockerfile
		'''
		
		# Generate the `echo` command for each line of the message
		prefix = 'echo.' if platform == 'windows' else "echo '"
		suffix = '' if platform == 'windows' else "'"
		echoCommands = ''.join([' && {}{}{}'.format(prefix, line, suffix) for line in messageLines])
		
		# Read the Dockerfile contents and convert all line endings to \n
		contents = FilesystemUtils.readFile(dockerfile)
		contents = contents.replace('\r\n', '\n')
		
		# Determine the escape character for the Dockerfile
		escapeMatch = re.search('#[\\s]*escape[\\s]*=[\\s]*([^\n])\n', contents)
		escape = escapeMatch[1] if escapeMatch is not None else '\\'
		
		# Identify each RUN directive in the Dockerfile
		runMatches = re.finditer('^RUN(.+?[^{}])\n'.format(re.escape(escape)), contents, re.DOTALL | re.MULTILINE)
		if runMatches is not None:
			for match in runMatches:
				
				# Append the `echo` commands to the directive
				contents = contents.replace(match[0], 'RUN{}{}\n'.format(match[1], echoCommands))
		
		# Write the modified contents back to the Dockerfile
		FilesystemUtils.writeFile(dockerfile, contents)
