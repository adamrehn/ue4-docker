#!/usr/bin/env python3
import json
import sys
from os.path import join
import os
import requests


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

major = versionDetails["MajorVersion"]
minor = versionDetails["MinorVersion"]
patch = versionDetails["PatchVersion"]

if major == 5 and minor == 0 and patch == 0:
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

if major < 5 or (major == 5 and minor < 2):
    gitdepsFile = join(engineRoot, "Engine", "Build", "Commit.gitdeps.xml")
    # See https://forums.unrealengine.com/t/upcoming-disruption-of-service-impacting-unreal-engine-users-on-github/1155880
    # In May 2023, Epics broke Commit.gitdeps.xml for *all existing releases up to 5.1.1* due to changes in their CDN
    # we need to authenticate
    password = os.getenv("GITPASS")
    #  eg curl -L \
    #          -H "Accept: application/vnd.github+json" \
    #          -H "Authorization: Bearer ghp_secretGoesHere" \
    #          -H "X-GitHub-Api-Version: 2022-11-28" \
    #          https://api.github.com/repos/EpicGames/UnrealEngine/releases/tags/4.27.2-release
    gitdepsUrl = f"https://api.github.com/repos/EpicGames/UnrealEngine/releases/tags/{major}.{minor}.{patch}-release"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + password.strip(),
        "X-GitHub-Api-Version": "2022-11-28",
    }
    with requests.get(gitdepsUrl, headers=headers) as response:
        assets = response.json()["assets"]
        if len(assets) == 1:
            gitdepsUrl = assets[0]["url"]

    # eg gitdepsUrl = f"https://api.github.com/repos/EpicGames/UnrealEngine/releases/assets/107274338"
    headers["Accept"] = "application/octet-stream"
    with requests.get(gitdepsUrl, headers=headers) as response:
        gitdepsXml = response.text.replace("&", "&amp;")
        writeFile(gitdepsFile, gitdepsXml)

        if verboseOutput:
            print("PATCHED {}:\n\n{}".format(gitdepsFile, gitdepsXml), file=sys.stderr)
        else:
            print("PATCHED {}".format(gitdepsFile), file=sys.stderr)
