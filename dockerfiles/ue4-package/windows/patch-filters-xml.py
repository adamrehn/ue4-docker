#!/usr/bin/env python3
import os, sys

def readFile(filename):
	with open(filename, 'rb') as f:
		return f.read().decode('utf-8')

def writeFile(filename, data):
	with open(filename, 'wb') as f:
		f.write(data.encode('utf-8'))

# Remove the dependency on Linux cross-compilation debug tools introduced in UE4.20.0
filtersXml = sys.argv[1]
code = readFile(filtersXml)
code = code.replace('Engine/Binaries/Linux/dump_syms.exe', '')
code = code.replace('Engine/Binaries/Linux/BreakpadSymbolEncoder.exe', '')
writeFile(filtersXml, code)
