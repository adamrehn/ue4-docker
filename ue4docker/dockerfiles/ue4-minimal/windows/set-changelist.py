#!/usr/bin/env python3
import json, os, sys


def readFile(filename):
    with open(filename, "rb") as f:
        return f.read().decode("utf-8")


def writeFile(filename, data):
    with open(filename, "wb") as f:
        f.write(data.encode("utf-8"))


# Update the `Changelist` field to reflect the `CompatibleChangelist` field in our version file
versionFile = sys.argv[1]
details = json.loads(readFile(versionFile))
details["Changelist"] = details["CompatibleChangelist"]
details["IsPromotedBuild"] = 1
writeFile(versionFile, json.dumps(details, indent=4))
