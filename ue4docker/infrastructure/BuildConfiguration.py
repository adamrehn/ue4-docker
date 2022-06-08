from .DockerUtils import DockerUtils
from .PackageUtils import PackageUtils
from .WindowsUtils import WindowsUtils
import humanfriendly, json, os, platform, random
from pkg_resources import parse_version

# Import the `semver` package even when the conflicting `node-semver` package is present
semver = PackageUtils.importFile(
    "semver", os.path.join(PackageUtils.getPackageLocation("semver"), "semver.py")
)

# The default Unreal Engine git repository
DEFAULT_GIT_REPO = "https://github.com/EpicGames/UnrealEngine.git"

# The base images for Linux containers
LINUX_BASE_IMAGES = {
    "opengl": "nvidia/opengl:1.0-glvnd-devel-{ubuntu}",
    "cudagl": "nvidia/cudagl:{cuda}-devel-{ubuntu}",
}

# The default ubuntu base to use
DEFAULT_LINUX_VERSION = "ubuntu18.04"

# The default CUDA version to use when `--cuda` is specified without a value
DEFAULT_CUDA_VERSION = "11.4"

# The default memory limit (in GB) under Windows
DEFAULT_MEMORY_LIMIT = 10.0

# The Perforce changelist numbers for each supported .0 release of the Unreal Engine
UNREAL_ENGINE_RELEASE_CHANGELISTS = {
    "4.20.0": 4212847,
    "4.21.0": 4541578,
    "4.22.0": 5660361,
    "4.23.0": 8386587,
    "4.24.0": 10570792,
    "4.25.0": 13144385,
    "4.26.0": 14830424,
    "4.27.0": 17155196,
    "5.0.0": 19505902,
}


class VisualStudio(object):
    VS2017 = "2017"
    VS2019 = "2019"
    VS2022 = "2022"

    BuildNumbers = {
        VS2017: "15",
        VS2019: "16",
        VS2022: "17",
    }

    MinSupportedUnreal = {
        # Unreal Engine 4.23.1 is the first that successfully builds with Visual Studio v16.3
        # See https://github.com/EpicGames/UnrealEngine/commit/2510d4fd07a35ba5bff6ac2c7becaa6e8b7f11fa
        #
        # Unreal Engine 4.25 is the first that works with .NET SDK 4.7+
        # See https://github.com/EpicGames/UnrealEngine/commit/5256eedbdef30212ab69fdf4c09e898098959683
        VS2019: semver.VersionInfo(4, 25),
        VS2022: semver.VersionInfo(4, 27),
    }


class ExcludedComponent(object):
    """
    The different components that we support excluding from the built images
    """

    # Engine Derived Data Cache (DDC)
    DDC = "ddc"

    # Engine debug symbols
    Debug = "debug"

    # Template projects and samples
    Templates = "templates"

    @staticmethod
    def description(component):
        """
        Returns a human-readable description of the specified component
        """
        return {
            ExcludedComponent.DDC: "Derived Data Cache (DDC)",
            ExcludedComponent.Debug: "Debug symbols",
            ExcludedComponent.Templates: "Template projects and samples",
        }.get(component, "[Unknown component]")


class BuildConfiguration(object):
    @staticmethod
    def addArguments(parser):
        """
        Registers our supported command-line arguments with the supplied argument parser
        """
        parser.add_argument(
            "release",
            nargs="?",  # aka "required = False", but that doesn't work in positionals
            help='UE4 release to build, in semver format (e.g. 4.20.0) or "custom" for a custom repo and branch (deprecated, use --ue-version instead)',
        )
        parser.add_argument(
            "--ue-version",
            default=None,
            help='UE4 release to build, in semver format (e.g. 4.20.0) or "custom" for a custom repo and branch',
        )
        parser.add_argument(
            "--linux",
            action="store_true",
            help="Build Linux container images under Windows",
        )
        parser.add_argument(
            "--rebuild",
            action="store_true",
            help="Rebuild images even if they already exist",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print `docker build` commands instead of running them",
        )
        parser.add_argument(
            "--no-engine",
            action="store_true",
            help="Don't build the ue4-engine image (deprecated, use --target instead)",
        )
        parser.add_argument(
            "--no-minimal",
            action="store_true",
            help="Don't build the ue4-minimal image (deprecated, use --target instead)",
        )
        parser.add_argument(
            "--no-full",
            action="store_true",
            help="Don't build the ue4-full image (deprecated, use --target instead)",
        )
        parser.add_argument(
            "--no-cache", action="store_true", help="Disable Docker build cache"
        )
        parser.add_argument(
            "--target",
            action="append",
            help="Add a target to the build list. Valid targets are `build-prerequisites`, `source`, `engine`, `minimal`, `full`, and `all`. May be specified multiple times or comma-separated. Defaults to `all`.",
        )
        parser.add_argument(
            "--random-memory",
            action="store_true",
            help="Use a random memory limit for Windows containers",
        )
        parser.add_argument(
            "--exclude",
            action="append",
            default=[],
            choices=[
                ExcludedComponent.DDC,
                ExcludedComponent.Debug,
                ExcludedComponent.Templates,
            ],
            help="Exclude the specified component (can be specified multiple times to exclude multiple components)",
        )
        parser.add_argument(
            "--opt",
            action="append",
            default=[],
            help="Set an advanced configuration option (can be specified multiple times to specify multiple options)",
        )
        parser.add_argument(
            "--cuda",
            default=None,
            metavar="VERSION",
            help="Add CUDA support as well as OpenGL support when building Linux containers",
        )
        parser.add_argument(
            "--visual-studio",
            default=VisualStudio.VS2017,
            choices=VisualStudio.BuildNumbers.keys(),
            help="Specify Visual Studio Build Tools version to use for Windows containers",
        )
        parser.add_argument(
            "-username",
            default=None,
            help="Specify the username to use when cloning the git repository",
        )
        parser.add_argument(
            "-password",
            default=None,
            help="Specify the password or access token to use when cloning the git repository",
        )
        parser.add_argument(
            "-repo",
            default=None,
            help='Set the custom git repository to clone when "custom" is specified as the release value',
        )
        parser.add_argument(
            "-branch",
            default=None,
            help='Set the custom branch/tag to clone when "custom" is specified as the release value',
        )
        parser.add_argument(
            "-isolation",
            default=None,
            help="Set the isolation mode to use for Windows containers (process or hyperv)",
        )
        parser.add_argument(
            "-basetag",
            default=None if platform.system() == "Windows" else DEFAULT_LINUX_VERSION,
            help="Operating system base image tag to use. For Linux this is the version of Ubuntu (default is ubuntu18.04). "
            "For Windows this is the Windows Server Core base image tag (default is the host OS version)",
        )
        parser.add_argument(
            "-suffix", default="", help="Add a suffix to the tags of the built images"
        )
        parser.add_argument(
            "-m",
            default=None,
            help="Override the default memory limit under Windows (also overrides --random-memory)",
        )
        parser.add_argument(
            "-ue4cli",
            default=None,
            help="Override the default version of ue4cli installed in the ue4-full image",
        )
        parser.add_argument(
            "-conan-ue4cli",
            default=None,
            help="Override the default version of conan-ue4cli installed in the ue4-full image",
        )
        parser.add_argument(
            "-layout",
            default=None,
            help="Copy generated Dockerfiles to the specified directory and don't build the images",
        )
        parser.add_argument(
            "--combine",
            action="store_true",
            help="Combine generated Dockerfiles into a single multi-stage build Dockerfile",
        )
        parser.add_argument(
            "--monitor",
            action="store_true",
            help="Monitor resource usage during builds (useful for debugging)",
        )
        parser.add_argument(
            "-interval",
            type=float,
            default=20.0,
            help="Sampling interval in seconds when resource monitoring has been enabled using --monitor (default is 20 seconds)",
        )
        parser.add_argument(
            "--ignore-blacklist",
            action="store_true",
            help="Run builds even on blacklisted versions of Windows (advanced use only)",
        )
        parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Enable verbose output during builds (useful for debugging)",
        )
        parser.add_argument(
            "-changelist",
            type=int,
            default=None,
            help="Set a specific changelist number in the Unreal Engine's Build.version file",
        )
        parser.add_argument(
            "--prerequisites-dockerfile",
            default=None,
            help="Specifies path to custom ue4-build-prerequisites dockerfile",
        )

    def __init__(self, parser, argv, logger):
        """
        Creates a new build configuration based on the supplied arguments object
        """

        # If the user has specified `--cuda` without a version value, treat the value as an empty string
        argv = [arg + "=" if arg == "--cuda" else arg for arg in argv]

        # Parse the supplied command-line arguments
        self.args = parser.parse_args(argv)
        self.changelist = self.args.changelist

        # Figure out what targets we have; this is needed to find out if we need --ue-version.
        using_target_specifier_old = (
            self.args.no_engine or self.args.no_minimal or self.args.no_full
        )
        using_target_specifier_new = self.args.target is not None

        # If we specified nothing, it's the same as specifying `all`
        if not using_target_specifier_old and not using_target_specifier_new:
            self.args.target = ["all"]
        elif using_target_specifier_old and not using_target_specifier_new:
            # Convert these to the new style
            logger.warning(
                "Using deprecated `--no-*` target specifiers; recommend changing to `--target`",
                False,
            )

            # no-minimal implies no-full
            if self.args.no_minimal:
                self.args.no_full = True

            # Change into target descriptors
            self.args.target = []

            if not self.args.no_full:
                self.args.target += ["full"]

            if not self.args.no_minimal:
                self.args.target += ["minimal"]

            if not self.args.no_engine:
                self.args.target += ["engine"]

            # disabling these was never supported
            self.args.target += ["source"]
            self.args.target += ["build-prerequisites"]

        elif using_target_specifier_new and not using_target_specifier_old:
            # these can be token-delimited, so let's just split them apart and then remerge them into one list
            split = [item.split(",") for item in self.args.target]
            self.args.target = [item for sublist in split for item in sublist]

        elif using_target_specifier_old and using_target_specifier_new:
            # uhoh
            raise RuntimeError(
                "specified both `--target` and the old `--no-*` options; please use only `--target`!"
            )

        # Now that we have our options in `self.args.target`, evaluate our dependencies
        # In a theoretical ideal world this should be code-driven; if you find yourself adding a lot more code to this, consider a redesign!
        active_targets = set(self.args.target)

        # build-prereq -> source -> engine
        # build-prereq -> source -> minimal -> full

        # We initialize these with all the options, with the intent that you should be accessing them directly and not checking for existence
        # This is to avoid typos giving false-negatives; KeyError is reliable and tells you what you did wrong
        self.buildTargets = {
            "build-prerequisites": False,
            "source": False,
            "engine": False,
            "minimal": False,
            "full": False,
        }

        for target in active_targets:
            if target != "all" and target not in self.buildTargets:
                valid_options = sorted(self.buildTargets.keys())
                raise RuntimeError(
                    f"unknown build target '{target}', valid options are: all {' '.join(valid_options)}"
                )

        if "full" in active_targets or "all" in active_targets:
            self.buildTargets["full"] = True
            active_targets.add("minimal")

        if "minimal" in active_targets or "all" in active_targets:
            self.buildTargets["minimal"] = True
            active_targets.add("source")

        if "engine" in active_targets or "all" in active_targets:
            self.buildTargets["engine"] = True
            active_targets.add("source")

        if "source" in active_targets or "all" in active_targets:
            self.buildTargets["source"] = True
            active_targets.add("build-prerequisites")

        if "build-prerequisites" in active_targets or "all" in active_targets:
            self.buildTargets["build-prerequisites"] = True

        if not self.buildTargets["build-prerequisites"]:
            raise RuntimeError(
                "we're not building anything; this shouldn't even be possible, but is definitely not useful"
            )

        # See if the user specified both the old positional version option and the new ue-version option
        if self.args.release is not None and self.args.ue_version is not None:
            raise RuntimeError(
                "specified both `--ue-version` and the old positional version option; please use only `--ue-version`!"
            )

        # For the sake of a simpler pull request, we use self.args.release as the canonical place for this data.
        # If support for the old positional version option is removed, this should be fixed.
        if self.args.ue_version is not None:
            self.args.release = self.args.ue_version

        # We care about the version number only if we're building source
        if self.buildTargets["source"]:
            if self.args.release is None:
                raise RuntimeError("missing `--ue-version` when building source")

            # Determine if we are building a custom version of UE4 rather than an official release
            self.args.release = self.args.release.lower()
            if self.args.release == "custom" or self.args.release.startswith("custom:"):

                # Both a custom repository and a custom branch/tag must be specified
                if self.args.repo is None or self.args.branch is None:
                    raise RuntimeError(
                        "both a repository and branch/tag must be specified when building a custom version of the Engine"
                    )

                # Use the specified repository and branch/tag
                customName = (
                    self.args.release.split(":", 2)[1].strip()
                    if ":" in self.args.release
                    else ""
                )
                self.release = customName if len(customName) > 0 else "custom"
                self.repository = self.args.repo
                self.branch = self.args.branch
                self.custom = True

            else:

                # Validate the specified version string
                try:
                    ue4Version = semver.parse(self.args.release)
                    if (
                        ue4Version["major"] not in [4, 5]
                        or ue4Version["prerelease"] != None
                    ):
                        raise Exception()
                    self.release = semver.format_version(
                        ue4Version["major"], ue4Version["minor"], ue4Version["patch"]
                    )
                except:
                    raise RuntimeError(
                        'invalid Unreal Engine release number "{}", full semver format required (e.g. "4.20.0")'.format(
                            self.args.release
                        )
                    )

                # Use the default repository and the release tag for the specified version
                self.repository = DEFAULT_GIT_REPO
                self.branch = "{}-release".format(self.release)
                self.custom = False

                # If the user specified a .0 release of the Unreal Engine and did not specify a changelist override then
                # use the official changelist number for that release to ensure consistency with Epic Games Launcher builds
                # (This is necessary because .0 releases do not include a `CompatibleChangelist` value in Build.version)
                if (
                    self.changelist is None
                    and self.release in UNREAL_ENGINE_RELEASE_CHANGELISTS
                ):
                    self.changelist = UNREAL_ENGINE_RELEASE_CHANGELISTS[self.release]
        else:
            # defaults needed by other parts of the codebase
            self.custom = False
            self.release = None
            self.repository = None
            self.branch = None

        # Store our common configuration settings
        self.containerPlatform = (
            "windows"
            if platform.system() == "Windows" and self.args.linux == False
            else "linux"
        )
        self.dryRun = self.args.dry_run
        self.rebuild = self.args.rebuild
        self.suffix = self.args.suffix
        self.platformArgs = ["--no-cache"] if self.args.no_cache == True else []
        self.excludedComponents = set(self.args.exclude)
        self.baseImage = None
        self.prereqsTag = None
        self.ignoreBlacklist = self.args.ignore_blacklist
        self.verbose = self.args.verbose
        self.layoutDir = self.args.layout
        self.combine = self.args.combine

        # If the user specified custom version strings for ue4cli and/or conan-ue4cli, process them
        self.ue4cliVersion = self._processPackageVersion("ue4cli", self.args.ue4cli)
        self.conanUe4cliVersion = self._processPackageVersion(
            "conan-ue4cli", self.args.conan_ue4cli
        )

        # Process any specified advanced configuration options (which we use directly as context values for the Jinja templating system)
        self.opts = {}
        for o in self.args.opt:
            if "=" in o:
                key, value = o.split("=", 1)
                self.opts[key.replace("-", "_")] = self._processTemplateValue(value)
            else:
                self.opts[o.replace("-", "_")] = True

        # If we are generating Dockerfiles then generate them for all images that have not been explicitly excluded
        if self.layoutDir is not None:
            self.rebuild = True

        # If we are generating Dockerfiles and combining them then set the corresponding Jinja context value
        if self.layoutDir is not None and self.combine == True:
            self.opts["combine"] = True

        # If the user requested an option that is only compatible with generated Dockerfiles then ensure `-layout` was specified
        if self.layoutDir is None and self.opts.get("source_mode", "git") != "git":
            raise RuntimeError(
                "the `-layout` flag must be used when specifying a non-default value for the `source_mode` option"
            )
        if self.layoutDir is None and self.combine == True:
            raise RuntimeError(
                "the `-layout` flag must be used when specifying the `--combine` flag"
            )

        # We care about source_mode and credential_mode only if we're building source
        if self.buildTargets["source"]:
            # Verify that the value for `source_mode` is valid if specified
            validSourceModes = ["git", "copy"]
            if self.opts.get("source_mode", "git") not in validSourceModes:
                raise RuntimeError(
                    "invalid value specified for the `source_mode` option, valid values are {}".format(
                        validSourceModes
                    )
                )

            # Verify that the value for `credential_mode` is valid if specified
            validCredentialModes = (
                ["endpoint", "secrets"]
                if self.containerPlatform == "linux"
                else ["endpoint"]
            )
            if self.opts.get("credential_mode", "endpoint") not in validCredentialModes:
                raise RuntimeError(
                    "invalid value specified for the `credential_mode` option, valid values are {} when building {} containers".format(
                        validCredentialModes, self.containerPlatform.title()
                    )
                )

        # Generate Jinja context values for keeping or excluding components
        self.opts["excluded_components"] = {
            "ddc": ExcludedComponent.DDC in self.excludedComponents,
            "debug": ExcludedComponent.Debug in self.excludedComponents,
            "templates": ExcludedComponent.Templates in self.excludedComponents,
        }

        # Warn user that they are in danger of Docker 20GB COPY bug
        # Unfortunately, we don't have a cheap way to check whether user environment is affected
        # See https://github.com/adamrehn/ue4-docker/issues/99
        if self.containerPlatform == "windows":
            warn20GiB = False
            if ExcludedComponent.Debug not in self.excludedComponents:
                logger.warning("Warning: You didn't pass --exclude debug", False)
                warn20GiB = True
            if (
                self.release
                and not self.custom
                and semver.VersionInfo.parse(self.release) >= semver.VersionInfo(5, 0)
            ):
                logger.warning("Warning: You're building Unreal Engine 5", False)
                warn20GiB = True

            if warn20GiB:
                logger.warning("Warning: You might hit Docker 20GiB COPY bug", False)
                logger.warning(
                    "Warning: Make sure that `ue4-docker diagnostics 20gig` passes",
                    False,
                )
                logger.warning(
                    "Warning: See https://github.com/adamrehn/ue4-docker/issues/99#issuecomment-1079702817 for details and workarounds",
                    False,
                )

        # If we're building Windows containers, generate our Windows-specific configuration settings
        if self.containerPlatform == "windows":
            self._generateWindowsConfig()

        # If we're building Linux containers, generate our Linux-specific configuration settings
        if self.containerPlatform == "linux":
            self._generateLinuxConfig()

        # If the user-specified suffix passed validation, prefix it with a dash
        self.suffix = "-{}".format(self.suffix) if self.suffix != "" else ""

    def describeExcludedComponents(self):
        """
        Returns a list of strings describing the components that will be excluded (if any.)
        """
        return sorted(
            [
                ExcludedComponent.description(component)
                for component in self.excludedComponents
            ]
        )

    def _generateWindowsConfig(self):
        self.visualStudio = self.args.visual_studio

        if self.release is not None and not self.custom:
            # Check whether specified Unreal Engine release is compatible with specified Visual Studio
            vsMinSupportedUnreal = VisualStudio.MinSupportedUnreal.get(
                self.visualStudio, None
            )
            if (
                vsMinSupportedUnreal is not None
                and semver.VersionInfo.parse(self.release) < vsMinSupportedUnreal
            ):
                raise RuntimeError(
                    "specified version of Unreal Engine cannot be built with Visual Studio {}, oldest supported is {}".format(
                        self.visualStudio, vsMinSupportedUnreal
                    )
                )

        self.visualStudioBuildNumber = VisualStudio.BuildNumbers[self.visualStudio]
        # See https://github.com/EpicGames/UnrealEngine/commit/72585138472785e2ee58aab9950a7260275ee2ac
        # Note: We must not pass VS2019 arg for older UE4 versions that didn't have VS2019 variable in their build graph xml.
        # Otherwise, UAT errors out with "Unknown argument: VS2019".
        if self.visualStudio != VisualStudio.VS2017:
            self.opts["buildgraph_args"] = (
                self.opts.get("buildgraph_args", "")
                + f" -set:VS{self.visualStudio}=true"
            )

        # Determine base tag for the Windows release of the host system
        self.hostBasetag = WindowsUtils.getHostBaseTag()

        # Store the tag for the base Windows Server Core image
        self.basetag = (
            self.args.basetag if self.args.basetag is not None else self.hostBasetag
        )

        if self.basetag is None:
            raise RuntimeError(
                "unable to determine Windows Server Core base image tag from host system. Specify it explicitly using -basetag command-line flag"
            )

        self.baseImage = "mcr.microsoft.com/windows/servercore:" + self.basetag
        self.dllSrcImage = WindowsUtils.getDllSrcImage(self.basetag)
        self.prereqsTag = self.basetag + "-vs" + self.visualStudio

        # If the user has explicitly specified an isolation mode then use it, otherwise auto-detect
        if self.args.isolation is not None:
            self.isolation = self.args.isolation
        else:

            # If we are able to use process isolation mode then use it, otherwise use Hyper-V isolation mode
            differentKernels = self.basetag != self.hostBasetag
            dockerSupportsProcess = parse_version(
                DockerUtils.version()["Version"]
            ) >= parse_version("18.09.0")
            if not differentKernels and dockerSupportsProcess:
                self.isolation = "process"
            else:
                self.isolation = "hyperv"

        # Set the isolation mode Docker flag
        self.platformArgs.append("--isolation=" + self.isolation)

        # If the user has explicitly specified a memory limit then use it, otherwise auto-detect
        self.memLimit = None
        if self.args.m is not None:
            try:
                self.memLimit = humanfriendly.parse_size(self.args.m) / (
                    1000 * 1000 * 1000
                )
            except:
                raise RuntimeError('invalid memory limit "{}"'.format(self.args.m))
        else:

            # Only specify a memory limit when using Hyper-V isolation mode, in order to override the 1GB default limit
            # (Process isolation mode does not impose any memory limits by default)
            if self.isolation == "hyperv":
                self.memLimit = (
                    DEFAULT_MEMORY_LIMIT
                    if self.args.random_memory == False
                    else random.uniform(
                        DEFAULT_MEMORY_LIMIT, DEFAULT_MEMORY_LIMIT + 2.0
                    )
                )

        # Set the memory limit Docker flag
        if self.memLimit is not None:
            self.platformArgs.extend(["-m", "{:.2f}GB".format(self.memLimit)])

    def _generateLinuxConfig(self):

        # Verify that any user-specified tag suffix does not collide with our base tags
        if self.suffix.startswith("opengl") or self.suffix.startswith("cudagl"):
            raise RuntimeError('tag suffix cannot begin with "opengl" or "cudagl".')

        # Determine if we are building CUDA-enabled container images
        self.cuda = None
        if self.args.cuda is not None:

            # Verify that the specified CUDA version is valid
            self.cuda = self.args.cuda if self.args.cuda != "" else DEFAULT_CUDA_VERSION
            # Use the appropriate base image for the specified CUDA version
            self.baseImage = LINUX_BASE_IMAGES["cudagl"]
            self.prereqsTag = "cudagl{cuda}-{ubuntu}"
        else:
            self.baseImage = LINUX_BASE_IMAGES["opengl"]
            self.prereqsTag = "opengl-{ubuntu}"

        self.baseImage = self.baseImage.format(
            cuda=self.args.cuda, ubuntu=self.args.basetag
        )
        self.prereqsTag = self.prereqsTag.format(
            cuda=self.args.cuda, ubuntu=self.args.basetag
        )

    def _processPackageVersion(self, package, version):

        # Leave the version value unmodified if a blank version was specified or a fully-qualified version was specified
        # (e.g. package==X.X.X, package>=X.X.X, git+https://url/for/package/repo.git, etc.)
        if version is None or "/" in version or version.lower().startswith(package):
            return version

        # If a version specifier (e.g. ==X.X.X, >=X.X.X, etc.) was specified, prefix it with the package name
        if "=" in version:
            return package + version

        # If a raw version number was specified, prefix the package name and a strict equality specifier
        return "{}=={}".format(package, version)

    def _processTemplateValue(self, value):

        # If the value is a boolean (either raw or represented by zero or one) then parse it
        if value.lower() in ["true", "1"]:
            return True
        elif value.lower() in ["false", "0"]:
            return False

        # If the value is a JSON object or array then attempt to parse it
        if (value.startswith("{") and value.endswith("}")) or (
            value.startswith("[") and value.endswith("]")
        ):
            try:
                return json.loads(value)
            except:
                print(
                    'Warning: could not parse option value "{}" as JSON, treating value as a string'.format(
                        value
                    )
                )

        # Treat all other values as strings
        return value
