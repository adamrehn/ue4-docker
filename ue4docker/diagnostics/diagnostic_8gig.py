from ..infrastructure import DockerUtils, WindowsUtils
from .base import DiagnosticBase

import argparse, os, platform
from os.path import abspath, dirname, join

class diagnostic8Gig(DiagnosticBase):
	
	# The tag we use for built images
	IMAGE_TAG = 'adamrehn/ue4-docker/diagnostics:8gig'
	
	def __init__(self):
		
		# Setup our argument parser so we can use its help message output in our description text
		self._parser = argparse.ArgumentParser(prog='ue4-docker diagnostics 8gig')
		self._parser.add_argument('--linux', action='store_true', help="Use Linux containers under Windows hosts (useful when testing Docker Desktop or LCOW support)")
		self._parser.add_argument('--isolation', default=None, choices=['hyperv', 'process'], help="Override the default isolation mode when testing Windows containers")
		self._parser.add_argument('-basetag', default=None, choices=WindowsUtils.getValidBaseTags(), help="Override the default base image tag when testing Windows containers")
	
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
			self._parser.format_help()
		])
	
	def run(self, logger, args=[]):
		'''
		Runs the diagnostic
		'''
		
		# Parse our supplied arguments
		args = self._parser.parse_args(args)
		
		# Determine which image platform we will build the Dockerfile for (default is the host platform unless overridden)
		containerPlatform = 'linux' if args.linux == True or platform.system().lower() != 'windows' else 'windows'
		
		# Verify that the user isn't trying to test Windows containers under Windows 10 when in Linux container mode (or vice versa)
		dockerInfo = DockerUtils.info()
		dockerPlatform = dockerInfo['OSType'].lower()
		if containerPlatform == 'windows' and dockerPlatform == 'linux':
			logger.error('[8gig] Error: attempting to test Windows containers while Docker Desktop is in Linux container mode.', False)
			logger.error('[8gig] Use the --linux flag if you want to test Linux containers instead.', False)
			return False
		elif containerPlatform == 'linux' and dockerPlatform == 'windows':
			logger.error('[8gig] Error: attempting to test Linux containers while Docker Desktop is in Windows container mode.', False)
			logger.error('[8gig] Remove the --linux flag if you want to test Windows containers instead.', False)
			return False
		
		# Set our build arguments when testing Windows containers
		buildArgs = []
		if containerPlatform == 'windows':
			
			# Determine the appropriate container image base tag for the host system release unless the user specified a base tag
			defaultBaseTag = WindowsUtils.getReleaseBaseTag(WindowsUtils.getWindowsRelease())
			baseTag = args.basetag if args.basetag is not None else defaultBaseTag
			buildArgs = ['--build-arg', 'BASETAG={}'.format(baseTag)]
			
			# Use the default isolation mode unless requested otherwise
			isolation = args.isolation if args.isolation is not None else dockerInfo['Isolation']
			buildArgs += ['--isolation={}'.format(isolation)]
			
			# If the user specified process isolation mode and a different base tag to the host system then warn them
			if isolation == 'process' and baseTag != defaultBaseTag:
				logger.info('[8gig] Warning: attempting to use different Windows container/host versions', False)
				logger.info('[8gig] when running in process isolation mode, this will usually break!', False)
			
			# Set a sensible memory limit when using Hyper-V isolation mode
			if isolation == 'hyperv':
				buildArgs += ['-m', '4GiB']
		
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
