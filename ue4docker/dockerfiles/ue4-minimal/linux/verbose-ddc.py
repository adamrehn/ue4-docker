#!/usr/bin/env python3
import os, sys

def readFile(filename):
	with open(filename, 'rb') as f:
		return f.read().decode('utf-8')

def writeFile(filename, data):
	with open(filename, 'wb') as f:
		f.write(data.encode('utf-8'))

# Add verbose output flags to the `BuildDerivedDataCache` command
buildXml = sys.argv[1]
code = readFile(buildXml)
code = code.replace(
	'Command Name="BuildDerivedDataCache" Arguments="',
	'Command Name="BuildDerivedDataCache" Arguments="-Verbose -AllowStdOutLogVerbosity '
)
writeFile(buildXml, code)
