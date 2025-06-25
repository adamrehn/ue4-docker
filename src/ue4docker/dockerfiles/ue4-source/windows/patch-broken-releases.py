#!/usr/bin/env python3
import json
import sys
from os.path import join


def readFile(filename):
    with open(filename, "rb") as f:
        return f.read().decode("utf-8")


def writeFile(filename, data):
    with open(filename, "wb") as f:
        f.write(data.encode("utf-8"))


engineRoot = sys.argv[1]
verboseOutput = len(sys.argv) > 2 and sys.argv[2] == "1"
versionDetails = json.loads(
    readFile(join(engineRoot, "Engine", "Build", "Build.version"))
)

if (
    versionDetails["MajorVersion"] == 5
    and versionDetails["MinorVersion"] == 1
    and versionDetails["PatchVersion"] == 0
):
    # Hack InstalledEngineFilters.xml with the changes from CL 23300641
    # (See: <https://github.com/EpicGames/UnrealEngine/commit/ae9de79b7012fc33df355c8dbfe5096b94545e3c>)
    buildFile = join(engineRoot, "Engine", "Build", "InstalledEngineFilters.xml")
    buildXml = readFile(buildFile)
    if "HoloLens.Automation.json" not in buildXml:
        buildXml = buildXml.replace(
            '<Property Name="CopyWin64CsToolsExceptions">',
            '<Property Name="CopyWin64CsToolsExceptions">\n'
            + "            Engine\\Saved\\CsTools\\Engine\\Intermediate\\ScriptModules\\HoloLens.Automation.json\n",
        )

        writeFile(buildFile, buildXml)

        if verboseOutput:
            print("PATCHED {}:\n\n{}".format(buildFile, buildFile), file=sys.stderr)
        else:
            print("PATCHED {}".format(buildFile), file=sys.stderr)
