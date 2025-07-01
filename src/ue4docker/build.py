import argparse, getpass, humanfriendly, json, os, platform, shutil, sys, tempfile, time
from .infrastructure import *
from .version import __version__
from os.path import join


def _getCredential(args, name, envVar, promptFunc):
    # Check if the credential was specified via the command-line
    if getattr(args, name, None) is not None:
        print("Using {} specified via `-{}` command-line argument.".format(name, name))
        return getattr(args, name)

    # Check if the credential was specified via an environment variable
    if envVar in os.environ:
        print("Using {} specified via {} environment variable.".format(name, envVar))
        return os.environ[envVar]

    # Fall back to prompting the user for the value
    return promptFunc()


def _getUsername(args):
    return _getCredential(
        args, "username", "UE4DOCKER_USERNAME", lambda: input("Username: ")
    )


def _getPassword(args):
    return _getCredential(
        args,
        "password",
        "UE4DOCKER_PASSWORD",
        lambda: getpass.getpass("Access token or password: "),
    )


def build():
    # Create our logger to generate coloured output on stderr
    logger = Logger(prefix="[{} build] ".format(sys.argv[0]))

    # Register our supported command-line arguments
    parser = argparse.ArgumentParser(prog="{} build".format(sys.argv[0]))
    BuildConfiguration.addArguments(parser)

    # If no command-line arguments were supplied, display the help message and exit
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(0)

    # Parse the supplied command-line arguments
    try:
        config = BuildConfiguration(parser, sys.argv[1:], logger)
    except RuntimeError as e:
        logger.error("Error: {}".format(e))
        sys.exit(1)

    # Verify that Docker is installed
    if DockerUtils.installed() == False:
        logger.error(
            "Error: could not detect Docker version. Please ensure Docker is installed."
        )
        sys.exit(1)

    # Verify that we aren't trying to build Windows containers under Windows 10 when in Linux container mode (or vice versa)
    # (Note that we don't bother performing this check when we're just copying Dockerfiles to an output directory)
    if config.layoutDir is None:
        dockerPlatform = DockerUtils.info()["OSType"].lower()
        if config.containerPlatform == "windows" and dockerPlatform == "linux":
            logger.error(
                "Error: cannot build Windows containers when Docker Desktop is in Linux container",
                False,
            )
            logger.error(
                "mode. Use the --linux flag if you want to build Linux containers instead.",
                False,
            )
            sys.exit(1)
        elif config.containerPlatform == "linux" and dockerPlatform == "windows":
            logger.error(
                "Error: cannot build Linux containers when Docker Desktop is in Windows container",
                False,
            )
            logger.error(
                "mode. Remove the --linux flag if you want to build Windows containers instead.",
                False,
            )
            sys.exit(1)

    # Warn the user if they're using an older version of Docker that can't build or run UE 5.4 Linux images without config changes
    if (
        config.containerPlatform == "linux"
        and DockerUtils.isVersionWithoutIPV6Loopback()
    ):
        logger.warning(
            DockerUtils.getIPV6WarningMessage() + "\n",
            False,
        )

    # Create an auto-deleting temporary directory to hold our build context
    with tempfile.TemporaryDirectory() as tempDir:
        contextOrig = join(os.path.dirname(os.path.abspath(__file__)), "dockerfiles")

        # Create the builder instance to build the Docker images
        builder = ImageBuilder(
            join(tempDir, "dockerfiles"),
            config.containerPlatform,
            logger,
            config.rebuild,
            config.dryRun,
            config.layoutDir,
            config.opts,
            config.combine,
        )

        # Resolve our main set of tags for the generated images; this is used only for Source and downstream
        if config.buildTargets["source"]:
            mainTags = [
                "{}{}-{}".format(config.release, config.suffix, config.prereqsTag),
                config.release + config.suffix,
            ]

        # Print the command-line invocation that triggered this build, masking any supplied passwords
        args = [
            (
                "*******"
                if config.args.password is not None and arg == config.args.password
                else arg
            )
            for arg in sys.argv
        ]
        logger.info("COMMAND-LINE INVOCATION:", False)
        logger.info(str(args), False)

        # Print the details of the Unreal Engine version being built
        logger.info("UNREAL ENGINE VERSION SETTINGS:")
        logger.info(
            "Custom build:  {}".format("Yes" if config.custom == True else "No"), False
        )
        if config.custom == True:
            logger.info("Custom name:   " + config.release, False)
        elif config.release is not None:
            logger.info("Release:       " + config.release, False)
        if config.repository is not None:
            logger.info("Repository:    " + config.repository, False)
            logger.info("Branch/tag:    " + config.branch + "\n", False)

        # Determine if we are using a custom version for ue4cli or conan-ue4cli
        if config.ue4cliVersion is not None or config.conanUe4cliVersion is not None:
            logger.info("CUSTOM PACKAGE VERSIONS:", False)
            logger.info(
                "ue4cli:        {}".format(
                    config.ue4cliVersion
                    if config.ue4cliVersion is not None
                    else "default"
                ),
                False,
            )
            logger.info(
                "conan-ue4cli:  {}\n".format(
                    config.conanUe4cliVersion
                    if config.conanUe4cliVersion is not None
                    else "default"
                ),
                False,
            )

        # Report any advanced configuration options that were specified
        if len(config.opts) > 0:
            logger.info("ADVANCED CONFIGURATION OPTIONS:", False)
            for key, value in sorted(config.opts.items()):
                logger.info("{}: {}".format(key, json.dumps(value)), False)
            print("", file=sys.stderr, flush=True)

        # Determine if we are building Windows or Linux containers
        if config.containerPlatform == "windows":
            # Provide the user with feedback so they are aware of the Windows-specific values being used
            logger.info("WINDOWS CONTAINER SETTINGS", False)
            logger.info(
                "Isolation mode:               {}".format(config.isolation), False
            )
            logger.info(
                "Base OS image:                {}".format(config.baseImage), False
            )
            logger.info(
                "Dll source image:             {}".format(config.dllSrcImage), False
            )
            logger.info(
                "Host OS:                      {}".format(WindowsUtils.systemString()),
                False,
            )
            logger.info(
                "Memory limit:                 {}".format(
                    "No limit"
                    if config.memLimit is None
                    else "{:.2f}GB".format(config.memLimit)
                ),
                False,
            )
            logger.info(
                "Detected max image size:      {:.0f}GB".format(DockerUtils.maxsize()),
                False,
            )
            logger.info(
                "Visual Studio:                {}".format(config.visualStudio), False
            )

            # Verify that the host OS is not a release that is blacklisted due to critical bugs
            if (
                config.ignoreBlacklist == False
                and WindowsUtils.isBlacklistedWindowsHost() == True
            ):
                logger.error(
                    "Error: detected blacklisted host OS version: {}".format(
                        WindowsUtils.systemString()
                    ),
                    False,
                )
                logger.error("", False)
                logger.error(
                    "This version of Windows contains one or more critical bugs that",
                    False,
                )
                logger.error(
                    "render it incapable of successfully building UE4 container images.",
                    False,
                )
                logger.error(
                    "You will need to use an older or newer version of Windows.", False
                )
                logger.error("", False)
                logger.error("For more information, see:", False)
                logger.error(
                    "https://unrealcontainers.com/docs/concepts/windows-containers",
                    False,
                )
                sys.exit(1)

            # Verify that the user is not attempting to build images with a newer kernel version than the host OS
            newer_check = WindowsUtils.isNewerBaseTag(
                config.hostBasetag, config.basetag
            )
            if newer_check:
                logger.error(
                    "Error: cannot build container images with a newer kernel version than that of the host OS!"
                )
                sys.exit(1)
            elif newer_check is None:
                logger.warning(
                    "Warning: unable to determine whether host system is new enough to use specified base tag"
                )

            # Ensure the Docker daemon is configured correctly
            requiredLimit = WindowsUtils.requiredSizeLimit()
            if DockerUtils.maxsize() < requiredLimit and config.buildTargets["source"]:
                logger.error("SETUP REQUIRED:")
                logger.error(
                    "The max image size for Windows containers must be set to at least {}GB.".format(
                        requiredLimit
                    )
                )
                logger.error(
                    "See the Microsoft documentation for configuration instructions:"
                )
                logger.error(
                    "https://docs.microsoft.com/en-us/virtualization/windowscontainers/manage-containers/container-storage#storage-limits"
                )
                logger.error(
                    "Under Windows Server, the command `{} setup` can be used to automatically configure the system.".format(
                        sys.argv[0]
                    )
                )
                sys.exit(1)

        elif config.containerPlatform == "linux":
            logger.info("LINUX CONTAINER SETTINGS", False)
            logger.info(
                "Base OS image: {}\n".format(config.baseImage),
                False,
            )

        # Report which Engine components are being excluded (if any)
        logger.info("GENERAL SETTINGS", False)
        logger.info(
            "Build targets: {}".format(
                " ".join(
                    sorted(
                        [
                            target
                            for target, enabled in config.buildTargets.items()
                            if enabled
                        ]
                    )
                )
            ),
            False,
        )
        logger.info(
            "Changelist override: {}".format(
                config.changelist
                if config.changelist is not None
                else "(None specified)"
            ),
            False,
        )
        if len(config.excludedComponents) > 0:
            logger.info("Excluding the following Engine components:", False)
            for component in config.describeExcludedComponents():
                logger.info("- {}".format(component), False)
        else:
            logger.info("Not excluding any Engine components.", False)

        # Print a warning if the user is attempting to build Linux images under Windows
        if config.containerPlatform == "linux" and (
            platform.system() == "Windows" or WindowsUtils.isWSL()
        ):
            logger.warning(
                "Warning: attempting to build Linux container images under Windows (e.g. via WSL)."
            )
            logger.warning(
                "The ue4-docker maintainers do not provide support for building and running Linux",
                False,
            )
            logger.warning(
                "containers under Windows, and this configuration is not tested to verify that it",
                False,
            )
            logger.warning(
                "functions correctly. Users are solely responsible for troubleshooting any issues",
                False,
            )
            logger.warning(
                "they encounter when attempting to build Linux container images under Windows.",
                False,
            )

        # Determine if we need to prompt for credentials
        if config.dryRun == True:
            # Don't bother prompting the user for any credentials during a dry run
            logger.info(
                "Performing a dry run, `docker build` commands will be printed and not executed."
            )
            username = ""
            password = ""

        elif config.layoutDir is not None:
            # Don't bother prompting the user for any credentials when we're just copying the Dockerfiles to a directory
            logger.info(
                "Copying generated Dockerfiles to: {}".format(config.layoutDir), False
            )
            username = ""
            password = ""

        elif (
            not config.buildTargets["source"]
            or builder.willBuild("ue4-source", mainTags) == False
        ):
            # Don't bother prompting the user for any credentials if we're not building the ue4-source image
            logger.info(
                "Not building the ue4-source image, no Git credentials required.", False
            )
            username = ""
            password = ""

        else:
            # Retrieve the Git username and password from the user when building the ue4-source image
            print(
                "\nRetrieving the Git credentials that will be used to clone the UE4 repo"
            )
            username = _getUsername(config.args)
            password = _getPassword(config.args)
            print()

        # If resource monitoring has been enabled, start the resource monitoring background thread
        resourceMonitor = ResourceMonitor(logger, config.args.interval)
        if config.args.monitor == True:
            resourceMonitor.start()

        # Prep for endpoint cleanup, if necessary
        endpoint = None

        try:
            # Keep track of our starting time
            startTime = time.time()

            # If we're copying Dockerfiles to an output directory then make sure it exists and is empty
            if config.layoutDir is not None:
                if os.path.exists(config.layoutDir):
                    shutil.rmtree(config.layoutDir)
                os.makedirs(config.layoutDir)

            # Keep track of the images we've built
            builtImages = []

            commonArgs = [
                "--build-arg",
                "NAMESPACE={}".format(GlobalConfiguration.getTagNamespace()),
            ] + config.args.docker_build_args

            # Build the UE4 build prerequisites image
            if config.buildTargets["build-prerequisites"]:
                # Compute the build options for the UE4 build prerequisites image
                # (This is the only image that does not use any user-supplied tag suffix, since the tag always reflects any customisations)
                prereqsArgs = ["--build-arg", "BASEIMAGE=" + config.baseImage]
                if config.containerPlatform == "windows":
                    prereqsArgs = prereqsArgs + [
                        "--build-arg",
                        "DLLSRCIMAGE=" + config.dllSrcImage,
                        "--build-arg",
                        "VISUAL_STUDIO_BUILD_NUMBER="
                        + config.visualStudio.build_number,
                        "--build-arg",
                        "UE_VERSION=" + config.release,
                    ]

                custom_prerequisites_dockerfile = config.args.prerequisites_dockerfile
                if custom_prerequisites_dockerfile is not None:
                    builder.build_builtin_image(
                        "ue4-base-build-prerequisites",
                        [config.prereqsTag],
                        commonArgs + config.platformArgs + prereqsArgs,
                        builtin_name="ue4-build-prerequisites",
                    )
                    builtImages.append("ue4-base-build-prerequisites")
                else:
                    builder.build_builtin_image(
                        "ue4-build-prerequisites",
                        [config.prereqsTag],
                        commonArgs + config.platformArgs + prereqsArgs,
                    )

                prereqConsumerArgs = [
                    "--build-arg",
                    "PREREQS_TAG={}".format(config.prereqsTag),
                ]

                if custom_prerequisites_dockerfile is not None:
                    builder.build(
                        "ue4-build-prerequisites",
                        [config.prereqsTag],
                        commonArgs + config.platformArgs + prereqConsumerArgs,
                        dockerfile_template=custom_prerequisites_dockerfile,
                        context_dir=os.path.dirname(custom_prerequisites_dockerfile),
                    )

                builtImages.append("ue4-build-prerequisites")
            else:
                logger.info("Skipping ue4-build-prerequisities image build.")

            # Build the UE4 source image
            if config.buildTargets["source"]:
                # Start the HTTP credential endpoint as a child process and wait for it to start
                if config.opts["credential_mode"] == "endpoint":
                    endpoint = CredentialEndpoint(username, password)
                    endpoint.start()

                # If we're using build secrets then pass the Git username and password to the UE4 source image as secrets
                secrets = {}
                if config.opts["credential_mode"] == "secrets":
                    secrets = {"username": username, "password": password}
                credentialArgs = [] if len(secrets) > 0 else endpoint.args()

                ue4SourceArgs = prereqConsumerArgs + [
                    "--build-arg",
                    "GIT_REPO={}".format(config.repository),
                    "--build-arg",
                    "GIT_BRANCH={}".format(config.branch),
                    "--build-arg",
                    "VERBOSE_OUTPUT={}".format("1" if config.verbose == True else "0"),
                ]

                changelistArgs = (
                    ["--build-arg", "CHANGELIST={}".format(config.changelist)]
                    if config.changelist is not None
                    else []
                )

                builder.build_builtin_image(
                    "ue4-source",
                    mainTags,
                    commonArgs
                    + config.platformArgs
                    + ue4SourceArgs
                    + credentialArgs
                    + changelistArgs,
                    secrets=secrets,
                )
                builtImages.append("ue4-source")
            else:
                logger.info("Skipping ue4-source image build.")

            # Build the minimal UE4 CI image, unless requested otherwise by the user
            if config.buildTargets["minimal"]:
                minimalArgs = prereqConsumerArgs + [
                    "--build-arg",
                    "TAG={}".format(mainTags[1]),
                ]

                builder.build_builtin_image(
                    "ue4-minimal",
                    mainTags,
                    commonArgs + config.platformArgs + minimalArgs,
                )
                builtImages.append("ue4-minimal")
            else:
                logger.info("Skipping ue4-minimal image build.")

            # Build the full UE4 CI image, unless requested otherwise by the user
            if config.buildTargets["full"]:
                # If custom version strings were specified for ue4cli and/or conan-ue4cli, use them
                infrastructureFlags = []
                if config.ue4cliVersion is not None:
                    infrastructureFlags.extend(
                        [
                            "--build-arg",
                            "UE4CLI_VERSION={}".format(config.ue4cliVersion),
                        ]
                    )
                if config.conanUe4cliVersion is not None:
                    infrastructureFlags.extend(
                        [
                            "--build-arg",
                            "CONAN_UE4CLI_VERSION={}".format(config.conanUe4cliVersion),
                        ]
                    )

                # Build the image
                builder.build_builtin_image(
                    "ue4-full",
                    mainTags,
                    commonArgs
                    + config.platformArgs
                    + ue4BuildArgs
                    + infrastructureFlags,
                )
                builtImages.append("ue4-full")
            else:
                logger.info("Skipping ue4-full image build.")

            # If we are generating Dockerfiles then include information about the options used to generate them
            if config.layoutDir is not None:
                # Determine whether we generated a single combined Dockerfile or a set of Dockerfiles
                if config.combine == True:
                    # Generate a comment to place at the top of the single combined Dockerfile
                    lines = [
                        "This file was generated by ue4-docker version {} with the following options:".format(
                            __version__
                        ),
                        "",
                    ]
                    lines.extend(
                        [
                            "- {}: {}".format(key, json.dumps(value))
                            for key, value in sorted(config.opts.items())
                        ]
                    )
                    lines.extend(
                        [
                            "",
                            "This Dockerfile combines the steps for the following images:",
                            "",
                        ]
                    )
                    lines.extend(["- {}".format(image) for image in builtImages])
                    comment = "\n".join(["# {}".format(line) for line in lines])

                    # Inject the comment at the top of the Dockerfile, being sure to place it after any `escape` parser directive
                    dockerfile = join(config.layoutDir, "combined", "Dockerfile")
                    dockerfileContents = FilesystemUtils.readFile(dockerfile)
                    if dockerfileContents.startswith("# escape"):
                        newline = dockerfileContents.index("\n")
                        dockerfileContents = (
                            dockerfileContents[0 : newline + 1]
                            + "\n"
                            + comment
                            + "\n\n"
                            + dockerfileContents[newline + 1 :]
                        )
                    else:
                        dockerfileContents = comment + "\n\n" + dockerfileContents
                    FilesystemUtils.writeFile(dockerfile, dockerfileContents)

                else:
                    # Create a JSON file to accompany the set of generated Dockerfiles
                    FilesystemUtils.writeFile(
                        join(config.layoutDir, "generated.json"),
                        json.dumps(
                            {
                                "version": __version__,
                                "images": builtImages,
                                "opts": config.opts,
                            },
                            indent=4,
                            sort_keys=True,
                        ),
                    )

            # Report the total execution time
            endTime = time.time()
            logger.action(
                "Total execution time: {}".format(
                    humanfriendly.format_timespan(endTime - startTime)
                )
            )

            # Stop the resource monitoring background thread if it is running
            resourceMonitor.stop()

            # Stop the HTTP server
            if endpoint is not None:
                endpoint.stop()

        except (Exception, KeyboardInterrupt) as e:
            # One of the images failed to build
            logger.error("Error: {}".format(e))
            resourceMonitor.stop()
            if endpoint is not None:
                endpoint.stop()
            sys.exit(1)
