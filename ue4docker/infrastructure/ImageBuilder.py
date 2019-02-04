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
	
	def build(self, name, tags, args, rebuild=False, dryRun=False):
		'''
		Builds the specified image if it doesn't exist (use rebuild=True to force a rebuild)
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
		imageTags = ['{}{}:{}'.format(self.prefix, name, tag) for tag in tags]
		self._processImage(
			imageTags[0],
			DockerUtils.build(imageTags, self.context(name), args),
			'build',
			'built',
			rebuild=rebuild,
			dryRun=dryRun
		)
	
	def context(self, name):
		'''
		Resolve the full path to the build context for the specified image
		'''
		return os.path.join(self.root, name, self.platform)
	
	def pull(self, image, rebuild=False, dryRun=False):
		'''
		Pulls the specified image if it doesn't exist (use rebuild=True to force a pull of a newer version)
		'''
		self._processImage(
			image,
			DockerUtils.pull(image),
			'pull',
			'pulled',
			rebuild=rebuild,
			dryRun=dryRun
		)
	
	def _processImage(self, image, command, actionPresentTense, actionPastTense, rebuild=False, dryRun=False):
		'''
		Processes the specified image by running the supplied command if it doesn't exist (use rebuild=True to force processing)
		'''
		
		# Determine if we are processing the image
		if DockerUtils.exists(image) == True and rebuild == False:
			self.logger.info('Image "{}" exists and rebuild not requested, skipping {}.'.format(image, actionPresentTense))
			return
		
		# Determine if we are running in "dry run" mode
		self.logger.action('{}ing image "{}"...'.format(actionPresentTense.capitalize(), image))
		if dryRun == True:
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
