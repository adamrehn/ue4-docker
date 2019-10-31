#!/usr/bin/env python3
import os, sys

def readFile(filename):
	with open(filename, 'rb') as f:
		return f.read().decode('utf-8')

def writeFile(filename, data):
	with open(filename, 'wb') as f:
		f.write(data.encode('utf-8'))

# Enable the OpenGL RHI for Engine versions where it is present but deprecated
iniFile = sys.argv[1]
config = readFile(iniFile)
config = config.replace(
	'; +TargetedRHIs=GLSL_430',
	'+TargetedRHIs=GLSL_430'
)
writeFile(iniFile, config)
