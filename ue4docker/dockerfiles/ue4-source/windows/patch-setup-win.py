#!/usr/bin/env python3
import os, sys

def readFile(filename):
	with open(filename, 'rb') as f:
		return f.read().decode('utf-8')

def writeFile(filename, data):
	with open(filename, 'wb') as f:
		f.write(data.encode('utf-8'))

# Comment out the call to the UE4 prereqs installer in Setup.bat
PREREQ_CALL = 'start /wait Engine\\Extras\\Redist\\en-us\\UE4PrereqSetup_x64.exe'
setupScript = sys.argv[1]
verboseOutput = len(sys.argv) > 2 and sys.argv[2] == '1'
code = readFile(setupScript)
code = code.replace('echo Installing prerequisites...', 'echo (Skipping installation of prerequisites)')
code = code.replace(PREREQ_CALL, '@rem ' + PREREQ_CALL)

# Also comment out the version selector call, since we don't need shell integration
SELECTOR_CALL = '.\\Engine\\Binaries\\Win64\\UnrealVersionSelector-Win64-Shipping.exe /register'
code = code.replace(SELECTOR_CALL, '@rem ' + SELECTOR_CALL)

# Add output so we can see when script execution is complete, and ensure `pause` is not called on error
code = code.replace('rem Done!', 'echo Done!\r\nexit /b 0')
code = code.replace('pause', '@rem pause')
writeFile(setupScript, code)

# Print the patched code to stderr for debug purposes
if verboseOutput == True:
	print('PATCHED {}:\n\n{}'.format(setupScript, code), file=sys.stderr)
else:
	print('PATCHED {}'.format(setupScript), file=sys.stderr)
