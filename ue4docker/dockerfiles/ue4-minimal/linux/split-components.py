#!/usr/bin/env python3
import glob, os, shutil, sys
from os.path import basename, dirname, exists, join

# Logs a message to stderr
def log(message):
    print(message, file=sys.stderr)
    sys.stderr.flush()


# Extracts the files and directories for the specified component and moves them to a separate output directory
def extractComponent(inputDir, outputDir, component, description, items):

    # Print progress output
    log("\nExtracting {}...".format(description))

    # Create the output directory for the component if it doesn't already exist
    componentDir = join(outputDir, component)
    os.makedirs(outputDir, exist_ok=True)

    # Move each file and directory for the component to the output directory
    for item in items:

        # Verify that the item exists
        if not exists(item):
            log("Skipping non-existent item: {}".format(item))
            continue

        # Print progress output
        log("Moving: {}".format(item))

        # Ensure the parent directory for the item exists in the output directory
        parent = dirname(item).replace(inputDir, componentDir)
        os.makedirs(parent, exist_ok=True)

        # Perform the move
        shutil.move(item, join(parent, basename(item)))


# Retrieve the path to the root directory of the Installed Build
rootDir = sys.argv[1]

# Retrieve the path to the root output directory for extracted components and ensure it exists
outputDir = sys.argv[2]
os.makedirs(outputDir, exist_ok=True)

# Extract the DDC
ddc = [join(rootDir, "Engine", "DerivedDataCache", "Compressed.ddp")]
extractComponent(rootDir, outputDir, "DDC", "Derived Data Cache (DDC)", ddc)

# Extract debug symbols
symbolFiles = glob.glob(join(rootDir, "**", "*.debug"), recursive=True) + glob.glob(
    join(rootDir, "**", "*.sym"), recursive=True
)
extractComponent(rootDir, outputDir, "DebugSymbols", "debug symbols", symbolFiles)

# Extract template projects and samples
subdirs = [join(rootDir, subdir) for subdir in ["FeaturePacks", "Samples", "Templates"]]
extractComponent(
    rootDir, outputDir, "TemplatesAndSamples", "template projects and samples", subdirs
)
