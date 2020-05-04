#!/usr/bin/env python3
import os, shutil, subprocess, ue4cli

# Runs a command, raising an error if it returns a nonzero exit code
def run(command, **kwargs):
	return subprocess.run(command, check=True, **kwargs)

# Retrieve the short version string for the Engine
manager = ue4cli.UnrealManagerFactory.create()
version = manager.getEngineVersion('short')

# Clone a simple C++ project and verify that we can build and package it
repo = 'https://gitlab.com/ue4-test-projects/{}/BasicCxx.git'.format(version)
projectDir = os.path.join(os.getcwd(), 'BasicCxx')
run(['git', 'clone', '--depth=1', repo, projectDir])
run(['ue4', 'package', 'Shipping'], cwd=projectDir)

# Perform cleanup
shutil.rmtree(projectDir)
