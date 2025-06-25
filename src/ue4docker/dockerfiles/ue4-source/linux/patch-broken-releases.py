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
    and versionDetails["MinorVersion"] == 0
    and versionDetails["PatchVersion"] == 0
):
    buildFile = join(engineRoot, "Engine", "Build", "InstalledEngineFilters.xml")
    buildXml = readFile(buildFile)

    # Add missing SetupDotnet.sh in Unreal Engine 5.0.0-early-access-1
    # See https://github.com/adamrehn/ue4-docker/issues/171#issuecomment-853918412
    # and https://github.com/EpicGames/UnrealEngine/commit/a18824057e6cd490750a10b59af29ca10b3d67d9
    dotnet = "Engine/Binaries/ThirdParty/DotNet/Linux/..."
    setup_dotnet = "Engine/Build/BatchFiles/Linux/SetupDotnet.sh"
    if dotnet in buildXml and setup_dotnet not in buildXml:
        buildXml = buildXml.replace(dotnet, f"{dotnet}\n{setup_dotnet}")

    writeFile(buildFile, buildXml)

    if verboseOutput:
        print("PATCHED {}:\n\n{}".format(buildFile, buildXml), file=sys.stderr)
    else:
        print("PATCHED {}".format(buildFile), file=sys.stderr)
