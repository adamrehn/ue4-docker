#!/usr/bin/env python3
import json, os, subprocess, sys

def readFile(filename):
	with open(filename, 'rb') as f:
		return f.read().decode('utf-8')

# Parse the UE4 version information
version = json.loads(readFile('C:\\UnrealEngine\\Engine\\Build\\Build.version'))

# UE4.19 has problems detecting the VS2017 Build Tools and doesn't use the Windows 10 SDK
# by default, so we need to install the VS2015 Build Tools and the Windows 8.1 SDK
if version['MinorVersion'] < 20:
	print('Installing VS2015 Build Tools and Windows 8.1 SDK for UE4.19 compatibility...')
	sys.stdout.flush()
	run = lambda cmd: subprocess.run(cmd, check=True)
	installerFile = '{}\\vs_buildtools.exe'.format(os.environ['TEMP'])
	run(['curl', '--progress', '-L', 'https://aka.ms/vs/16/release/vs_buildtools.exe', '--output', installerFile])
	run([
		installerFile,
		'--quiet', '--wait', '--norestart', '--nocache',
		'--installPath', 'C:\BuildTools',
		'--channelUri', 'https://aka.ms/vs/15/release/channel',
		'--installChannelUri', 'https://aka.ms/vs/15/release/channel',
		'--channelId', 'VisualStudio.15.Release',
		'--productId', 'Microsoft.VisualStudio.Product.BuildTools',
		'--add', 'Microsoft.VisualStudio.Component.VC.140',
		'--add', 'Microsoft.VisualStudio.ComponentGroup.NativeDesktop.Win81'
	])
