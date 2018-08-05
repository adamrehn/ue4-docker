#!/usr/bin/env python3
import glob, os, shutil, sys, ue4cli

# Retrieve the source and destination directories from our command-line arguments
sourceDir = sys.argv[1]
destDir = sys.argv[2]

# Query ue4cli for the UE4 version string
ue4 = ue4cli.UnrealManagerFactory.create()
versionMinor = int(ue4.getEngineVersion('minor'))

# We only need to copy SDL2 for 4.20.0 and newer
if versionMinor < 20:
	print('Detected UE4 version {}, skipping copy of SDL2 files.'.format(ue4.getEngineVersion()), file=sys.stderr)
else:
	print('Copying files from {} to {}...'.format(sourceDir, destDir), file=sys.stderr)
	shutil.rmtree(destDir)
	shutil.copytree(sourceDir, destDir)
	for file in glob.glob(os.path.join(destDir, '*')):
		print(os.path.basename(file), file=sys.stderr)
