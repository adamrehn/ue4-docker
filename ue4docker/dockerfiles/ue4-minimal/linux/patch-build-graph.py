#!/usr/bin/env python3
import os, sys

def readFile(filename):
	with open(filename, 'rb') as f:
		return f.read().decode('utf-8')

def writeFile(filename, data):
	with open(filename, 'wb') as f:
		f.write(data.encode('utf-8'))

# Read the build graph XML
buildXml = sys.argv[1]
code = readFile(buildXml)

# Add verbose output flags to the `BuildDerivedDataCache` command
code = code.replace(
	'Command Name="BuildDerivedDataCache" Arguments="',
	'Command Name="BuildDerivedDataCache" Arguments="-Verbose -AllowStdOutLogVerbosity '
)

# Enable client and server targets by default in 4.23.0 onwards
code = code.replace(
	'Option Name="WithClient" Restrict="true|false" DefaultValue="false"',
	'Option Name="WithClient" Restrict="true|false" DefaultValue="true"'
)
code = code.replace(
	'Option Name="WithServer" Restrict="true|false" DefaultValue="false"',
	'Option Name="WithServer" Restrict="true|false" DefaultValue="true"'
)

# Write the modified XML back to disk
writeFile(buildXml, code)
