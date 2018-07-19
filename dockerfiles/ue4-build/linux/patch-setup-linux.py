#!/usr/bin/env python3
import os, sys

def readFile(filename):
	with open(filename, 'rb') as f:
		return f.read().decode('utf-8')

def writeFile(filename, data):
	with open(filename, 'wb') as f:
		f.write(data.encode('utf-8'))

# Patch out all instances of `sudo` in Setup.sh
setupScript = sys.argv[1]
code = readFile(setupScript)
code = code.replace('sudo ', '')
code = code.replace('./UnrealVersionSelector-Linux-Shipping -register', 'echo "Skipping registration when running as root."')
writeFile(setupScript, code)

# Print the patched code to stderr for debug purposes
print('PATCHED {}:\n\n{}'.format(setupScript, code), file=sys.stderr)
