from .PackageUtils import PackageUtils
import os, platform

if platform.system() == 'Windows':
	import winreg

# Import the `semver` package even when the conflicting `node-semver` package is present
semver = PackageUtils.importFile('semver', os.path.join(PackageUtils.getPackageLocation('semver'), 'semver.py'))

class WindowsUtils(object):
	
	# The latest Windows build version we recognise as a non-Insider build
	_latestReleaseBuild = 17134
	
	# The list of Windows Server Core base image tags that we support, in ascending version number order
	_validTags = ['ltsc2016', '1709', '1803']
	
	@staticmethod
	def formatSystemName(release):
		'''
		Generates a human-readable version string for the Windows host system
		'''
		return 'Windows {} version {}'.format('Server' if WindowsUtils.isWindowsServer() else '10', release)
	
	@staticmethod
	def getWindowsVersion():
		'''
		Returns the version information for the Windows host system as a semver instance
		'''
		return semver.parse(platform.win32_ver()[1])
	
	@staticmethod
	def getWindowsRelease():
		'''
		Determines the Windows 10 / Windows Server release (1607, 1709, 1803, etc.) of the Windows host system
		'''
		key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
		releaseId = winreg.QueryValueEx(key, 'ReleaseId')
		winreg.CloseKey(key)
		return releaseId[0]
	
	@staticmethod
	def isSupportedWindowsVersion():
		'''
		Verifies that the Windows host system is Windows 10 / Windows Server 2016 version 1607 or newer
		
		(1607 is the first build to support Windows containers, as per:
		<https://docs.microsoft.com/en-us/virtualization/windowscontainers/deploy-containers/version-compatibility>)
		'''
		version = WindowsUtils.getWindowsVersion()
		return version['major'] == 10 and version['patch'] >= 14393
	
	@staticmethod
	def isWindowsServer():
		'''
		Determines if the Windows host system is Windows Server
		'''
		key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
		productName = winreg.QueryValueEx(key, 'ProductName')
		winreg.CloseKey(key)
		return 'Windows Server' in productName[0]
	
	@staticmethod
	def isInsiderPreview():
		'''
		Determines if the Windows host system is a Windows Insider preview build
		'''
		version = WindowsUtils.getWindowsVersion()
		return version['patch'] > WindowsUtils._latestReleaseBuild
	
	@staticmethod
	def getReleaseBaseTag(release):
		'''
		Retrieves the tag for the Windows Server Core base image matching the specified Windows 10 / Windows Server release
		'''
		
		# For Windows Insider preview builds, build the latest release tag
		if WindowsUtils.isInsiderPreview():
			return WindowsUtils._validTags[-1]
		
		# This lookup table is based on the list of valid tags from <https://hub.docker.com/r/microsoft/windowsservercore/>
		return {
			'1709': '1709',
			'1803': '1803',
		}.get(release, 'ltsc2016')
	
	@staticmethod
	def getValidBaseTags():
		'''
		Returns the list of valid tags for the Windows Server Core base image, in ascending chronological release order
		'''
		return WindowsUtils._validTags
	
	@staticmethod
	def isValidBaseTag(tag):
		'''
		Determines if the specified tag is a valid Windows Server Core base image tag
		'''
		return tag in WindowsUtils._validTags
	
	@staticmethod
	def isNewerBaseTag(older, newer):
		'''
		Determines if the base tag `newer` is chronologically newer than the base tag `older`
		'''
		return WindowsUtils._validTags.index(newer) > WindowsUtils._validTags.index(older)
