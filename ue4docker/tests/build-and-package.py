#!/usr/bin/env python3
import os, shutil, subprocess, time, ue4cli


# Runs a command, raising an error if it returns a nonzero exit code
def run(command, **kwargs):
	return subprocess.run(command, check=True, **kwargs)

# Repeatedly calls a function until it succeeds or the max number of retries has been reached
def repeat(func, maxRetries=5, sleepTime=0.5):
	for i in range(0, maxRetries):
		try:
			func()
			break
		except:
			time.sleep(sleepTime)


# Retrieve the short version string for the Engine
manager = ue4cli.UnrealManagerFactory.create()
version = manager.getEngineVersion('short')

# Clone a simple C++ project and verify that we can build and package it
repo = 'https://gitlab.com/ue4-test-projects/{}/BasicCxx.git'.format(version)
projectDir = os.path.join(os.getcwd(), 'BasicCxx')
run(['git', 'clone', '--depth=1', repo, projectDir])
run(['ue4', 'package', 'Shipping'], cwd=projectDir)

# Perform cleanup
# (This can sometimes fail arbitrarily under Windows, so retry a few times if it does)
repeat(lambda: shutil.rmtree(projectDir))
