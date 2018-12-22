#!/usr/bin/env python3
import glob, json, os, sys

# Logs a message to stderr
def log(message):
	print(message, file=sys.stderr)
	sys.stderr.flush()

# Reads the contents of a file
def readFile(filename):
	with open(filename, 'rb') as f:
		return f.read().decode('utf-8')

# Parse the UE4 version information
rootDir = sys.argv[1]
version = json.loads(readFile(os.path.join(rootDir, 'Engine', 'Build', 'Build.version')))

# Determine if we are preserving or truncating PDB files
keepDebug = len(sys.argv) > 2 and sys.argv[2] == '1'
if keepDebug == True:
	log('User opted to preserve debug symbols, leaving all PDB files intact.')
	sys.exit(0)

# Truncate all PDB files to save space whilst avoiding the issues that would be caused by the files being missing
log('Scanning for PDB files in directory {}...'.format(rootDir))
pdbFiles = glob.glob(os.path.join(rootDir, '**', '*.pdb'), recursive=True)
for pdbFile in pdbFiles:
	log('Truncating PDB file {}...'.format(pdbFile))
	try:
		os.truncate(pdbFile, 0)
	except:
		log('  Warning: failed to truncate PDB file {}.'.format(pdbFile))

# Under UE4.19, we need to delete the PDB files for AutomationTool entirely, since truncated files cause issues
if version['MinorVersion'] < 20:
	pdbFiles = glob.glob(os.path.join(rootDir, 'Engine', 'Source', 'Programs', 'AutomationTool', '**', '*.pdb'), recursive=True)
	for pdbFile in pdbFiles:
		log('Removing PDB file {}...'.format(pdbFile))
		try:
			os.unlink(pdbFile)
		except:
			log('  Warning: failed to remove PDB file {}.'.format(pdbFile))
