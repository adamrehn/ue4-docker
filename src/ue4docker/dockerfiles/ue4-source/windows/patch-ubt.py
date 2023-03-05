#!/usr/bin/env python3
import os, re, sys


def readFile(filename):
    with open(filename, "rb") as f:
        return f.read().decode("utf-8")


def writeFile(filename, data):
    with open(filename, "wb") as f:
        f.write(data.encode("utf-8"))


def patchFile(filename, search, replace):
    contents = readFile(filename)
    patched = contents.replace(search, replace)
    writeFile(filename, patched)


# Apply our bugfixes to UnrealBuildTool (UBT)

# Ensure modules always have a binary output directory value set when exporting JSON
# (In some Engine versions, External modules do not have an output directory set, breaking modules that reference `$(BinaryOutputDir)`)
patchFile(
    os.path.join(sys.argv[1], "Configuration", "UEBuildTarget.cs"),
    "Module.ExportJson(Module.Binary?.OutputDir, GetExecutableDir(), Writer);",
    "Module.ExportJson((Module.Binary != null || Binaries.Count == 0) ? Module.Binary?.OutputDir : Binaries[0].OutputDir, GetExecutableDir(), Writer);",
)
