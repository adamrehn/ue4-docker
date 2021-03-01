from .DockerUtils import DockerUtils
from .FilesystemUtils import FilesystemUtils
from .GlobalConfiguration import GlobalConfiguration
import glob, humanfriendly, os, shutil, subprocess, tempfile, time
from os.path import basename, exists, join
from jinja2 import Environment, Template

class ImageBuilder(object):
	
	def __init__(self, root, platform, logger, rebuild=False, dryRun=False, layoutDir=None, templateContext=None, combine=False):
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
		self.combine = combine
	
	def build(self, name, tags, args, secrets=None):
		'''
		Builds the specified image if it doesn't exist or if we're forcing a rebuild
		'''
		
		# Create a Jinja template environment and render the Dockerfile template
		environment = Environment(autoescape=False, trim_blocks=True, lstrip_blocks=True)
		dockerfile = join(self.context(name), 'Dockerfile')
		templateInstance = environment.from_string(FilesystemUtils.readFile(dockerfile))
		rendered = templateInstance.render(self.templateContext)
		
		# Compress excess whitespace introduced during Jinja rendering and save the contents back to disk
		# (Ensure that we still have a single trailing newline at the end of the Dockerfile)
		while '\n\n\n' in rendered:
			rendered = rendered.replace('\n\n\n', '\n\n')
		rendered = rendered.strip('\n') + '\n'
		FilesystemUtils.writeFile(dockerfile, rendered)
		
		# Inject our filesystem layer commit message after each RUN directive in the Dockerfile
		DockerUtils.injectPostRunMessage(dockerfile, self.platform, [
			'',
			'RUN directive complete. Docker will now commit the filesystem layer to disk.',
			'Note that for large filesystem layers this can take quite some time.',
			'Performing filesystem layer commit...',
			''
		])
		
		# Create a temporary directory to hold any files needed for the build
		with tempfile.TemporaryDirectory() as tempDir:
			
			# Determine whether we are building using `docker buildx` with build secrets
			imageTags = self._formatTags(name, tags)
			command = DockerUtils.build(imageTags, self.context(name), args)
			if self.platform == 'linux' and secrets is not None and len(secrets) > 0:
				
				# Create temporary files to store the contents of each of our secrets
				secretFlags = []
				for secret, contents in secrets.items():
					secretFile = join(tempDir, secret)
					FilesystemUtils.writeFile(secretFile, contents)
					secretFlags.append('id={},src={}'.format(secret, secretFile))
				
				# Generate the `docker buildx` command to use our build secrets
				command = DockerUtils.buildx(imageTags, self.context(name), args, secretFlags)
			
			# Build the image if it doesn't already exist
			self._processImage(
				imageTags[0],
				name,
				command,
				'build',
				'built'
			)
	
	def context(self, name):
		'''
		Resolve the full path to the build context for the specified image
		'''
		return join(self.root, basename(name), self.platform)
	
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
			
			# Determine whether we're performing a simple copy or combining generated Dockerfiles
			source = self.context(name)
			if self.combine == True:
				
				# Ensure the destination directory exists
				dest = join(self.layoutDir, 'combined')
				self.logger.action('Merging "{}" into "{}"...'.format(source, dest), newline=False)
				os.makedirs(dest, exist_ok=True)
				
				# Merge the source Dockerfile with any existing Dockerfile contents in the destination directory
				# (Insert a single newline between merged file contents and ensure we have a single trailing newline)
				sourceDockerfile = join(source, 'Dockerfile')
				destDockerfile = join(dest, 'Dockerfile')
				dockerfileContents = FilesystemUtils.readFile(destDockerfile) if exists(destDockerfile) else ''
				dockerfileContents = dockerfileContents + '\n' + FilesystemUtils.readFile(sourceDockerfile)
				dockerfileContents = dockerfileContents.strip('\n') + '\n'
				FilesystemUtils.writeFile(destDockerfile, dockerfileContents)
				
				# Copy any supplemental files from the source directory to the destination directory
				# (Exclude any extraneous files which are not referenced in the Dockerfile contents)
				for file in glob.glob(join(source, '*.*')):
					if basename(file) in dockerfileContents:
						shutil.copy(file, join(dest, basename(file)))
				
				# Report our success
				self.logger.action('Merged Dockerfile for image "{}".'.format(image), newline=False)
				
			else:
				
				# Copy the source directory to the destination
				dest = join(self.layoutDir, basename(name))
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
