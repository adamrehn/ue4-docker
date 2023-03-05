import ntpath
import os
import posixpath
import sys

import docker
from docker.errors import ImageNotFound

from .infrastructure import (
    ContainerUtils,
    GlobalConfiguration,
    Logger,
)


def test():
    # Create our logger to generate coloured output on stderr
    logger = Logger(prefix="[{} test] ".format(sys.argv[0]))

    # Create our Docker API client
    client = docker.from_env()

    # Check that an image tag has been specified
    if len(sys.argv) > 1 and sys.argv[1].strip("-") not in ["h", "help"]:
        # Verify that the specified container image exists
        tag = sys.argv[1]
        image_name = GlobalConfiguration.resolveTag(
            "ue4-full:{}".format(tag) if ":" not in tag else tag
        )

        try:
            image = client.images.get(image_name)
        except ImageNotFound:
            logger.error(
                'Error: the specified container image "{}" does not exist.'.format(
                    image_name
                )
            )
            sys.exit(1)

        # Use process isolation mode when testing Windows containers, since running Hyper-V containers don't currently support manipulating the filesystem
        platform = image.attrs["Os"]
        isolation = "process" if platform == "windows" else None

        # Start a container to run our tests in, automatically stopping and removing the container when we finish
        logger.action(
            'Starting a container using the "{}" image...'.format(image_name), False
        )
        container = ContainerUtils.start_for_exec(
            client, image_name, platform, isolation=isolation
        )
        with ContainerUtils.automatically_stop(container):
            # Create the workspace directory in the container
            workspaceDir = (
                "C:\\workspace" if platform == "windows" else "/tmp/workspace"
            )
            shell_prefix = (
                ["cmd", "/S", "/C"] if platform == "windows" else ["bash", "-c"]
            )

            ContainerUtils.exec(
                container,
                shell_prefix + ["mkdir " + workspaceDir],
            )

            # Copy our test scripts into the container
            testDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests")
            ContainerUtils.copy_from_host(container, testDir, workspaceDir)

            # Create a harness to invoke individual tests
            containerPath = ntpath if platform == "windows" else posixpath
            pythonCommand = "python" if platform == "windows" else "python3"

            def runTest(script):
                logger.action('Running test "{}"...'.format(script), False)
                try:
                    ContainerUtils.exec(
                        container,
                        [pythonCommand, containerPath.join(workspaceDir, script)],
                        workdir=workspaceDir,
                    )
                    logger.action('Passed test "{}"'.format(script), False)
                except RuntimeError as e:
                    logger.error('Error: test "{}" failed!'.format(script))
                    raise e from None

            # Run each of our tests in turn
            runTest("build-and-package.py")
            runTest("consume-external-deps.py")

            # If we've reached this point then all of the tests passed
            logger.action("All tests passed.", False)

    else:
        # Print usage syntax
        print("Usage: {} test TAG".format(sys.argv[0]))
        print("Runs tests to verify the correctness of built container images\n")
        print("TAG should specify the tag of the ue4-full image to test.")
