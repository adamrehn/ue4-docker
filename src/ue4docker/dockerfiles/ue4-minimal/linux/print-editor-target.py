#!/usr/bin/env python3
from pathlib import Path
import json, sys

# Parse the Unreal Engine version information
engineRoot = Path(sys.argv[1])
versionFile = engineRoot / "Engine" / "Build" / "Build.version"
versionDetails = json.loads(versionFile.read_text("utf-8"))

# Determine the name of the Editor target based on the version
target = "UE4Editor" if versionDetails["MajorVersion"] == 4 else "UnrealEditor"
print(target)
