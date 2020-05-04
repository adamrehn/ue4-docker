#!/usr/bin/env python3
import os, shutil, subprocess, time, ue4cli


# Reads data from a file
def read(filename):
	with open(filename, 'rb') as f:
		return f.read().decode('utf-8')

# Repeatedly calls a function until it succeeds or the max number of retries has been reached
def repeat(func, maxRetries=5, sleepTime=0.5):
	for i in range(0, maxRetries):
		try:
			func()
			break
		except:
			time.sleep(sleepTime)

# Runs a command, raising an error if it returns a nonzero exit code
def run(command, **kwargs):
	print('[RUN COMMAND] {} {}'.format(command, kwargs), flush=True)
	return subprocess.run(command, check=True, **kwargs)

# Writes data to a file
def write(filename, data):
	with open(filename, 'wb') as f:
		f.write(data.encode('utf-8'))


# Retrieve the short version string for the Engine
manager = ue4cli.UnrealManagerFactory.create()
version = manager.getEngineVersion('short')

# Clone a simple C++ project
repo = 'https://gitlab.com/ue4-test-projects/{}/BasicCxx.git'.format(version)
projectDir = os.path.join(os.getcwd(), 'BasicCxx')
run(['git', 'clone', '--depth=1', repo, projectDir])

# Generate a code module to wrap our external dependencies
sourceDir = os.path.join(projectDir, 'Source')
run(['ue4', 'conan', 'boilerplate', 'WrapperModule'], cwd=sourceDir)

# Add the wrapper module as a dependency of the project's main source code module
rulesFile = os.path.join(sourceDir, 'BasicCxx', 'BasicCxx.Build.cs')
rules = read(rulesFile)
rules = rules.replace('PublicDependencyModuleNames.AddRange(new string[] {', 'PublicDependencyModuleNames.AddRange(new string[] { "WrapperModule", ')
write(rulesFile, rules)

# Add some dependencies to the module's conanfile.py
moduleDir = os.path.join(sourceDir, 'WrapperModule')
conanfile = os.path.join(moduleDir, 'conanfile.py')
deps = read(conanfile)
deps = deps.replace('pass', 'self._requireUnreal("zlib/ue4@adamrehn/{}")')
write(conanfile, deps)

# Verify that we can build the project with dynamically located dependencies
run(['ue4', 'build'], cwd=projectDir)
run(['ue4', 'clean'], cwd=projectDir)

# Verify that we can build the project with precomputed dependency data
run(['ue4', 'conan', 'precompute', 'host'], cwd=moduleDir)
run(['ue4', 'build'], cwd=projectDir)

# Perform cleanup
# (This can sometimes fail arbitrarily under Windows, so retry a few times if it does)
repeat(lambda: shutil.rmtree(projectDir))
