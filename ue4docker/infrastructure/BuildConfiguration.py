from .DockerUtils import DockerUtils
from .PackageUtils import PackageUtils
from .WindowsUtils import WindowsUtils
import humanfriendly, json, os, platform, random
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
		'10.1': 'nvidia/cudagl:10.1-devel-ubuntu18.04',
		'10.2': 'nvidia/cudagl:10.2-devel-ubuntu18.04'
	}
}

# The default CUDA version to use when `--cuda` is specified without a value
DEFAULT_CUDA_VERSION = '9.2'

# The default memory limit (in GB) under Windows
DEFAULT_MEMORY_LIMIT = 10.0

class VisualStudio(object):
	VS2017 = '2017'
	VS2019 = '2019'

	BuildNumbers = {
		VS2017 : '15',
		VS2019 : '16',
	}

	MinSupportedUnreal = {
		# Unreal Engine 4.23.1 is the first that successfully builds with Visual Studio v16.3
		# See https://github.com/EpicGames/UnrealEngine/commit/2510d4fd07a35ba5bff6ac2c7becaa6e8b7f11fa
		#
		# Unreal Engine 4.25 is the first that works with .NET SDK 4.7+
		# See https://github.com/EpicGames/UnrealEngine/commit/5256eedbdef30212ab69fdf4c09e898098959683
		VS2019 : semver.VersionInfo(4, 25)
	}

class ExcludedComponent(object):
	'''
	The different components that we support excluding from the built images
	'''
	
	# Engine Derived Data Cache (DDC)
	DDC = 'ddc'
	
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
			
			ExcludedComponent.DDC: 'Derived Data Cache (DDC)',
			ExcludedComponent.Debug: 'Debug symbols',
			ExcludedComponent.Templates: 'Template projects and samples'
			
		}.get(component, '[Unknown component]')


class BuildConfiguration(object):
	
	@staticmethod
	def addArguments(parser):
		'''
		Registers our supported command-line arguments with the supplied argument parser
		'''
		parser.add_argument('release', help='UE4 release to build, in semver format (e.g. 4.20.0) or "custom" for a custom repo and branch')
		parser.add_argument('--linux', action='store_true', help='Build Linux container images under Windows')
		parser.add_argument('--rebuild', action='store_true', help='Rebuild images even if they already exist')
		parser.add_argument('--dry-run', action='store_true', help='Print `docker build` commands instead of running them')
		parser.add_argument('--pull-prerequisites', action='store_true', help='Pull the ue4-build-prerequisites image from Docker Hub instead of building it')
		parser.add_argument('--no-engine', action='store_true', help='Don\'t build the ue4-engine image')
		parser.add_argument('--no-minimal', action='store_true', help='Don\'t build the ue4-minimal image')
		parser.add_argument('--no-full', action='store_true', help='Don\'t build the ue4-full image')
		parser.add_argument('--no-cache', action='store_true', help='Disable Docker build cache')
		parser.add_argument('--random-memory', action='store_true', help='Use a random memory limit for Windows containers')
		parser.add_argument('--exclude', action='append', default=[], choices=[ExcludedComponent.DDC, ExcludedComponent.Debug, ExcludedComponent.Templates], help='Exclude the specified component (can be specified multiple times to exclude multiple components)')
		parser.add_argument('--opt', action='append', default=[], help='Set an advanced configuration option (can be specified multiple times to specify multiple options)')
		parser.add_argument('--cuda', default=None, metavar='VERSION', help='Add CUDA support as well as OpenGL support when building Linux containers')
		parser.add_argument('--visual-studio', default=VisualStudio.VS2017, choices=VisualStudio.BuildNumbers.keys(), help='Specify Visual Studio Build Tools version to use for Windows containers')
		parser.add_argument('-username', default=None, help='Specify the username to use when cloning the git repository')
		parser.add_argument('-password', default=None, help='Specify the password or access token to use when cloning the git repository')
		parser.add_argument('-repo', default=None, help='Set the custom git repository to clone when "custom" is specified as the release value')
		parser.add_argument('-branch', default=None, help='Set the custom branch/tag to clone when "custom" is specified as the release value')
		parser.add_argument('-isolation', default=None, help='Set the isolation mode to use for Windows containers (process or hyperv)')
		parser.add_argument('-basetag', default=None, help='Windows Server Core base image tag to use for Windows containers (default is the host OS version)')
		parser.add_argument('-dlldir', default=None, help='Set the directory to copy required Windows DLLs from (default is the host System32 directory)')
		parser.add_argument('-suffix', default='', help='Add a suffix to the tags of the built images')
		parser.add_argument('-m', default=None, help='Override the default memory limit under Windows (also overrides --random-memory)')
		parser.add_argument('-ue4cli', default=None, help='Override the default version of ue4cli installed in the ue4-full image')
		parser.add_argument('-conan-ue4cli', default=None, help='Override the default version of conan-ue4cli installed in the ue4-full image')
		parser.add_argument('-layout', default=None, help='Copy generated Dockerfiles to the specified directory and don\'t build the images')
		parser.add_argument('--combine', action='store_true', help='Combine generated Dockerfiles into a single multi-stage build Dockerfile')
		parser.add_argument('--monitor', action='store_true', help='Monitor resource usage during builds (useful for debugging)')
		parser.add_argument('-interval', type=float, default=20.0, help='Sampling interval in seconds when resource monitoring has been enabled using --monitor (default is 20 seconds)')
		parser.add_argument('--ignore-eol', action='store_true', help='Run builds even on EOL versions of Windows (advanced use only)')
		parser.add_argument('--ignore-blacklist', action='store_true', help='Run builds even on blacklisted versions of Windows (advanced use only)')
		parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output during builds (useful for debugging)')
	
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
				raise RuntimeError('invalid UE4 release number "{}", full semver format required (e.g. "4.20.0")'.format(self.args.release))
			
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
		self.ignoreEOL = self.args.ignore_eol
		self.ignoreBlacklist = self.args.ignore_blacklist
		self.verbose = self.args.verbose
		self.layoutDir = self.args.layout
		self.combine = self.args.combine
		
		# If the user specified custom version strings for ue4cli and/or conan-ue4cli, process them
		self.ue4cliVersion = self._processPackageVersion('ue4cli', self.args.ue4cli)
		self.conanUe4cliVersion = self._processPackageVersion('conan-ue4cli', self.args.conan_ue4cli)
		
		# Process any specified advanced configuration options (which we use directly as context values for the Jinja templating system)
		self.opts = {}
		for o in self.args.opt:
			if '=' in o:
				key, value = o.split('=', 1)
				self.opts[key.replace('-', '_')] = self._processTemplateValue(value)
			else:
				self.opts[o.replace('-', '_')] = True
		
		# If we are generating Dockerfiles then generate them for all images that have not been explicitly excluded
		if self.layoutDir is not None:
			self.rebuild = True
		
		# If we are generating Dockerfiles and combining them then set the corresponding Jinja context value
		if self.layoutDir is not None and self.combine == True:
			self.opts['combine'] = True
		
		# If the user requested an option that is only compatible with generated Dockerfiles then ensure `-layout` was specified
		if self.layoutDir is None and self.opts.get('source_mode', 'git') != 'git':
			raise RuntimeError('the `-layout` flag must be used when specifying a non-default value for the `source_mode` option')
		if self.layoutDir is None and self.combine == True:
			raise RuntimeError('the `-layout` flag must be used when specifying the `--combine` flag')
		
		# Verify that the value for `source_mode` is valid if specified
		validSourceModes = ['git', 'copy']
		if self.opts.get('source_mode', 'git') not in validSourceModes:
			raise RuntimeError('invalid value specified for the `source_mode` option, valid values are {}'.format(validSourceModes))
		
		# Verify that the value for `credential_mode` is valid if specified
		validCredentialModes = ['endpoint', 'secrets'] if self.containerPlatform == 'linux' else ['endpoint']
		if self.opts.get('credential_mode', 'endpoint') not in validCredentialModes:
			raise RuntimeError('invalid value specified for the `credential_mode` option, valid values are {} when building {} containers'.format(validCredentialModes, self.containerPlatform.title()))
		
		# Generate our flags for keeping or excluding components
		self.exclusionFlags = [
			
			'--build-arg', 'BUILD_DDC={}'.format('false' if ExcludedComponent.DDC in self.excludedComponents else 'true'),
			'--build-arg', 'EXCLUDE_DEBUG={}'.format(1 if ExcludedComponent.Debug in self.excludedComponents else 0),
			'--build-arg', 'EXCLUDE_TEMPLATES={}'.format(1 if ExcludedComponent.Templates in self.excludedComponents else 0)
		]

		self.uatBuildFlags = []
		
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
		hostSysnative = os.path.join(os.environ['SystemRoot'], 'Sysnative')
		hostSystem32 = os.path.join(os.environ['SystemRoot'], 'System32')
		self.defaultDllDir = hostSysnative if os.path.exists(hostSysnative) else hostSystem32
		self.dlldir = self.args.dlldir if self.args.dlldir is not None else self.defaultDllDir

		self.visualStudio = self.args.visual_studio

		if not self.custom:
			# Check whether specified Unreal Engine release is compatible with specified Visual Studio
			vsMinSupportedUnreal = VisualStudio.MinSupportedUnreal.get(self.visualStudio, None)
			if vsMinSupportedUnreal is not None and semver.VersionInfo.parse(self.release) < vsMinSupportedUnreal:
				raise RuntimeError('specified version of Unreal Engine cannot be built with Visual Studio {}, oldest supported is {}'.format(self.visualStudio, vsMinSupportedUnreal))

		self.visualStudioBuildNumber = VisualStudio.BuildNumbers[self.visualStudio]
		# See https://github.com/EpicGames/UnrealEngine/commit/72585138472785e2ee58aab9950a7260275ee2ac
		self.uatBuildFlags += ['--build-arg', 'USE_VS2019={}'.format('true' if self.visualStudio == VisualStudio.VS2019 else 'false')]

		# Determine base tag for the Windows release of the host system
		self.hostRelease = WindowsUtils.getWindowsRelease()
		self.hostBasetag = WindowsUtils.getReleaseBaseTag(self.hostRelease)
		
		# Store the tag for the base Windows Server Core image
		self.basetag = self.args.basetag if self.args.basetag is not None else self.hostBasetag
		self.baseImage = 'mcr.microsoft.com/windows/servercore:' + self.basetag
		self.prereqsTag = self.basetag + '-vs' + self.visualStudio

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
			hostSupportsProcess = WindowsUtils.supportsProcessIsolation()
			dockerSupportsProcess = parse_version(DockerUtils.version()['Version']) >= parse_version('18.09.0')
			if not differentKernels and hostSupportsProcess and dockerSupportsProcess:
				self.isolation = 'process'
			else:
				self.isolation = DockerUtils.info()['Isolation']
		
		# Set the isolation mode Docker flag
		self.platformArgs.append('--isolation=' + self.isolation)
		
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
	
	def _processPackageVersion(self, package, version):
		
		# Leave the version value unmodified if a blank version was specified or a fully-qualified version was specified
		# (e.g. package==X.X.X, package>=X.X.X, git+https://url/for/package/repo.git, etc.)
		if version is None or '/' in version or version.lower().startswith(package):
			return version
		
		# If a version specifier (e.g. ==X.X.X, >=X.X.X, etc.) was specified, prefix it with the package name
		if '=' in version:
			return package + version
		
		# If a raw version number was specified, prefix the package name and a strict equality specifier
		return '{}=={}'.format(package, version)
	
	def _processTemplateValue(self, value):
		
		# If the value is a boolean (either raw or represented by zero or one) then parse it
		if value.lower() in ['true', '1']:
			return True
		elif value.lower() in ['false', '0']:
			return False
		
		# If the value is a JSON object or array then attempt to parse it
		if (value.startswith('{') and value.endswith('}')) or (value.startswith('[') and value.endswith(']')):
			try:
				return json.loads(value)
			except:
				print('Warning: could not parse option value "{}" as JSON, treating value as a string'.format(value))
		
		# Treat all other values as strings
		return value
