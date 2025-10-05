import tempfile

from docker.models.containers import Container

from ..infrastructure import DockerUtils, SubprocessUtils
import json, os, platform, shutil, subprocess, sys


def exportInstalledBuild(image, destination, extraArgs):
    # Verify that the destination directory does not already exist
    if os.path.exists(destination) == True:
        print("Error: the destination directory already exists.", file=sys.stderr)
        sys.exit(1)

    # Create a container from which we will copy files
    container = DockerUtils.create(image)

    exit_code = 1
    try:
        exit_code = doExportInstalledBuild(container, destination, extraArgs)
    except Exception as e:
        print("Error: failed to export Installed Build.", file=sys.stderr)
        raise e
    finally:
        # Remove the container, irrespective of whether or not the export succeeded
        container.remove()

        sys.exit(exit_code)


def doExportInstalledBuild(container: Container, destination: str, extraArgs) -> int:
    if platform.system() == "Windows":
        engineRoot = "C:/UnrealEngine"
    else:
        engineRoot = "/home/ue4/UnrealEngine"

    with tempfile.TemporaryDirectory() as tmpdir:
        versionFilePath = os.path.join(tmpdir, "Build.version")
        # Verify that the Installed Build in the specified image is at least 4.21.0
        subprocess.run(
            [
                "docker",
                "cp",
                f"{container.name}:{engineRoot}/Engine/Build/Build.version",
                versionFilePath,
            ],
            check=True,
        )
        try:
            with open(versionFilePath, "r") as versionFile:
                version = json.load(versionFile)
                if version["MajorVersion"] == 4 and version["MinorVersion"] < 21:
                    raise Exception()
        except:
            print(
                "Error: Installed Builds can only be exported for Unreal Engine 4.21.0 and newer.",
                file=sys.stderr,
            )
            return 1

    # Attempt to perform the export
    print("Exporting to {}...".format(destination))
    subprocess.run(
        ["docker", "cp", f"{container.name}:{engineRoot}", destination], check=True
    )
