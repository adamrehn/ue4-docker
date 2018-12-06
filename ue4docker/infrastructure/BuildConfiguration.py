from .PackageUtils import PackageUtils
from .WindowsUtils import WindowsUtils
import humanfriendly, os, platform, random

# Import the `semver` package even when the conflicting `node-semver` package is present
semver = PackageUtils.importFile('semver', os.path.join(PackageUtils.getPackageLocation('semver'), 'semver.py'))

# The default Unreal Engine git repository
DEFAULT_GIT_REPO = 'https://github.com/EpicGames/UnrealEngine.git'

# The base images for Linux containers
LINUX_BASE_IMAGES = {
	'opengl': 'nvidia/opengl:1.0-glvnd-devel-ubuntu18.04',
	'cudagl': 'nvidia/cudagl:10.0-devel-ubuntu18.04'
}

# The default memory limit (in GB) under Windows
DEFAULT_MEMORY_LIMIT = 10.0

class BuildConfiguration(object):
	
	def __init__(self, args):
		'''
		Creates a new build configuration based on the supplied arguments object
		'''
		
		# Determine if we are building a custom version of UE4 rather than an official release
		if args.release.lower() == 'custom':
			
			# Both a custom repository and a custom branch/tag must be specified
			if args.repo is None or args.branch is None:
				raise RuntimeError('both a repository and branch/tag must be specified when building a custom version of the Engine')
			
			# Use the specified repository and branch/tag
			self.release = 'custom'
			self.repository = args.repo
			self.branch = args.branch
			
		else:
			
			# Validate the specified version string
			try:
				ue4Version = semver.parse(args.release)
				if ue4Version['major'] != 4 or ue4Version['prerelease'] != None:
					raise Exception()
				self.release = semver.format_version(ue4Version['major'], ue4Version['minor'], ue4Version['patch'])
			except:
				raise RuntimeError('invalid UE4 release number "{}", full semver format required (e.g. "4.19.0")'.format(args.release))
			
			# Use the default repository and the release tag for the specified version
			self.repository = DEFAULT_GIT_REPO
			self.branch = '{}-release'.format(self.release)
		
		# Store our common configuration settings
		self.containerPlatform = 'windows' if platform.system() == 'Windows' and args.linux == False else 'linux'
		self.dryRun = args.dry_run
		self.rebuild = args.rebuild
		self.noEngine = args.no_engine
		self.noMinimal = args.no_minimal
		self.noFull = args.no_full
		self.suffix = args.suffix
		self.platformArgs = ['--no-cache'] if args.no_cache == True else []
		self.baseImage = None
		
		# If we're building Windows containers, generate our Windows-specific configuration settings
		if self.containerPlatform == 'windows':
			self._generateWindowsConfig(args)
		
		# If we're building Linux containers, generate our Linux-specific configuration settings
		if self.containerPlatform == 'linux':
			self._generateLinuxConfig(args)
	
	def _generateWindowsConfig(self, args):
		
		# Store the path to the directory containing our required Windows DLL files
		self.defaultDllDir = os.path.join(os.environ['SystemRoot'], 'System32')
		self.dlldir = args.dlldir if args.dlldir is not None else self.defaultDllDir
		
		# Determine base tag for the Windows release of the host system
		self.hostRelease = WindowsUtils.getWindowsRelease()
		self.hostBasetag = WindowsUtils.getReleaseBaseTag(self.hostRelease)
		
		# Store the tag for the base Windows Server Core image
		self.basetag = args.basetag if args.basetag is not None else self.hostBasetag
		self.baseImage = 'microsoft/dotnet-framework:4.7.2-sdk-windowsservercore-' + self.basetag
		
		# Verify that any user-specified base tag is valid
		if WindowsUtils.isValidBaseTag(self.basetag) == False:
			raise RuntimeError('unrecognised Windows Server Core base image tag "{}", supported tags are {}'.format(self.basetag, WindowsUtils.getValidBaseTags()))
		
		# Set the memory limit Docker flags
		if args.m is not None:
			try:
				self.memLimit = humanfriendly.parse_size(args.m) / (1000*1000*1000)
			except:
				raise RuntimeError('invalid memory limit "{}"'.format(args.m))
		else:
			self.memLimit = DEFAULT_MEMORY_LIMIT if args.random_memory == False else random.uniform(DEFAULT_MEMORY_LIMIT, DEFAULT_MEMORY_LIMIT + 2.0)
		self.platformArgs.extend(['-m', '{:.2f}GB'.format(self.memLimit)])
		
		# Set the isolation mode Docker flags
		self.isolation = args.isolation if args.isolation is not None else 'default'
		if self.isolation != 'default':
			self.platformArgs.append('-isolation=' + self.isolation)
	
	def _generateLinuxConfig(self, args):
		
		# Determine if we are building CUDA-enabled container images
		self.cuda = args.cuda
		if self.cuda == True:
			self.baseImage = LINUX_BASE_IMAGES['cudagl']
		else:
			self.baseImage = LINUX_BASE_IMAGES['opengl']
