from .PackageUtils import PackageUtils
from .WindowsUtils import WindowsUtils
import os, platform, random

# Import the `semver` package even when the conflicting `node-semver` package is present
semver = PackageUtils.importFile('semver', os.path.join(PackageUtils.getPackageLocation('semver'), 'semver.py'))

# The base images for Linux containers
LINUX_BASE_IMAGES = {
	'default': 'ubuntu:18.04',
	'opengl':  'nvidia/opengl:1.0-glvnd-devel-ubuntu18.04',
	'cudagl':  'nvidia/cudagl:9.2-devel-ubuntu18.04'
}

class BuildConfiguration(object):
	
	def __init__(self, args):
		'''
		Creates a new build configuration based on the supplied arguments object
		'''
		
		# Validate the specified version string
		try:
			ue4Version = semver.parse(args.release)
			if ue4Version['major'] != 4 or ue4Version['prerelease'] != None:
				raise Exception()
			self.release = semver.format_version(ue4Version['major'], ue4Version['minor'], ue4Version['patch'])
		except:
			raise RuntimeError('invalid UE4 release number "{}", full semver format required (e.g. "4.19.0")'.format(args.release))
		
		# Store our common configuration settings
		self.containerPlatform = 'windows' if platform.system() == 'Windows' and args.linux == False else 'linux'
		self.dryRun = args.dry_run
		self.rebuild = args.rebuild
		self.noPackage = args.no_package
		self.noCapture = args.no_capture
		self.suffix = args.suffix
		self.platformArgs = []
		self.baseImage = None
		
		# If we're building Windows containers, generate our Windows-specific configuration settings
		if self.containerPlatform == 'windows':
			self._generateWindowsConfig(args)
		
		# If we're building Linux containers, generate our Linux-specific configuration settings
		if self.containerPlatform == 'linux':
			self._generateLinuxConfig(args)
	
	def _generateWindowsConfig(self, args):
		
		# Determine base tag for the Windows release of the host system
		hostRelease = WindowsUtils.getWindowsRelease()
		self.hostBasetag = WindowsUtils.getReleaseBaseTag(hostRelease)
		
		# Store the tag for the base Windows Server Core image
		self.basetag = args.basetag if args.basetag is not None else self.hostBasetag
		self.baseImage = 'microsoft/dotnet-framework:4.7.2-sdk-windowsservercore-' + self.basetag
		
		# Verify that any user-specified base tag is valid
		if WindowsUtils.isValidBaseTag(self.basetag) == False:
			raise RuntimeError('unrecognised Windows Server Core base image tag "{}", supported tags are {}'.format(self.basetag, WindowsUtils.getValidBaseTags()))
		
		# Set the memory limit Docker flags
		self.memLimit = 8.0 if args.random_memory == False else random.uniform(8.0, 10.0)
		self.platformArgs = ['-m', '{:.2f}GB'.format(self.memLimit)]
		
		# Set the isolation mode Docker flags
		self.isolation = args.isolation if args.isolation is not None else 'default'
		if self.isolation != 'default':
			self.platformArgs.append('-isolation=' + self.isolation)
	
	def _generateLinuxConfig(self, args):
		
		# Store our NVIDIA Docker-related settings
		self.nvidia = args.nvidia
		self.cuda = args.cuda
		
		# Determine if we are building GPU-enabled container images
		if self.nvidia == True and self.cuda == True:
			self.baseImage = LINUX_BASE_IMAGES['cudagl']
		elif self.nvidia == True:
			self.baseImage = LINUX_BASE_IMAGES['opengl']
		else:
			self.baseImage = LINUX_BASE_IMAGES['default']
