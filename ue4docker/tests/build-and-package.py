#!/usr/bin/env python3
import os, platform, subprocess, tempfile, ue4cli


# Runs a command, raising an error if it returns a nonzero exit code
def run(command, **kwargs):
	print('[RUN COMMAND] {} {}'.format(command, kwargs), flush=True)
	return subprocess.run(command, check=True, **kwargs)


# Retrieve the short version string for the Engine
manager = ue4cli.UnrealManagerFactory.create()
version = manager.getEngineVersion('short')

# Create an auto-deleting temporary directory to work in
with tempfile.TemporaryDirectory() as tempDir:
	
	# Clone a simple C++ project and verify that we can build and package it
	repo = 'https://gitlab.com/ue4-test-projects/{}/BasicCxx.git'.format(version)
	projectDir = os.path.join(tempDir, 'BasicCxx')
	run(['git', 'clone', '--depth=1', repo, projectDir])
	run(['ue4', 'package', 'Shipping'], cwd=projectDir)
	
	# Forcibly delete the .git subdirectory under Windows to avoid permissions errors when deleting the temp directory
	if platform.system() == 'Windows':
		run(['del', '/f', '/s', '/q', os.path.join(projectDir, '.git')], shell=True)
