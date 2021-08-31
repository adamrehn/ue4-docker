from ..infrastructure import DockerUtils, WindowsUtils
from .base import DiagnosticBase

import argparse, os, platform
from os.path import abspath, dirname, join


class diagnostic8Gig(DiagnosticBase):

    # The tag we use for built images
    IMAGE_TAG = "adamrehn/ue4-docker/diagnostics:8gig"

    def __init__(self):

        # Setup our argument parser so we can use its help message output in our description text
        self._parser = argparse.ArgumentParser(prog="ue4-docker diagnostics 8gig")
        self._parser.add_argument(
            "--linux",
            action="store_true",
            help="Use Linux containers under Windows hosts (useful when testing Docker Desktop or LCOW support)",
        )
        self._parser.add_argument(
            "--random",
            action="store_true",
            help="Create a file filled with random bytes instead of zeroes under Windows",
        )
        self._parser.add_argument(
            "--isolation",
            default=None,
            choices=["hyperv", "process"],
            help="Override the default isolation mode when testing Windows containers",
        )
        self._parser.add_argument(
            "-basetag",
            default=None,
            choices=WindowsUtils.getKnownBaseTags(),
            help="Override the default base image tag when testing Windows containers",
        )

    def getName(self):
        """
        Returns the human-readable name of the diagnostic
        """
        return "Check for Docker 8GiB filesystem layer bug"

    def getDescription(self):
        """
        Returns a description of what the diagnostic does
        """
        return "\n".join(
            [
                "This diagnostic determines if the Docker daemon suffers from one of the 8GiB filesystem",
                "layer bugs reported at https://github.com/moby/moby/issues/37581 (affects all platforms)",
                "or https://github.com/moby/moby/issues/40444 (affects Windows containers only)",
                "",
                "#37581 was fixed in Docker CE 18.09.0 and #40444 was fixed in Docker CE 20.10.0",
                "",
                self._parser.format_help(),
            ]
        )

    def getPrefix(self):
        """
        Returns the short name of the diagnostic for use in log output
        """
        return "8gig"

    def run(self, logger, args=[]):
        """
        Runs the diagnostic
        """

        # Parse our supplied arguments
        args = self._parser.parse_args(args)

        # Determine which image platform we will build the Dockerfile for (default is the host platform unless overridden)
        containerPlatform = (
            "linux"
            if args.linux == True or platform.system().lower() != "windows"
            else "windows"
        )

        # Verify that the user isn't trying to test Windows containers under Windows 10 when in Linux container mode (or vice versa)
        try:
            self._checkPlatformMistmatch(logger, containerPlatform)
        except RuntimeError:
            return False

        # Set our build arguments when testing Windows containers
        buildArgs = (
            self._generateWindowsBuildArgs(logger, args.basetag, args.isolation)
            if containerPlatform == "windows"
            else []
        )

        # Attempt to build the Dockerfile
        logger.action(
            "[8gig] Attempting to build an image with an 8GiB filesystem layer...",
            False,
        )
        built = self._buildDockerfile(
            logger, containerPlatform, diagnostic8Gig.IMAGE_TAG, buildArgs
        )

        # Inform the user of the outcome of the diagnostic
        if built == True:
            logger.action(
                "[8gig] Diagnostic succeeded! The Docker daemon can build images with 8GiB filesystem layers.\n"
            )
        else:
            logger.error(
                "[8gig] Diagnostic failed! The Docker daemon cannot build images with 8GiB filesystem layers.\n",
                True,
            )

        return built
