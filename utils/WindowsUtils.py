from .PackageUtils import PackageUtils
import os, platform

# Import the `semver` package even when the conflicting `node-semver` package is present
semver = PackageUtils.importFile('semver', os.path.join(PackageUtils.getPackageLocation('semver'), 'semver.py'))

class WindowsUtils(object):
	
	# The list of Windows Server Core base image tags that we support
	_validTags = ['ltsc2016', '1709', '1803']
	
	@staticmethod
	def getWindowsRelease():
		'''
		Determines the Windows 10 / Windows Server release (1607, 1709, 1803, etc.) of the Windows host system
		'''
		
		# This lookup table is based on the data from these pages:
		#  <https://www.microsoft.com/en-us/itpro/windows-10/release-information>
		# and
		#  <https://docs.microsoft.com/en-us/windows-server/get-started/windows-server-release-info>)
		releases = {
			10240: 1507,
			14393: 1607,
			15063: 1703,
			16299: 1709,
			17134: 1803
		}
		
		# Determine which Windows release the OS build number corresponds to
		osBuild = semver.parse(platform.win32_ver()[1])
		if osBuild['patch'] in releases:
			return releases[osBuild['patch']]
		else:
			raise RuntimeError('unrecognised Windows build "{}"'.format(semver.format_version(osBuild['major'], osBuild['minor'], osBuild['patch'])))
	
	@staticmethod
	def getReleaseBaseTag(release):
		'''
		Retrieves the tag for the Windows Server Core base image matching the specified Windows 10 / Windows Server release
		'''
		
		# This lookup table is based on the list of valid tags from <https://hub.docker.com/r/microsoft/windowsservercore/>
		return {
			1507: 'ltsc2016',
			1607: 'ltsc2016',
			1703: 'ltsc2016',
			1709: '1709',
			1803: '1803'
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
		Determines if the base tag `newer` is actually newer than the base tag `older`
		'''
		return WindowsUtils._validTags.index(newer) > WindowsUtils._validTags.index(older)
