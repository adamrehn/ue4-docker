#!/usr/bin/env python3
import json, sys


def readFile(filename):
    with open(filename, "rb") as f:
        return f.read().decode("utf-8")


def writeFile(filename, data):
    with open(filename, "wb") as f:
        f.write(data.encode("utf-8"))


# Update the `Changelist` field to reflect the `CompatibleChangelist` field in our version file, unless a specific value was provided
versionFile = sys.argv[1]
changelistOverride = int(sys.argv[2]) if len(sys.argv) > 2 else None
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
