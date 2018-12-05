import docker, fnmatch, humanfriendly, json, os, platform

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
	def build(tag, context, args):
		'''
		Returns the `docker build` command to build an image
		'''
		return ['docker', 'build', '-t', tag, context] + args
	
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
