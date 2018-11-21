#!/usr/bin/env python3
from os.path import basename, dirname, join, relpath
import glob, shutil, sys

# Determine the root directory for the source build and the Installed Build
sourceRoot = sys.argv[1]
installedRoot = join(sourceRoot, 'LocalBuilds', 'Engine', 'Linux')

# Locate the bundled toolchain and copy it to the Installed Build
sdkGlob = join(sourceRoot, 'Engine', 'Extras', 'ThirdPartyNotUE', 'SDKs', 'HostLinux', 'Linux_x64', '*', 'x86_64-unknown-linux-gnu')
for bundled in glob.glob(sdkGlob):
	
	# Extract the root path for the toolchain
	toolchain = dirname(bundled)
	
	# Print progress output
	print('Copying bundled toolchain "{}" to Installed Build...'.format(basename(toolchain)), file=sys.stderr)
	sys.stderr.flush()
	
	# Perform the copy
	dest = join(installedRoot, relpath(toolchain, sourceRoot))
	shutil.copytree(toolchain, dest)
