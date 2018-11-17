from .PackageUtils import PackageUtils
import os, platform

# Import the `semver` package even when the conflicting `node-semver` package is present
semver = PackageUtils.importFile('semver', os.path.join(PackageUtils.getPackageLocation('semver'), 'semver.py'))

class DarwinUtils(object):
	
	@staticmethod
	def minimumRequiredVersion():
		'''
		Returns the minimum required version of macOS, which is 10.10.3 Yosemite
		
		(10.10.3 is the minimum required version for Docker for Mac, as per:
		<https://store.docker.com/editions/community/docker-ce-desktop-mac>)
		'''
		return '10.10.3'
	
	@staticmethod
	def systemString():
		'''
		Generates a human-readable version string for the macOS host system
		'''
		return 'macOS {} (Kernel Version {})'.format(
			platform.mac_ver()[0],
			platform.uname().release
		)
	
	@staticmethod
	def getMacOsVersion():
		'''
		Returns the version number for the macOS host system
		'''
		return platform.mac_ver()[0]
	
	@staticmethod
	def isSupportedMacOsVersion():
		'''
		Verifies that the macOS host system meets our minimum version requirements
		'''
		return semver.compare(DarwinUtils.getMacOsVersion(), DarwinUtils.minimumRequiredVersion()) >= 0
