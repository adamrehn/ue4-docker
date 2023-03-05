import contextlib
import io
import logging
import os
import shutil
import sys
import tempfile

import docker
from docker.models.containers import Container


class ContainerUtils(object):
    """
    Provides functionality related to Docker containers
    """

    @staticmethod
    @contextlib.contextmanager
    def automatically_stop(container: Container, timeout: int = 1):
        """
        Context manager to automatically stop a container returned by `ContainerUtils.start_for_exec()`
        """
        try:
            yield container
        finally:
            logging.info("Stopping Docker container {}...".format(container.short_id))
            container.stop(timeout=timeout)

    @staticmethod
    def copy_from_host(
        container: Container, host_path: str, container_path: str
    ) -> None:
        """
        Copies a file or directory from the host system to a container returned by `ContainerUtils.start_for_exec()`.

        `host_path` is the absolute path to the file or directory on the host system.

        `container_path` is the absolute path to the directory in the container where the copied file(s) will be placed.
        """

        # If the host path denotes a file rather than a directory, copy it to a temporary directory
        # (If the host path is a directory then we create a no-op context manager to use in our `with` statement below)
        tempDir = contextlib.suppress()
        if os.path.isfile(host_path):
            tempDir = tempfile.TemporaryDirectory()
            shutil.copy2(
                host_path, os.path.join(tempDir.name, os.path.basename(host_path))
            )
            host_path = tempDir.name

        # Automatically delete the temporary directory if we created one
        with tempDir:
            # Create a temporary file to hold the .tar archive data
            with tempfile.NamedTemporaryFile(
                suffix=".tar", delete=False
            ) as tempArchive:
                # Add the data from the host system to the temporary archive
                tempArchive.close()
                archiveName = os.path.splitext(tempArchive.name)[0]
                shutil.make_archive(archiveName, "tar", host_path)

                # Copy the data from the temporary archive to the container
                with open(tempArchive.name, "rb") as archive:
                    container.put_archive(container_path, archive.read())

                # Remove the temporary archive
                os.unlink(tempArchive.name)

    @staticmethod
    def exec(container: Container, command: [str], capture: bool = False, **kwargs):
        """
        Executes a command in a container returned by `ContainerUtils.start_for_exec()` and streams or captures the output
        """

        # Determine if we are capturing the output or printing it
        stdoutDest = io.StringIO() if capture else sys.stdout
        stderrDest = io.StringIO() if capture else sys.stderr

        # Attempt to start the command
        details = container.client.api.exec_create(container.id, command, **kwargs)
        output = container.client.api.exec_start(details["Id"], stream=True, demux=True)

        # Stream the output
        for chunk in output:
            # Isolate the stdout and stderr chunks
            stdout, stderr = chunk

            # Capture/print the stderr data if we have any
            if stderr is not None:
                print(stderr.decode("utf-8"), end="", flush=True, file=stderrDest)

            # Capture/print the stdout data if we have any
            if stdout is not None:
                print(stdout.decode("utf-8"), end="", flush=True, file=stdoutDest)

        # Determine if the command succeeded
        capturedOutput = (
            (stdoutDest.getvalue(), stderrDest.getvalue()) if capture else None
        )
        result = container.client.api.exec_inspect(details["Id"])["ExitCode"]
        if result != 0:
            container.stop()
            raise RuntimeError(
                "Failed to run command {} in container. Process returned exit code {} with output {}.".format(
                    command,
                    result,
                    capturedOutput if capture else "printed above",
                )
            )

        # If we captured the output then return it
        return capturedOutput

    @staticmethod
    def start_for_exec(
        client: docker.DockerClient, image: str, platform: str, **kwargs
    ) -> Container:
        """
        Starts a container in a detached state using a command that will block indefinitely
        and returns the container handle. The handle can then be used to execute commands
        inside the container. The container will be removed automatically when it is stopped,
        but it will need to be stopped manually by calling `ContainerUtils.stop()`.
        """
        command = (
            ["timeout", "/t", "99999", "/nobreak"]
            if platform == "windows"
            else ["bash", "-c", "sleep infinity"]
        )
        return client.containers.run(
            image,
            command,
            stdin_open=platform == "windows",
            tty=platform == "windows",
            detach=True,
            remove=True,
            **kwargs,
        )
