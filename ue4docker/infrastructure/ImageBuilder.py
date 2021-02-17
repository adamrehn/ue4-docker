from .DockerUtils import DockerUtils
from .FilesystemUtils import FilesystemUtils
from .GlobalConfiguration import GlobalConfiguration
import humanfriendly, os, shutil, subprocess, time
from jinja2 import Environment, Template

class ImageBuilder(object):
	
	def __init__(self, root, platform, logger, rebuild=False, dryRun=False, layoutDir=None, templateContext=None):
		'''
		Creates an ImageBuilder for the specified build parameters
		'''
		self.root = root
		self.platform = platform
		self.logger = logger
		self.rebuild = rebuild
		self.dryRun = dryRun
		self.layoutDir = layoutDir
		self.templateContext = templateContext if templateContext is not None else {}
	
	def build(self, name, tags, args):
		'''
		Builds the specified image if it doesn't exist or if we're forcing a rebuild
		'''
		
		# Create a Jinja template environment and render the Dockerfile template
		environment = Environment(autoescape=False)
		dockerfile = os.path.join(self.context(name), 'Dockerfile')
		templateInstance = environment.from_string(FilesystemUtils.readFile(dockerfile))
		rendered = templateInstance.render(self.templateContext)
		FilesystemUtils.writeFile(dockerfile, rendered)
		
		# Inject our filesystem layer commit message after each RUN directive in the Dockerfile
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
			name,
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
			None,
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
	
	def _processImage(self, image, name, command, actionPresentTense, actionPastTense):
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
		
		# Determine if we're just copying the Dockerfile to an output directory
		if self.layoutDir is not None:
			source = self.context(name)
			dest = os.path.join(self.layoutDir, os.path.basename(name))
			self.logger.action('Copying "{}" to "{}"...'.format(source, dest), newline=False)
			shutil.copytree(source, dest)
			self.logger.action('Copied Dockerfile for image "{}".'.format(image), newline=False)
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
