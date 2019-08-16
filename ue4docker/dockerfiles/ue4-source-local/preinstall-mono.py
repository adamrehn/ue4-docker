#!/usr/bin/env python3
import json, os, subprocess, sys

def readFile(filename):
	with open(filename, 'rb') as f:
		return f.read().decode('utf-8')

# Determine if we are building UE 4.19
versionDetails = json.loads(readFile('/home/ue4/UnrealEngine/Engine/Build/Build.version'))
if versionDetails['MinorVersion'] == 19:
	
	# Our required packages, extracted from Setup.sh
	packages = [
		'mono-xbuild',
		'mono-dmcs',
		'libmono-microsoft-build-tasks-v4.0-4.0-cil',
		'libmono-system-data-datasetextensions4.0-cil',
		'libmono-system-web-extensions4.0-cil',
		'libmono-system-management4.0-cil',
		'libmono-system-xml-linq4.0-cil',
		'libmono-corlib4.5-cil',
		'libmono-windowsbase4.0-cil',
		'libmono-system-io-compression4.0-cil',
		'libmono-system-io-compression-filesystem4.0-cil',
		'libmono-system-runtime4.0-cil',
		'mono-devel'
	]
	
	# Preinstall the packages
	result = subprocess.call(['apt-get', 'install', '-y'] + packages)
	if result != 0:
		sys.exit(result)
	
	# Add the package installation commands to root_commands.sh
	# (This ensures the packages will subsequently be installed by the ue4-minimal image)
	with open('/home/ue4/UnrealEngine/root_commands.sh', 'a') as script:
		for package in packages:
			script.write('apt-get install -y {}\n'.format(package))
