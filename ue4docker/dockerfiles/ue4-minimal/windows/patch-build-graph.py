#!/usr/bin/env python3
import os, sys

def readFile(filename):
	with open(filename, 'rb') as f:
		return f.read().decode('utf-8')

def writeFile(filename, data):
	with open(filename, 'wb') as f:
		f.write(data.encode('utf-8'))

# Prevent HoloLens support from being enabled by default under Windows in 4.23.0 onwards
buildXml = sys.argv[1]
code = readFile(buildXml)
code = code.replace(
	'Option Name="WithHoloLens" Restrict="true|false" DefaultValue="$(DefaultWithWindows)"',
	'Option Name="WithHoloLens" Restrict="true|false" DefaultValue="false"'
)
writeFile(buildXml, code)
