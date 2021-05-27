from .DockerUtils import DockerUtils
from pkg_resources import parse_version
import platform, sys

if platform.system() == 'Windows':
	import winreg

class WindowsUtils(object):

	# The latest Windows build version we recognise as a non-Insider build
	_latestReleaseBuild = 19042

	# The list of Windows Server Core base image tags that we recognise, in ascending version number order
	_validTags = ['ltsc2016', '1709', '1803', 'ltsc2019', '1903', '1909', '2004', '20H2']

	# The list of Windows Server and Windows 10 host OS releases that are blacklisted due to critical bugs
	# (See: <https://unrealcontainers.com/docs/concepts/windows-containers>)
	_blacklistedReleases = ['1903', '1909']

	# The list of Windows Server Core container image releases that are unsupported due to having reached EOL
	_eolReleases = ['1703', '1709', '1803', '1903', '1909']

	@staticmethod
	def _getVersionRegKey(subkey : str) -> str:
		'''
		Retrieves the specified Windows version key from the registry

		@raises FileNotFoundError if registry key doesn't exist
		'''
		key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion')
		value = winreg.QueryValueEx(key, subkey)
		winreg.CloseKey(key)
		return value[0]

	@staticmethod
	def requiredHostDlls(basetag: str) -> [str]:
		'''
		Returns the list of required host DLL files for the specified container image base tag
		'''

		# `ddraw.dll` is only required under Windows Server 2016 version 1607
		common = ['dsound.dll', 'opengl32.dll', 'glu32.dll']
		return ['ddraw.dll'] + common if basetag == 'ltsc2016' else common

	@staticmethod
	def requiredSizeLimit() -> float:
		'''
		Returns the minimum required image size limit (in GB) for Windows containers
		'''
		return 400.0

	@staticmethod
	def minimumRequiredBuild() -> int:
		'''
		Returns the minimum required version of Windows 10 / Windows Server, which is release 1607

		(1607 is the first build to support Windows containers, as per:
		<https://docs.microsoft.com/en-us/virtualization/windowscontainers/deploy-containers/version-compatibility>)
		'''
		return 14393

	@staticmethod
	def systemString() -> str:
		'''
		Generates a verbose human-readable version string for the Windows host system
		'''
		return '{} Version {} (Build {}.{})'.format(
			WindowsUtils._getVersionRegKey('ProductName'),
			WindowsUtils.getWindowsRelease(),
			WindowsUtils.getWindowsBuild(),
			WindowsUtils._getVersionRegKey('UBR')
		)

	@staticmethod
	def getWindowsRelease() -> str:
		'''
		Determines the Windows 10 / Windows Server release (1607, 1709, 1803, etc.) of the Windows host system
		'''
		return WindowsUtils._getVersionRegKey('ReleaseId')

	@staticmethod
	def getWindowsBuild() -> int:
		'''
		Returns build number for the Windows host system
		'''
		return sys.getwindowsversion().build

	@staticmethod
	def isBlacklistedWindowsVersion(release=None):
		'''
		Determines if the specified Windows release is one with bugs that make it unsuitable for use
		(defaults to checking the host OS release if one is not specified)
		'''
		dockerVersion = parse_version(DockerUtils.version()['Version'])
		release = WindowsUtils.getWindowsRelease() if release is None else release
		return release in WindowsUtils._blacklistedReleases and dockerVersion < parse_version('19.03.6')

	@staticmethod
	def isEndOfLifeWindowsVersion(release=None):
		'''
		Determines if the specified Windows release is one that has reached End Of Life (EOL)
		(defaults to checking the host OS release if one is not specified)
		'''
		release = WindowsUtils.getWindowsRelease() if release is None else release
		return release in WindowsUtils._eolReleases

	@staticmethod
	def isWindowsServer() -> bool:
		'''
		Determines if the Windows host system is Windows Server
		'''
		# TODO: Replace this with something more reliable
		return 'Windows Server' in WindowsUtils._getVersionRegKey('ProductName')

	@staticmethod
	def isInsiderPreview() -> bool:
		'''
		Determines if the Windows host system is a Windows Insider preview build
		'''
		return WindowsUtils.getWindowsBuild() > WindowsUtils._latestReleaseBuild

	@staticmethod
	def getReleaseBaseTag(release: str) -> str:
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
			'1809': 'ltsc2019',
			'1903': '1903',
			'1909': '1909',
			'2004': '2004',
			'2009': '20H2',
			'20H2': '20H2'
		}.get(release, 'ltsc2016')

	@staticmethod
	def getValidBaseTags() -> [str]:
		'''
		Returns the list of valid tags for the Windows Server Core base image, in ascending chronological release order
		'''
		return WindowsUtils._validTags

	@staticmethod
	def isValidBaseTag(tag: str) -> bool:
		'''
		Determines if the specified tag is a valid Windows Server Core base image tag
		'''
		return tag in WindowsUtils._validTags

	@staticmethod
	def isNewerBaseTag(older: str, newer: str) -> bool:
		'''
		Determines if the base tag `newer` is chronologically newer than the base tag `older`
		'''
		return WindowsUtils._validTags.index(newer) > WindowsUtils._validTags.index(older)

	@staticmethod
	def supportsProcessIsolation() -> bool:
		'''
		Determines whether the Windows host system supports process isolation for containers

		@see https://docs.microsoft.com/en-us/virtualization/windowscontainers/manage-containers/hyperv-container
		'''
		return WindowsUtils.isWindowsServer() or WindowsUtils.getWindowsBuild() >= 17763
