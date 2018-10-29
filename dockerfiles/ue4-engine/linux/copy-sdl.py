#!/usr/bin/env python3
import glob, os, shutil, sys

# Retrieve the source and destination directories from our command-line arguments
sourceDir = sys.argv[1]
destDir = sys.argv[2]

# Copy the SDL files
print('Copying files from {} to {}...'.format(sourceDir, destDir), file=sys.stderr)
shutil.rmtree(destDir)
shutil.copytree(sourceDir, destDir)
for file in glob.glob(os.path.join(destDir, '*')):
	print(os.path.basename(file), file=sys.stderr)
