from .DockerUtils import DockerUtils
from .GlobalConfiguration import GlobalConfiguration
import humanfriendly, os, subprocess, time

class ImageBuilder(object):
	
	def __init__(self, root, platform, logger, rebuild=False, dryRun=False):
		'''
		Creates an ImageBuilder for the specified build parameters
		'''
		self.root = root
		self.platform = platform
		self.logger = logger
		self.rebuild = rebuild
		self.dryRun = dryRun
	
	def build(self, name, tags, args):
		'''
		Builds the specified image if it doesn't exist or if we're forcing a rebuild
		'''
		
		# Inject our filesystem layer commit message after each RUN directive in the Dockerfile
		dockerfile = os.path.join(self.context(name), 'Dockerfile')
		DockerUtils.injectPostRunMessage(dockerfile, self.platform, [
			'',
			'RUN directive complete. Docker will now commit the filesystem layer to disk.',
			'Note that for large filesystem layers this can take quite some time.',
			'Performing filesystem layer commit...',
			''
		])
		
		# Build the image if it doesn't already exist
		imageTags = self._formatTags(name, tags)
		self._processImage(
			imageTags[0],
			DockerUtils.build(imageTags, self.context(name), args),
			'build',
			'built'
		)
	
	def context(self, name):
		'''
		Resolve the full path to the build context for the specified image
		'''
		return os.path.join(self.root, os.path.basename(name), self.platform)
	
	def pull(self, image):
		'''
		Pulls the specified image if it doesn't exist or if we're forcing a pull of a newer version
		'''
		self._processImage(
			image,
			DockerUtils.pull(image),
			'pull',
			'pulled'
		)
	
	def willBuild(self, name, tags):
		'''
		Determines if we will build the specified image, based on our build settings
		'''
		imageTags = self._formatTags(name, tags)
		return self._willProcess(imageTags[0])
	
	def _formatTags(self, name, tags):
		'''
		Generates the list of fully-qualified tags that we will use when building an image
		'''
		return ['{}:{}'.format(GlobalConfiguration.resolveTag(name), tag) for tag in tags]
	
	def _willProcess(self, image):
		'''
		Determines if we will build or pull the specified image, based on our build settings
		'''
		return self.rebuild == True or DockerUtils.exists(image) == False
	
	def _processImage(self, image, command, actionPresentTense, actionPastTense):
		'''
		Processes the specified image by running the supplied command if it doesn't exist (use rebuild=True to force processing)
		'''
		
		# Determine if we are processing the image
		if self._willProcess(image) == False:
			self.logger.info('Image "{}" exists and rebuild not requested, skipping {}.'.format(image, actionPresentTense))
			return
		
		# Determine if we are running in "dry run" mode
		self.logger.action('{}ing image "{}"...'.format(actionPresentTense.capitalize(), image))
		if self.dryRun == True:
			print(command)
			self.logger.action('Completed dry run for image "{}".'.format(image), newline=False)
			return
		
		# Attempt to process the image using the supplied command
		startTime = time.time()
		exitCode = subprocess.call(command)
		endTime = time.time()
		
		# Determine if processing succeeded
		if exitCode == 0:
			self.logger.action('{} image "{}" in {}'.format(
				actionPastTense.capitalize(),
				image,
				humanfriendly.format_timespan(endTime - startTime)
			), newline=False)
		else:
			raise RuntimeError('failed to {} image "{}".'.format(actionPresentTense, image))
