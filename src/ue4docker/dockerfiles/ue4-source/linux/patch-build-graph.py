#!/usr/bin/env python3
import json, os, sys


def readFile(filename):
    with open(filename, "rb") as f:
        return f.read().decode("utf-8")


def writeFile(filename, data):
    with open(filename, "wb") as f:
        f.write(data.encode("utf-8"))


# Read the build graph XML
buildXml = sys.argv[1]
code = readFile(buildXml)

# Read the UE4 version information
versionFile = sys.argv[2]
versionData = json.loads(readFile(versionFile))

# Disable AArch64 by default (enabled since 4.24.0)
code = code.replace(
    'Property Name="DefaultWithLinuxAArch64" Value="true"',
    'Property Name="DefaultWithLinuxAArch64" Value="false"',
)
# AArch64 was renamed to Arm64 in UE-5.0, so also disable it
code = code.replace(
    'Property Name="DefaultWithLinuxArm64" Value="true"',
    'Property Name="DefaultWithLinuxArm64" Value="false"',
)

# Write the modified XML back to disk
writeFile(buildXml, code)
