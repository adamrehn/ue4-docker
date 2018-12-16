#!/usr/bin/env python3
import glob, os, sys

# Logs a message to stderr
def log(message):
	print(message, file=sys.stderr)
	sys.stderr.flush()

# Determine if we are preserving or truncating PDB files
keepDebug = len(sys.argv) > 2 and sys.argv[2] == '1'
if keepDebug == True:
	log('User opted to preserve debug symbols, leaving all PDB files intact.')
	sys.exit(0)

# Truncate all PDB files to save space whilst avoiding the issues that would be caused by the files being missing
rootDir = sys.argv[1]
log('Scanning for PDB files in directory {}...'.format(rootDir))
pdbFiles = glob.glob(os.path.join(rootDir, '**', '*.pdb'), recursive=True)
for pdbFile in pdbFiles:
	log('Truncating PDB file {}...'.format(pdbFile))
	try:
		os.truncate(pdbFile, 0)
	except:
		log('  Warning: failed to truncate PDB file {}.'.format(pdbFile))
