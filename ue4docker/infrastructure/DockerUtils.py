import docker, humanfriendly, json, os

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
	def maxsize():
		'''
		Determines the configured size limit (in GB) for Windows containers
		'''
		with open('{}\\Docker\\config\\daemon.json'.format(os.environ['ProgramData'])) as configFile:
			config = json.load(configFile)
			if 'storage-opts' in config:
				sizes = [opt.replace('size=', '') for opt in config['storage-opts'] if 'size=' in opt]
				if len(sizes) > 0:
					return humanfriendly.parse_size(sizes[0]) / 1000000000
		
		# The default limit on image size is 20GB
		# (https://docs.microsoft.com/en-us/visualstudio/install/build-tools-container-issues)
		return 20.0
