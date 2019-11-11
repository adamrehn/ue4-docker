#!/usr/bin/env python3
import os, re, sys

def readFile(filename):
	with open(filename, 'rb') as f:
		return f.read().decode('utf-8')

def writeFile(filename, data):
	with open(filename, 'wb') as f:
		f.write(data.encode('utf-8'))

# Ensure the `PlatformType` field is set correctly for Client and Server targets in BaseEngine.ini
iniFile = sys.argv[1]
config = readFile(iniFile)
config = re.sub('PlatformType="Game", RequiredFile="(.+UE4(Client|Server).*\\.target)"', 'PlatformType="\\2", RequiredFile="\\1"', config)
writeFile(iniFile, config)
