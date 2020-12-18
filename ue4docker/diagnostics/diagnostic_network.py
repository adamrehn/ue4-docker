from ..infrastructure import DockerUtils, WindowsUtils
from .base import DiagnosticBase
import argparse, platform

class diagnosticNetwork(DiagnosticBase):
	
	# The tag we use for built images
	IMAGE_TAG = 'adamrehn/ue4-docker/diagnostics:network'
	
	def __init__(self):
		
		# Setup our argument parser so we can use its help message output in our description text
		self._parser = argparse.ArgumentParser(prog='ue4-docker diagnostics network')
		self._parser.add_argument('--linux', action='store_true', help="Use Linux containers under Windows hosts (useful when testing Docker Desktop or LCOW support)")
		self._parser.add_argument('--isolation', default=None, choices=['hyperv', 'process'], help="Override the default isolation mode when testing Windows containers")
		self._parser.add_argument('-basetag', default=None, choices=WindowsUtils.getValidBaseTags(), help="Override the default base image tag when testing Windows containers")
	
	def getName(self):
		'''
		Returns the human-readable name of the diagnostic
		'''
		return 'Check that containers can access the internet correctly'
	
	def getDescription(self):
		'''
		Returns a description of what the diagnostic does
		'''
		return '\n'.join([
			'This diagnostic determines if running containers are able to access the internet,',
			'resolve DNS entries, and download remote files.',
			'',
			'This is primarily useful in troubleshooting network connectivity and proxy issues.'
		])
	
	def getPrefix(self):
		'''
		Returns the short name of the diagnostic for use in log output
		'''
		return 'network'
	
	def run(self, logger, args=[]):
		'''
		Runs the diagnostic
		'''
		
		# Parse our supplied arguments
		args = self._parser.parse_args(args)
		
		# Determine which image platform we will build the Dockerfile for (default is the host platform unless overridden)
		containerPlatform = 'linux' if args.linux == True or platform.system().lower() != 'windows' else 'windows'
		
		# Verify that the user isn't trying to test Windows containers under Windows 10 when in Linux container mode (or vice versa)
		try:
			self._checkPlatformMistmatch(logger, containerPlatform)
		except RuntimeError:
			return False
		
		# Set our build arguments when testing Windows containers
		buildArgs = self._generateWindowsBuildArgs(logger, args.basetag, args.isolation) if containerPlatform == 'windows' else []
		
		# Attempt to build the Dockerfile
		logger.action('[network] Attempting to build an image that accesses network resources...', False)
		built = self._buildDockerfile(logger, containerPlatform, diagnosticNetwork.IMAGE_TAG, buildArgs)
		
		# Inform the user of the outcome of the diagnostic
		if built == True:
			logger.action('[network] Diagnostic succeeded! Running containers can access network resources without any issues.\n')
		else:
			logger.error('[network] Diagnostic failed! Running containers cannot access network resources. See the docs for troubleshooting tips:', True)
			logger.error('[network] https://docs.adamrehn.com/ue4-docker/building-images/troubleshooting-build-issues#building-the-ue4-build-prerequisites-image-fails-with-a-network-related-error\n', False)
		
		return built
