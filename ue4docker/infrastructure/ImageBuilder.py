from .DockerUtils import DockerUtils
import humanfriendly, os, subprocess, time

class ImageBuilder(object):
	
	def __init__(self, root, prefix, platform, logger):
		'''
		Creates an ImageBuilder for the specified build context root, image name prefix, and platform
		'''
		self.root = root
		self.prefix = prefix
		self.platform = platform
		self.logger = logger
	
	def build(self, name, tag, args, rebuild=False, dryRun=False):
		'''
		Builds the specified image if it doesn't exist (use rebuild=True to force a rebuild)
		'''
		
		# Determine if we are building the image
		fullName = '{}{}:{}'.format(self.prefix, name, tag)
		if DockerUtils.exists(fullName) == True and rebuild == False:
			self.logger.info('Image "{}" exists and rebuild not requested, skipping build.'.format(fullName))
			return
		
		# Determine if we are running in "dry run" mode
		self.logger.action('Building image "{}"...'.format(fullName))
		buildCommand = DockerUtils.build(fullName, self.context(name), args)
		if dryRun == True:
			print(buildCommand)
			self.logger.action('Completed dry run for image "{}".'.format(fullName), newline=False)
			return
		
		# Attempt to build the image
		startTime = time.time()
		exitCode = subprocess.call(buildCommand)
		endTime = time.time()
		
		# Determine if the build succeeded
		if exitCode == 0:
			self.logger.action('Built image "{}" in {}'.format(
				fullName,
				humanfriendly.format_timespan(endTime - startTime)
			), newline=False)
		else:
			raise RuntimeError('failed to build image "{}".'.format(fullName))
	
	def context(self, name):
		'''
		Resolve the full path to the build context for the specified image
		'''
		return os.path.join(self.root, name, self.platform)
