from ..infrastructure import DockerUtils, WindowsUtils
from os.path import abspath, dirname, join
import subprocess

class DiagnosticBase(object):
	
	def getName(self):
		'''
		Returns the human-readable name of the diagnostic
		'''
		raise NotImplementedError
	
	def getDescription(self):
		'''
		Returns a description of what the diagnostic does
		'''
		raise NotImplementedError
	
	def getPrefix(self):
		'''
		Returns the short name of the diagnostic for use in log output
		'''
		raise NotImplementedError
	
	def run(self, logger, args=[]):
		'''
		Runs the diagnostic
		'''
		raise NotImplementedError
	
	
	# Helper functionality for derived classes
	
	def _printAndRun(self, logger, prefix, command, check=False):
		'''
		Prints a command and then executes it
		'''
		logger.info(prefix + 'Run: {}'.format(command), False)
		subprocess.run(command, check=check)
	
	def _checkPlatformMistmatch(self, logger, containerPlatform):
		'''
		Verifies that the user isn't trying to test Windows containers under Windows 10 when in Linux container mode (or vice versa)
		'''
		prefix = self.getPrefix()
		dockerInfo = DockerUtils.info()
		dockerPlatform = dockerInfo['OSType'].lower()
		if containerPlatform == 'windows' and dockerPlatform == 'linux':
			logger.error('[{}] Error: attempting to test Windows containers while Docker Desktop is in Linux container mode.'.format(prefix), False)
			logger.error('[{}] Use the --linux flag if you want to test Linux containers instead.'.format(prefix), False)
			raise RuntimeError
		elif containerPlatform == 'linux' and dockerPlatform == 'windows':
			logger.error('[{}] Error: attempting to test Linux containers while Docker Desktop is in Windows container mode.'.format(prefix), False)
			logger.error('[{}] Remove the --linux flag if you want to test Windows containers instead.'.format(prefix), False)
			raise RuntimeError
	
	def _generateWindowsBuildArgs(self, logger, basetagOverride=None, isolationOverride=None):
		'''
		Generates the build arguments for testing Windows containers, with optional overrides for base tag and isolation mode
		'''
		
		# Determine the appropriate container image base tag for the host system release unless the user specified a base tag
		buildArgs = []
		defaultBaseTag = WindowsUtils.getReleaseBaseTag(WindowsUtils.getWindowsRelease())
		baseTag = basetagOverride if basetagOverride is not None else defaultBaseTag
		buildArgs = ['--build-arg', 'BASETAG={}'.format(baseTag)]
		
		# Use the default isolation mode unless requested otherwise
		dockerInfo = DockerUtils.info()
		isolation = isolationOverride if isolationOverride is not None else dockerInfo['Isolation']
		buildArgs += ['--isolation={}'.format(isolation)]
		
		# If the user specified process isolation mode and a different base tag to the host system then warn them
		prefix = self.getPrefix()
		if isolation == 'process' and baseTag != defaultBaseTag:
			logger.info('[{}] Warning: attempting to use different Windows container/host versions'.format(prefix), False)
			logger.info('[{}] when running in process isolation mode, this will usually break!'.format(prefix), False)
		
		# Set a sensible memory limit when using Hyper-V isolation mode
		if isolation == 'hyperv':
			buildArgs += ['-m', '4GiB']
		
		return buildArgs
	
	def _buildDockerfile(self, logger, containerPlatform, tag, buildArgs):
		'''
		Attempts to build the diagnostic's Dockerfile for the specified container platform, with the specified parameters
		'''
		
		# Attempt to build the Dockerfile
		prefix = self.getPrefix()
		contextDir = join(dirname(dirname(abspath(__file__))), 'dockerfiles', 'diagnostics', prefix, containerPlatform)
		try:
			command = ['docker', 'build', '-t', tag, contextDir] + buildArgs
			self._printAndRun(logger, '[{}] '.format(prefix), command, check=True)
			built = True
		except:
			logger.error('[{}] Build failed!'.format(prefix))
			built = False
		
		# Remove any built images, including intermediate images
		logger.action('[{}] Cleaning up...'.format(prefix), False)
		if built == True:
			self._printAndRun(logger, '[{}] '.format(prefix), ['docker', 'rmi', tag])
		self._printAndRun(logger, '[{}] '.format(prefix), ['docker', 'system', 'prune', '-f'])
		
		# Report the success or failure of the build
		return built
