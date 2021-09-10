from ..infrastructure import DockerUtils, SubprocessUtils
import json, os, platform, shutil, subprocess, sys


def exportInstalledBuild(image, destination, extraArgs):

    # Verify that we are running under Linux
    if platform.system() != "Linux":
        print(
            "Error: Installed Builds can only be exported under Linux.", file=sys.stderr
        )
        sys.exit(1)

    # Verify that the destination directory does not already exist
    if os.path.exists(destination) == True:
        print("Error: the destination directory already exists.", file=sys.stderr)
        sys.exit(1)

    # Verify that the Installed Build in the specified image is at least 4.21.0
    versionResult = SubprocessUtils.capture(
        [
            "docker",
            "run",
            "--rm",
            "-ti",
            image,
            "cat",
            "/home/ue4/UnrealEngine/Engine/Build/Build.version",
        ],
        universal_newlines=True,
    )
    try:
        version = json.loads(versionResult.stdout)
        if version["MajorVersion"] == 4 and version["MinorVersion"] < 21:
            raise Exception()
    except:
        print(
            "Error: Installed Builds can only be exported for Unreal Engine 4.21.0 and newer.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Start a container from which we will copy files
    container = DockerUtils.start(image, "bash")

    # Attempt to perform the export
    print("Exporting to {}...".format(destination))
    containerPath = "{}:/home/ue4/UnrealEngine".format(container.name)
    exportResult = subprocess.call(["docker", "cp", containerPath, destination])

    # Stop the container, irrespective of whether or not the export succeeded
    container.stop()

    # If the export succeeded, regenerate the linker symlinks on the host system
    if exportResult == 0:
        print("Performing linker symlink fixup...")
        subprocess.call(
            [
                sys.executable,
                os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "dockerfiles",
                    "ue4-source",
                    "linux",
                    "linker-fixup.py",
                ),
                os.path.join(
                    destination,
                    "Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux/Linux_x64",
                ),
                shutil.which("ld"),
            ]
        )

    # Report any failures
    if exportResult != 0:
        print("Error: failed to export Installed Build.", file=sys.stderr)
        sys.exit(1)
