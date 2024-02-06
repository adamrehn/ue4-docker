#!/usr/bin/env python3
import argparse, os, platform, subprocess, sys, traceback
from pathlib import Path

try:
    import colorama
    from termcolor import colored
except:
    print(
        "Error: could not import colorama and termcolor! Make sure you install ue4-docker at least once before running the test suite."
    )
    sys.exit(1)


class UERelease:
    def __init__(
        self, name: str, tag: str, repo: str, vsVersion: int, ubuntuVersion: str
    ) -> None:
        self.name = name
        self.tag = tag
        self.repo = repo
        self.vsVersion = vsVersion
        self.ubuntuVersion = ubuntuVersion


# Older releases have broken tags in the upstream Unreal Engine repository, so we use a fork with the updated `Commit.gitdeps.xml` files
UPSTREAM_REPO = "https://github.com/EpicGames/UnrealEngine.git"
COMMITDEPS_REPO = "https://github.com/adamrehn/UnrealEngine.git"

# The list of Unreal Engine releases that are currently supported by ue4-docker
SUPPORTED_RELEASES = [
    UERelease("4.22", "4.22.3-fixed", COMMITDEPS_REPO, 2017, None),
    UERelease("4.23", "4.23.1-fixed", COMMITDEPS_REPO, 2017, None),
    UERelease("4.24", "4.24.3-fixed", COMMITDEPS_REPO, 2017, None),
    UERelease("4.25", "4.25.4-fixed", COMMITDEPS_REPO, 2017, None),
    UERelease("4.26", "4.26.2-fixed", COMMITDEPS_REPO, 2017, None),
    UERelease("4.27", "4.27.2-fixed", COMMITDEPS_REPO, 2017, None),
    UERelease("5.0", "5.0.3-fixed", COMMITDEPS_REPO, 2019, "20.04"),
    UERelease("5.1", "5.1.1-fixed", COMMITDEPS_REPO, 2019, None),
    UERelease("5.2", "5.2.1-release", UPSTREAM_REPO, 2022, None),
    UERelease("5.3", "5.3.2-release", UPSTREAM_REPO, 2022, None),
]


# Logs a message with the specified colour, making it bold to distinguish it from `ue4-docker build` log output
def log(message: str, colour: str):
    print(colored(message, color=colour, attrs=["bold"]), file=sys.stderr, flush=True)


# Logs a command and runs it
def run(dryRun: bool, command: str, **kwargs: dict) -> subprocess.CompletedProcess:
    log(command, colour="green")
    if not dryRun:
        return subprocess.run(command, **{"check": True, **kwargs})
    else:
        return subprocess.CompletedProcess(command, 0)


# Runs our tests for the specified Unreal Engine release
def testRelease(
    release: UERelease, username: str, token: str, keepImages: bool, dryRun: bool
) -> None:

    # Pass the supplied credentials to the build process via environment variables
    environment = {
        **os.environ,
        "UE4DOCKER_USERNAME": username,
        "UE4DOCKER_PASSWORD": token,
    }

    # Generate the command to build the ue4-minimal image (and its dependencies) for the specified Unreal Engine release
    command = [
        sys.executable,
        "-m",
        "ue4docker",
        "build",
        "--ue-version",
        f"custom:{release.name}",
        "-repo",
        release.repo,
        "-branch",
        release.tag,
        "--target",
        "minimal",
    ]

    # Apply any platform-specific flags
    if platform.system() == "Windows":
        command += ["--visual-studio", release.vsVersion]
    elif release.ubuntuVersion is not None:
        command += ["-basetag", f"ubuntu{release.ubuntuVersion}"]

    # Attempt to run the build
    run(
        dryRun,
        command,
        env=environment,
    )

    # Unless requested otherwise, remove the built images to free up disk space
    if not keepImages:
        run(
            dryRun,
            [
                sys.executable,
                "-m",
                "ue4docker",
                "clean",
                "-tag",
                release.name,
                "--all",
                "--prune",
                "--dry-run",
            ],
        )


if __name__ == "__main__":

    try:
        # Initialise coloured log output under Windows
        colorama.init()

        # Resolve the paths to our input directories
        testDir = Path(__file__).parent
        credentialsDir = testDir / "credentials"
        repoRoot = testDir.parent

        # Parse our command-line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--releases",
            default=None,
            help="Run tests for the specified Unreal Engine releases (comma-delimited, defaults to all supported releases)",
        )
        parser.add_argument(
            "--keep-images",
            action="store_true",
            help="Don't remove images after they are built (uses more disk space)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print commands instead of running them",
        )
        args = parser.parse_args()

        # Parse and validate the specified list of releases
        if args.releases is not None:
            testQueue = []
            versions = args.releases.split(",")
            for version in versions:
                found = [r for r in SUPPORTED_RELEASES if r.name == version]
                if len(found) == 1:
                    testQueue.append(found[0])
                else:
                    raise RuntimeError(f'unsupported Unreal Engine release "{version}"')
        else:
            testQueue = SUPPORTED_RELEASES

        # Read the GitHub username from the credentials directory
        usernameFile = credentialsDir / "username.txt"
        if usernameFile.exists():
            username = usernameFile.read_text("utf-8").strip()
        else:
            raise RuntimeError(f"place GitHub username in the file {str(usernameFile)}")

        # Read the GitHub Personal Access Token (PAT) from the credentials directory
        tokenFile = credentialsDir / "password.txt"
        if tokenFile.exists():
            token = tokenFile.read_text("utf-8").strip()
        else:
            raise RuntimeError(
                f"place GitHub Personal Access Token (PAT) in the file {str(tokenFile)}"
            )

        # Ensure any local changes to ue4-docker are installed
        run(
            args.dry_run,
            [sys.executable, "-m", "pip", "install", "--user", str(repoRoot)],
        )

        # Run the tests for each of the selected Unreal Engine releases
        for release in testQueue:
            testRelease(release, username, token, args.keep_images, args.dry_run)

    except Exception as e:
        log(traceback.format_exc(), colour="red")
