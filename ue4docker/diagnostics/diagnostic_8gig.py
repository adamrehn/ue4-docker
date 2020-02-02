from ..infrastructure import DockerUtils, WindowsUtils
from .base import DiagnosticBase

import os, platform
from os.path import abspath, dirname, join

class diagnostic8Gig(DiagnosticBase):
	
	# The tag we use for built images
	IMAGE_TAG = 'adamrehn/ue4-docker/diagnostics:8gig'
	
	def getName(self):
		'''
		Returns the human-readable name of the diagnostic
		'''
		return 'Check for Docker 8GiB filesystem layer bug'
	
	def getDescription(self):
		'''
		Returns a description of what the diagnostic does
		'''
		return '\n'.join([
			'This diagnostic determines if the Docker daemon suffers from the 8GiB filesystem',
			'layer bug reported here: https://github.com/moby/moby/issues/37581',
			'',
			'This bug was fixed in Docker CE 18.09.0, but still exists in some versions of',
			'Docker CE under Windows 10 and Docker EE under Windows Server.',
			'',
			'You can force the use of a Linux image under Windows hosts by specifying the',
			'--linux flag, which can be useful when testing Docker Desktop or LCOW support.'
		])
	
	def run(self, logger, args=[]):
		'''
		Runs the diagnostic
		'''
		
		# Determine which image platform we will build the Dockerfile for (default is the host platform unless overridden)
		containerPlatform = 'linux' if '--linux' in args or platform.system().lower() != 'windows' else 'windows'
		
		# Verify that the user isn't trying to test Windows containers under Windows 10 when in Linux container mode (or vice versa)
		dockerPlatform = DockerUtils.info()['OSType'].lower()
		if containerPlatform == 'windows' and dockerPlatform == 'linux':
			logger.error('[8gig] Error: attempting to test Windows containers while Docker Desktop is in Linux container mode.', False)
			logger.error('[8gig] Use the --linux flag if you want to test Linux containers instead.', False)
			return False
		elif containerPlatform == 'linux' and dockerPlatform == 'windows':
			logger.error('[8gig] Error: attempting to test Linux containers while Docker Desktop is in Windows container mode.', False)
			logger.error('[8gig] Remove the --linux flag if you want to test Windows containers instead.', False)
			return False
		
		# Under Windows host systems, determine the appropriate container image base tag
		buildArgs = [
			'-m', '4GiB',
			'--build-arg',
			'BASETAG=' + WindowsUtils.getReleaseBaseTag(WindowsUtils.getWindowsRelease())
		] if containerPlatform == 'windows' else []
		
		# Attempt to build the Dockerfile
		contextDir = join(dirname(dirname(abspath(__file__))), 'dockerfiles', 'diagnostics', '8gig', containerPlatform)
		try:
			logger.action('[8gig] Attempting to build an image with an 8GiB filesystem layer...', False)
			command = ['docker', 'build', '-t', diagnostic8Gig.IMAGE_TAG, contextDir] + buildArgs
			self._printAndRun(logger, '[8gig] ', command, check=True)
			built = True
		except:
			logger.error('[8gig] Build failed!')
			built = False
		
		# Remove any built images, including intermediate images
		logger.action('[8gig] Cleaning up...', False)
		if built == True:
			self._printAndRun(logger, '[8gig] ', ['docker', 'rmi', diagnostic8Gig.IMAGE_TAG])
		self._printAndRun(logger, '[8gig] ', ['docker', 'system', 'prune', '-f'])
		
		# Inform the user of the outcome of the diagnostic
		if built == True:
			logger.action('[8gig] Diagnostic succeeded! The Docker daemon can build images with 8GiB filesystem layers.\n')
		else:
			logger.error('[8gig] Diagnostic failed! The Docker daemon cannot build images with 8GiB filesystem layers.\n', True)
		
		return built
