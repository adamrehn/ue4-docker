#!/usr/bin/env python3
import os, re, sys

def readFile(filename):
	with open(filename, 'rb') as f:
		return f.read().decode('utf-8')

def writeFile(filename, data):
	with open(filename, 'wb') as f:
		f.write(data.encode('utf-8'))

# Extract all commands requiring `sudo` in Setup.sh and place them in root_commands.sh
setupScript = sys.argv[1]
code = readFile(setupScript)
code = re.sub('(\\s)sudo ([^\\n]+)\\n', '\\1echo \\2 >> /home/ue4/UnrealEngine/root_commands.sh\\n', code)
writeFile(setupScript, code)

# Print the patched code to stderr for debug purposes
print('PATCHED {}:\n\n{}'.format(setupScript, code), file=sys.stderr)
