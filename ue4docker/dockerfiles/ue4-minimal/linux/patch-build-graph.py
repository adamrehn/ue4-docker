#!/usr/bin/env python3
import json, os, sys

def readFile(filename):
	with open(filename, 'rb') as f:
		return f.read().decode('utf-8')

def writeFile(filename, data):
	with open(filename, 'wb') as f:
		f.write(data.encode('utf-8'))

# Read the build graph XML
buildXml = sys.argv[1]
code = readFile(buildXml)

# Read the UE4 version information
versionFile = sys.argv[2]
versionData = json.loads(readFile(versionFile))

# Add verbose output flags to the `BuildDerivedDataCache` command
code = code.replace(
	'Command Name="BuildDerivedDataCache" Arguments="',
	'Command Name="BuildDerivedDataCache" Arguments="-Verbose -AllowStdOutLogVerbosity '
)

# Disable building for AArch64 by default (enabled by default since 4.24.0)
code = code.replace(
	'Property Name="DefaultWithLinuxAArch64" Value="true"',
	'Property Name="DefaultWithLinuxAArch64" Value="false"'
)

# Enable client and server targets by default in 4.23.0 onwards, except for 4.24.0 - 4.24.2 where Linux server builds fail
# (See <https://issues.unrealengine.com/issue/UE-87878> for details of the bug and its fix)
if versionData['MinorVersion'] != 24 or versionData['PatchVersion'] >= 3:
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
