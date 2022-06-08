from typing import Dict, Optional

from .DockerUtils import DockerUtils
from .FilesystemUtils import FilesystemUtils
from .GlobalConfiguration import GlobalConfiguration
import glob, humanfriendly, os, shutil, subprocess, tempfile, time
from os.path import basename, exists, join
from jinja2 import Environment


class ImageBuildParams(object):
    def __init__(
        self, dockerfile: str, context_dir: str, env: Optional[Dict[str, str]] = None
    ):
        self.dockerfile = dockerfile
        self.context_dir = context_dir
        self.env = env


class ImageBuilder(object):
    def __init__(
        self,
        tempDir: str,
        platform: str,
        logger,
        rebuild: bool = False,
        dryRun: bool = False,
        layoutDir: str = None,
        templateContext: Dict[str, str] = None,
        combine: bool = False,
    ):
        """
        Creates an ImageBuilder for the specified build parameters
        """
        self.tempDir = tempDir
        self.platform = platform
        self.logger = logger
        self.rebuild = rebuild
        self.dryRun = dryRun
        self.layoutDir = layoutDir
        self.templateContext = templateContext if templateContext is not None else {}
        self.combine = combine

    def get_built_image_context(self, name):
        """
        Resolve the full path to the build context for the specified image
        """
        return os.path.normpath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..",
                "dockerfiles",
                basename(name),
                self.platform,
            )
        )

    def build_builtin_image(
        self,
        name: str,
        tags: [str],
        args: [str],
        builtin_name: str = None,
        secrets: Dict[str, str] = None,
    ):
        context_dir = self.get_built_image_context(
            name if builtin_name is None else builtin_name
        )
        return self.build(
            name, tags, args, join(context_dir, "Dockerfile"), context_dir, secrets
        )

    def build(
        self,
        name: str,
        tags: [str],
        args: [str],
        dockerfile_template: str,
        context_dir: str,
        secrets: Dict[str, str] = None,
    ):
        """
        Builds the specified image if it doesn't exist or if we're forcing a rebuild
        """

        workdir = join(self.tempDir, basename(name), self.platform)
        os.makedirs(workdir, exist_ok=True)

        # Create a Jinja template environment and render the Dockerfile template
        environment = Environment(
            autoescape=False, trim_blocks=True, lstrip_blocks=True
        )
        dockerfile = join(workdir, "Dockerfile")

        templateInstance = environment.from_string(
            FilesystemUtils.readFile(dockerfile_template)
        )
        rendered = templateInstance.render(self.templateContext)

        # Compress excess whitespace introduced during Jinja rendering and save the contents back to disk
        # (Ensure that we still have a single trailing newline at the end of the Dockerfile)
        while "\n\n\n" in rendered:
            rendered = rendered.replace("\n\n\n", "\n\n")
        rendered = rendered.strip("\n") + "\n"
        FilesystemUtils.writeFile(dockerfile, rendered)

        # Inject our filesystem layer commit message after each RUN directive in the Dockerfile
        DockerUtils.injectPostRunMessage(
            dockerfile,
            self.platform,
            [
                "",
                "RUN directive complete. Docker will now commit the filesystem layer to disk.",
                "Note that for large filesystem layers this can take quite some time.",
                "Performing filesystem layer commit...",
                "",
            ],
        )

        # Create a temporary directory to hold any files needed for the build
        with tempfile.TemporaryDirectory() as tempDir:

            # Determine whether we are building using `docker buildx` with build secrets
            imageTags = self._formatTags(name, tags)

            if self.platform == "linux" and secrets is not None and len(secrets) > 0:

                # Create temporary files to store the contents of each of our secrets
                secretFlags = []
                for secret, contents in secrets.items():
                    secretFile = join(tempDir, secret)
                    FilesystemUtils.writeFile(secretFile, contents)
                    secretFlags.append("id={},src={}".format(secret, secretFile))

                # Generate the `docker buildx` command to use our build secrets
                command = DockerUtils.buildx(imageTags, context_dir, args, secretFlags)
            else:
                command = DockerUtils.build(imageTags, context_dir, args)

            command += ["--file", dockerfile]

            env = os.environ.copy()
            if self.platform == "linux":
                env["DOCKER_BUILDKIT"] = "1"

            # Build the image if it doesn't already exist
            self._processImage(
                imageTags[0],
                name,
                command,
                "build",
                "built",
                ImageBuildParams(dockerfile, context_dir, env),
            )

    def pull(self, image: str) -> None:
        """
        Pulls the specified image if it doesn't exist or if we're forcing a pull of a newer version
        """
        self._processImage(image, None, DockerUtils.pull(image), "pull", "pulled")

    def willBuild(self, name: str, tags: [str]) -> bool:
        """
        Determines if we will build the specified image, based on our build settings
        """
        imageTags = self._formatTags(name, tags)
        return self._willProcess(imageTags[0])

    def _formatTags(self, name: str, tags: [str]):
        """
        Generates the list of fully-qualified tags that we will use when building an image
        """
        return [
            "{}:{}".format(GlobalConfiguration.resolveTag(name), tag) for tag in tags
        ]

    def _willProcess(self, image: [str]) -> bool:
        """
        Determines if we will build or pull the specified image, based on our build settings
        """
        return self.rebuild or not DockerUtils.exists(image)

    def _processImage(
        self,
        image: str,
        name: Optional[str],
        command: [str],
        actionPresentTense: str,
        actionPastTense: str,
        build_params: Optional[ImageBuildParams] = None,
    ) -> None:
        """
        Processes the specified image by running the supplied command if it doesn't exist (use rebuild=True to force processing)
        """

        # Determine if we are processing the image
        if not self._willProcess(image):
            self.logger.info(
                'Image "{}" exists and rebuild not requested, skipping {}.'.format(
                    image, actionPresentTense
                )
            )
            return

        # Determine if we are running in "dry run" mode
        self.logger.action(
            '{}ing image "{}"...'.format(actionPresentTense.capitalize(), image)
        )
        if self.dryRun:
            print(command)
            self.logger.action(
                'Completed dry run for image "{}".'.format(image), newline=False
            )
            return

        # Determine if we're just copying the Dockerfile to an output directory
        if self.layoutDir is not None:

            # Determine whether we're performing a simple copy or combining generated Dockerfiles
            if self.combine:

                # Ensure the destination directory exists
                dest = join(self.layoutDir, "combined")
                self.logger.action(
                    'Merging "{}" into "{}"...'.format(build_params.context_dir, dest),
                    newline=False,
                )
                os.makedirs(dest, exist_ok=True)

                # Merge the source Dockerfile with any existing Dockerfile contents in the destination directory
                # (Insert a single newline between merged file contents and ensure we have a single trailing newline)
                sourceDockerfile = build_params.dockerfile
                destDockerfile = join(dest, "Dockerfile")
                dockerfileContents = (
                    FilesystemUtils.readFile(destDockerfile)
                    if exists(destDockerfile)
                    else ""
                )
                dockerfileContents = (
                    dockerfileContents
                    + "\n"
                    + FilesystemUtils.readFile(sourceDockerfile)
                )
                dockerfileContents = dockerfileContents.strip("\n") + "\n"
                FilesystemUtils.writeFile(destDockerfile, dockerfileContents)

                # Copy any supplemental files from the source directory to the destination directory
                # (Exclude any extraneous files which are not referenced in the Dockerfile contents)
                for file in glob.glob(join(build_params.context_dir, "*.*")):
                    if basename(file) in dockerfileContents:
                        shutil.copy(file, join(dest, basename(file)))

                # Report our success
                self.logger.action(
                    'Merged Dockerfile for image "{}".'.format(image), newline=False
                )

            else:

                # Copy the source directory to the destination
                dest = join(self.layoutDir, basename(name))
                self.logger.action(
                    'Copying "{}" to "{}"...'.format(build_params.context_dir, dest),
                    newline=False,
                )
                shutil.copytree(build_params.context_dir, dest)
                shutil.copy(build_params.dockerfile, dest)
                self.logger.action(
                    'Copied Dockerfile for image "{}".'.format(image), newline=False
                )

            return

        # Attempt to process the image using the supplied command
        startTime = time.time()
        exitCode = subprocess.call(
            command, env=build_params.env if build_params else None
        )
        endTime = time.time()

        # Determine if processing succeeded
        if exitCode == 0:
            self.logger.action(
                '{} image "{}" in {}'.format(
                    actionPastTense.capitalize(),
                    image,
                    humanfriendly.format_timespan(endTime - startTime),
                ),
                newline=False,
            )
        else:
            raise RuntimeError(
                'failed to {} image "{}".'.format(actionPresentTense, image)
            )
