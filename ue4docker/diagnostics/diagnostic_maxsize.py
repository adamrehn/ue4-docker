from ..infrastructure import DockerUtils, WindowsUtils
from .base import DiagnosticBase
import platform

class diagnosticMaxSize(DiagnosticBase):
	
	def getName(self):
		'''
		Returns the human-readable name of the diagnostic
		'''
		return 'Check for Windows storage-opt bug'
	
	def getDescription(self):
		'''
		Returns a description of what the diagnostic does
		'''
		return '\n'.join([
			'This diagnostic determines if the Windows host OS suffers from the bug that',
			'prevents users from increasing the maximum allowed image size using Docker\'s',
			'`storage-opt` configuration key, as reported here:',
			'https://github.com/docker/for-win/issues/4100',
			'',
			'This bug is present in Windows Server and Windows 10 versions 1903 and 1909,',
			'but a workaround was introduced in Docker CE version 19.03.6.',
		])
	
	def getPrefix(self):
		'''
		Returns the short name of the diagnostic for use in log output
		'''
		return 'maxsize'
	
	def run(self, logger, args=[]):
		'''
		Runs the diagnostic
		'''
		
		# Verify that we are running under Windows and are in Windows container mode if using Docker Desktop
		dockerPlatform = DockerUtils.info()['OSType'].lower()
		hostPlatform = platform.system().lower()
		if hostPlatform != 'windows':
			logger.info('[maxsize] This diagnostic only applies to Windows host systems.', False)
			return True
		elif dockerPlatform != 'windows':
			logger.error('[maxsize] Error: Docker Desktop is currently in Linux container mode.', False)
			logger.error('[maxsize] Please switch to Windows container mode to run this diagnostic.', False)
			return False
		
		# Verify that we are running Windows Server or Windows 10 version 1903 or newer
		if WindowsUtils.getWindowsBuild() < 18362:
			logger.info('[maxsize] This diagnostic only applies to Windows Server and Windows 10 version 1903 and newer.', False)
			return True
		
		# Attempt to run a Windows Nanoserver 1903 container with the `storage-mode` configuration options set
		# (The bug doesn't seem to be triggered when using older Windows images, presumably because they use an older host kernel)
		try:
			command = ['docker', 'run', '--rm', '--storage-opt', 'size=200GB', 'mcr.microsoft.com/windows/nanoserver:1903', 'cmd', 'exit']
			self._printAndRun(logger, '[maxsize] ', command, check=True)
			logger.action('[maxsize] Diagnostic succeeded! The host platform can specify maximum image sizes using Docker\'s `storage-opt` configuration key.\n')
			return True
		except:
			logger.error('[maxsize] Diagnostic failed! The host platform cannot specify maximum image sizes using Docker\'s `storage-opt` configuration key.\n', True)
			return False
