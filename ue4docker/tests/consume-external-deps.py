#!/usr/bin/env python3
import os, platform, subprocess, tempfile, ue4cli


# Reads data from a file
def read(filename):
	with open(filename, 'rb') as f:
		return f.read().decode('utf-8')

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

# Create an auto-deleting temporary directory to work in
with tempfile.TemporaryDirectory() as tempDir:
	
	# Clone a simple C++ project
	repo = 'https://gitlab.com/ue4-test-projects/{}/BasicCxx.git'.format(version)
	projectDir = os.path.join(tempDir, 'BasicCxx')
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
	
	# Forcibly delete the .git subdirectory under Windows to avoid permissions errors when deleting the temp directory
	if platform.system() == 'Windows':
		run(['del', '/f', '/s', '/q', os.path.join(projectDir, '.git')], shell=True)
