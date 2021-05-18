from ..infrastructure import DockerUtils, WindowsUtils
from .base import DiagnosticBase

import argparse, os, platform
from os.path import abspath, dirname, join

class diagnostic20Gig(DiagnosticBase):
	
	# The tag we use for built images
	IMAGE_TAG = 'adamrehn/ue4-docker/diagnostics:20gig'
	
	def __init__(self):
		
		# Setup our argument parser so we can use its help message output in our description text
		self._parser = argparse.ArgumentParser(prog='ue4-docker diagnostics 20gig')
		self._parser.add_argument('--isolation', default=None, choices=['hyperv', 'process'], help="Override the default isolation mode when testing Windows containers")
		self._parser.add_argument('-basetag', default=None, choices=WindowsUtils.getValidBaseTags(), help="Override the default base image tag when testing Windows containers")
	
	def getName(self):
		'''
		Returns the human-readable name of the diagnostic
		'''
		return 'Check for Docker 20GiB COPY bug'
	
	def getDescription(self):
		'''
		Returns a description of what the diagnostic does
		'''
		return '\n'.join([
			'This diagnostic determines if the Docker daemon suffers from 20GiB COPY bug',
			'reported at https://github.com/moby/moby/issues/37352 (affects Windows containers only)',
			'',
			'#37352 was fixed in https://github.com/moby/moby/pull/41636 but that fix was not released yet',
			'',
			self._parser.format_help()
		])
	
	def getPrefix(self):
		'''
		Returns the short name of the diagnostic for use in log output
		'''
		return '20gig'
	
	def run(self, logger, args=[]):
		'''
		Runs the diagnostic
		'''
		
		# Parse our supplied arguments
		args = self._parser.parse_args(args)
		
		# Determine which platform we are running on
		containerPlatform = platform.system().lower()

		if containerPlatform != 'windows':
			logger.action('[20gig] Diagnostic skipped. Current platform is not affected by the bug this diagnostic checks\n')
			return True

		buildArgs = self._generateWindowsBuildArgs(logger, args.basetag, args.isolation)
		
		# Attempt to build the Dockerfile
		logger.action('[20gig] Attempting to COPY more than 20GiB between layers...', False)
		built = self._buildDockerfile(logger, containerPlatform, diagnostic20Gig.IMAGE_TAG, buildArgs)
		
		# Inform the user of the outcome of the diagnostic
		if built == True:
			logger.action('[20gig] Diagnostic succeeded! The Docker daemon can COPY more than 20GiB between layers.\n')
		else:
			logger.error('[20gig] Diagnostic failed! The Docker daemon cannot COPY more than 20GiB between layers.\n', True)
		
		return built
