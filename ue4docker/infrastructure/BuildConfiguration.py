from .DockerUtils import DockerUtils
from .PackageUtils import PackageUtils
from .WindowsUtils import WindowsUtils
import humanfriendly, os, platform, random
from pkg_resources import parse_version

# Import the `semver` package even when the conflicting `node-semver` package is present
semver = PackageUtils.importFile('semver', os.path.join(PackageUtils.getPackageLocation('semver'), 'semver.py'))

# The default Unreal Engine git repository
DEFAULT_GIT_REPO = 'https://github.com/EpicGames/UnrealEngine.git'

# The base images for Linux containers
LINUX_BASE_IMAGES = {
	'opengl': 'nvidia/opengl:1.0-glvnd-devel-ubuntu18.04',
	'cudagl': {
		'9.2':  'nvidia/cudagl:9.2-devel-ubuntu18.04',
		'10.0': 'nvidia/cudagl:10.0-devel-ubuntu18.04',
		'10.1': 'nvidia/cudagl:10.1-devel-ubuntu18.04'
	}
}

# The default CUDA version to use when `--cuda` is specified without a value
DEFAULT_CUDA_VERSION = '9.2'

# The default memory limit (in GB) under Windows
DEFAULT_MEMORY_LIMIT = 10.0


class ExcludedComponent(object):
	'''
	The different components that we support excluding from the built images
	'''
	
	# Engine debug symbols
	Debug = 'debug'
	
	# Template projects and samples
	Templates = 'templates'
	
	
	@staticmethod
	def description(component):
		'''
		Returns a human-readable description of the specified component
		'''
		return {
			
			ExcludedComponent.Debug: 'Debug symbols',
			ExcludedComponent.Templates: 'Template projects and samples'
			
		}.get(component, '[Unknown component]')


class BuildConfiguration(object):
	
	@staticmethod
	def addArguments(parser):
		'''
		Registers our supported command-line arguments with the supplied argument parser
		'''
		parser.add_argument('release', help='UE4 release to build, in semver format (e.g. 4.19.0) or "custom" for a custom repo and branch')
		parser.add_argument('--linux', action='store_true', help='Build Linux container images under Windows')
		parser.add_argument('--rebuild', action='store_true', help='Rebuild images even if they already exist')
		parser.add_argument('--dry-run', action='store_true', help='Print `docker build` commands instead of running them')
		parser.add_argument('--pull-prerequisites', action='store_true', help='Pull the ue4-build-prerequisites image from Docker Hub instead of building it')
		parser.add_argument('--no-engine', action='store_true', help='Don\'t build the ue4-engine image')
		parser.add_argument('--no-minimal', action='store_true', help='Don\'t build the ue4-minimal image')
		parser.add_argument('--no-full', action='store_true', help='Don\'t build the ue4-full image')
		parser.add_argument('--no-cache', action='store_true', help='Disable Docker build cache')
		parser.add_argument('--random-memory', action='store_true', help='Use a random memory limit for Windows containers')
		parser.add_argument('--exclude', action='append', default=[], choices=[ExcludedComponent.Debug, ExcludedComponent.Templates], help='Exclude the specified component (can be specified multiple times to exclude multiple components)')
		parser.add_argument('--cuda', default=None, metavar='VERSION', help='Add CUDA support as well as OpenGL support when building Linux containers')
		parser.add_argument('-username', default=None, help='Specify the username to use when cloning the git repository')
		parser.add_argument('-password', default=None, help='Specify the password to use when cloning the git repository')
		parser.add_argument('-repo', default=None, help='Set the custom git repository to clone when "custom" is specified as the release value')
		parser.add_argument('-branch', default=None, help='Set the custom branch/tag to clone when "custom" is specified as the release value')
		parser.add_argument('-isolation', default=None, help='Set the isolation mode to use for Windows containers (process or hyperv)')
		parser.add_argument('-basetag', default=None, help='Windows Server Core base image tag to use for Windows containers (default is the host OS version)')
		parser.add_argument('-dlldir', default=None, help='Set the directory to copy required Windows DLLs from (default is the host System32 directory)')
		parser.add_argument('-suffix', default='', help='Add a suffix to the tags of the built images')
		parser.add_argument('-m', default=None, help='Override the default memory limit under Windows (also overrides --random-memory)')
	
	def __init__(self, parser, argv):
		'''
		Creates a new build configuration based on the supplied arguments object
		'''
		
		# If the user has specified `--cuda` without a version value, treat the value as an empty string
		argv = [arg + '=' if arg == '--cuda' else arg for arg in argv]
		
		# Parse the supplied command-line arguments
		self.args = parser.parse_args(argv)
		
		# Determine if we are building a custom version of UE4 rather than an official release
		self.args.release = self.args.release.lower()
		if self.args.release == 'custom' or self.args.release.startswith('custom:'):
			
			# Both a custom repository and a custom branch/tag must be specified
			if self.args.repo is None or self.args.branch is None:
				raise RuntimeError('both a repository and branch/tag must be specified when building a custom version of the Engine')
			
			# Use the specified repository and branch/tag
			customName = self.args.release.split(':', 2)[1].strip() if ':' in self.args.release else ''
			self.release = customName if len(customName) > 0 else 'custom'
			self.repository = self.args.repo
			self.branch = self.args.branch
			self.custom = True
			
		else:
			
			# Validate the specified version string
			try:
				ue4Version = semver.parse(self.args.release)
				if ue4Version['major'] != 4 or ue4Version['prerelease'] != None:
					raise Exception()
				self.release = semver.format_version(ue4Version['major'], ue4Version['minor'], ue4Version['patch'])
			except:
				raise RuntimeError('invalid UE4 release number "{}", full semver format required (e.g. "4.19.0")'.format(self.args.release))
			
			# Use the default repository and the release tag for the specified version
			self.repository = DEFAULT_GIT_REPO
			self.branch = '{}-release'.format(self.release)
			self.custom = False
		
		# Store our common configuration settings
		self.containerPlatform = 'windows' if platform.system() == 'Windows' and self.args.linux == False else 'linux'
		self.dryRun = self.args.dry_run
		self.rebuild = self.args.rebuild
		self.pullPrerequisites = self.args.pull_prerequisites
		self.noEngine = self.args.no_engine
		self.noMinimal = self.args.no_minimal
		self.noFull = self.args.no_full
		self.suffix = self.args.suffix
		self.platformArgs = ['--no-cache'] if self.args.no_cache == True else []
		self.excludedComponents = set(self.args.exclude)
		self.baseImage = None
		self.prereqsTag = None
		
		# Generate our flags for keeping or excluding components
		self.exclusionFlags = [
			'--build-arg', 'EXCLUDE_DEBUG={}'.format(1 if ExcludedComponent.Debug in self.excludedComponents else 0),
			'--build-arg', 'EXCLUDE_TEMPLATES={}'.format(1 if ExcludedComponent.Templates in self.excludedComponents else 0)
		]
		
		# If we're building Windows containers, generate our Windows-specific configuration settings
		if self.containerPlatform == 'windows':
			self._generateWindowsConfig()
		
		# If we're building Linux containers, generate our Linux-specific configuration settings
		if self.containerPlatform == 'linux':
			self._generateLinuxConfig()
		
		# If the user-specified suffix passed validation, prefix it with a dash
		self.suffix = '-{}'.format(self.suffix) if self.suffix != '' else ''
	
	def describeExcludedComponents(self):
		'''
		Returns a list of strings describing the components that will be excluded (if any.)
		'''
		return sorted([ExcludedComponent.description(component) for component in self.excludedComponents])
	
	def _generateWindowsConfig(self):
		
		# Store the path to the directory containing our required Windows DLL files
		self.defaultDllDir = os.path.join(os.environ['SystemRoot'], 'System32')
		self.dlldir = self.args.dlldir if self.args.dlldir is not None else self.defaultDllDir
		
		# Determine base tag for the Windows release of the host system
		self.hostRelease = WindowsUtils.getWindowsRelease()
		self.hostBasetag = WindowsUtils.getReleaseBaseTag(self.hostRelease)
		
		# Store the tag for the base Windows Server Core image
		self.basetag = self.args.basetag if self.args.basetag is not None else self.hostBasetag
		self.baseImage = 'mcr.microsoft.com/dotnet/framework/sdk:4.7.2-windowsservercore-' + self.basetag
		self.prereqsTag = self.basetag
		
		# Verify that any user-specified base tag is valid
		if WindowsUtils.isValidBaseTag(self.basetag) == False:
			raise RuntimeError('unrecognised Windows Server Core base image tag "{}", supported tags are {}'.format(self.basetag, WindowsUtils.getValidBaseTags()))
		
		# Verify that any user-specified tag suffix does not collide with our base tags
		if WindowsUtils.isValidBaseTag(self.suffix) == True:
			raise RuntimeError('tag suffix cannot be any of the Windows Server Core base image tags: {}'.format(WindowsUtils.getValidBaseTags()))
		
		# If the user has explicitly specified an isolation mode then use it, otherwise auto-detect
		if self.args.isolation is not None:
			self.isolation = self.args.isolation
		else:
			
			# If we are able to use process isolation mode then use it, otherwise fallback to the Docker daemon's default isolation mode
			differentKernels = WindowsUtils.isInsiderPreview() or self.basetag != self.hostBasetag
			hostSupportsProcess = WindowsUtils.isWindowsServer() or int(self.hostRelease) >= 1809
			dockerSupportsProcess = parse_version(DockerUtils.version()['Version']) >= parse_version('18.09.0')
			if not differentKernels and hostSupportsProcess and dockerSupportsProcess:
				self.isolation = 'process'
			else:
				self.isolation = DockerUtils.info()['Isolation']
		
		# Set the isolation mode Docker flag
		self.platformArgs.append('-isolation=' + self.isolation)
		
		# If the user has explicitly specified a memory limit then use it, otherwise auto-detect
		self.memLimit = None
		if self.args.m is not None:
			try:
				self.memLimit = humanfriendly.parse_size(self.args.m) / (1000*1000*1000)
			except:
				raise RuntimeError('invalid memory limit "{}"'.format(self.args.m))
		else:
			
			# Only specify a memory limit when using Hyper-V isolation mode, in order to override the 1GB default limit
			# (Process isolation mode does not impose any memory limits by default)
			if self.isolation == 'hyperv':
				self.memLimit = DEFAULT_MEMORY_LIMIT if self.args.random_memory == False else random.uniform(DEFAULT_MEMORY_LIMIT, DEFAULT_MEMORY_LIMIT + 2.0)
		
		# Set the memory limit Docker flag
		if self.memLimit is not None:
			self.platformArgs.extend(['-m', '{:.2f}GB'.format(self.memLimit)])
	
	def _generateLinuxConfig(self):
		
		# Verify that any user-specified tag suffix does not collide with our base tags
		if self.suffix.startswith('opengl') or self.suffix.startswith('cudagl'):
			raise RuntimeError('tag suffix cannot begin with "opengl" or "cudagl".')
		
		# Determine if we are building CUDA-enabled container images
		self.cuda = None
		if self.args.cuda is not None:
			
			# Verify that the specified CUDA version is valid
			self.cuda = self.args.cuda if self.args.cuda != '' else DEFAULT_CUDA_VERSION
			if self.cuda not in LINUX_BASE_IMAGES['cudagl']:
				raise RuntimeError('unsupported CUDA version "{}", supported versions are: {}'.format(
					self.cuda,
					', '.join([v for v in LINUX_BASE_IMAGES['cudagl']])
				))
			
			# Use the appropriate base image for the specified CUDA version
			self.baseImage = LINUX_BASE_IMAGES['cudagl'][self.cuda]
			self.prereqsTag = 'cudagl{}'.format(self.cuda)
		else:
			self.baseImage = LINUX_BASE_IMAGES['opengl']
			self.prereqsTag = 'opengl'
