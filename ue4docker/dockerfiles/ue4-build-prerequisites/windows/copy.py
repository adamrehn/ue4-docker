#!/usr/bin/env python3
# This script is used to avoid issues with `xcopy.exe` under Windows Server 2016 (https://github.com/moby/moby/issues/38425)
import glob, os, shutil, sys

# If the destination is an existing directory then expand wildcards in the source
destination = sys.argv[2]
if os.path.isdir(destination) == True:
	sources = glob.glob(sys.argv[1])
else:
	sources = [sys.argv[1]]

# Copy each of our source files/directories
for source in sources:
	if os.path.isdir(source):
		dest = os.path.join(destination, os.path.basename(source))
		shutil.copytree(source, dest)
	else:
		shutil.copy2(source, destination)
	print('Copied {} to {}.'.format(source, destination), file=sys.stderr)
