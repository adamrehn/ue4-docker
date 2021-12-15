#!/usr/bin/env python3
from os.path import dirname
from subprocess import run, PIPE
import json, re, sys


def readFile(filename):
    with open(filename, "rb") as f:
        return f.read().decode("utf-8")


def writeFile(filename, data):
    with open(filename, "wb") as f:
        f.write(data.encode("utf-8"))


# Determine whether a changelist override value was specified
changelistOverride = None
if len(sys.argv) > 2 and sys.argv[2] != "%CHANGELIST%":

    # If the override was "auto" then attempt to retrieve the CL number from the git commit message
    if sys.argv[2] == "auto":

        # Retrieve the commit message from git
        engineRoot = dirname(dirname(dirname(sys.argv[1])))
        commitMessage = run(
            ["git", "log", "-n", "1", "--format=%s%n%b"],
            cwd=engineRoot,
            stdout=PIPE,
            stderr=PIPE,
            universal_newlines=True,
        ).stdout.strip()

        # If the commit is a tagged engine release then it won't have a CL number, and using "auto" is user error
        if re.fullmatch("[0-9\\.]+ release", commitMessage) is not None:
            print(
                "Error: you are attempting to automatically retrieve the CL number for a tagged Unreal Engine release.\n"
                "For hotfix releases of the Unreal Engine, a CL override is not required and should not be specified.\n"
                "For supported .0 releases of the Unreal Engine, ue4-docker ships with known CL numbers, so an override should not be necessary.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Attempt to extract the CL number from the commit message
        match = re.search("\\[CL ([0-9]+) by .+ in .+ branch\\]", commitMessage)
        if match is not None:
            changelistOverride = int(match.group(1))
        else:
            print(
                "Error: failed to find a CL number in the git commit message! This was the commit message:\n\n"
                + commitMessage,
                file=sys.stderr,
            )
            sys.exit(1)

    else:
        changelistOverride = int(sys.argv[2])

# Update the `Changelist` field to reflect the override if it was supplied, or else the `CompatibleChangelist` field in our version file
versionFile = sys.argv[1]
details = json.loads(readFile(versionFile))
details["Changelist"] = (
    changelistOverride
    if changelistOverride is not None
    else details["CompatibleChangelist"]
)
details["IsPromotedBuild"] = 1
patchedJson = json.dumps(details, indent=4)
writeFile(versionFile, patchedJson)
print("PATCHED BUILD.VERSION:\n{}".format(patchedJson), file=sys.stderr)
