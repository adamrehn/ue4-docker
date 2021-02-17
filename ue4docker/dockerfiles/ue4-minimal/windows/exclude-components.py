#!/usr/bin/env python3
import glob, json, os, shutil, sys
from os.path import join

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
version = json.loads(readFile(join(rootDir, 'Engine', 'Build', 'Build.version')))

# Determine if we are excluding debug symbols
truncateDebug = len(sys.argv) > 2 and sys.argv[2] == '1'
if truncateDebug == True:
	
	# Truncate all PDB files to save space whilst avoiding the issues that would be caused by the files being missing
	log('User opted to exclude debug symbols, truncating all PDB files.')
	log('Scanning for PDB files in directory {}...'.format(rootDir))
	pdbFiles = glob.glob(join(rootDir, '**', '*.pdb'), recursive=True)
	for pdbFile in pdbFiles:
		log('Truncating PDB file {}...'.format(pdbFile))
		try:
			os.truncate(pdbFile, 0)
		except:
			log('  Warning: failed to truncate PDB file {}.'.format(pdbFile))

# Determine if we are excluding the Engine's template projects and samples
excludeTemplates = len(sys.argv) > 3 and sys.argv[3] == '1'
if excludeTemplates == True:
	log('User opted to exclude templates and samples.')
	for subdir in ['FeaturePacks', 'Samples', 'Templates']:
		log('Removing {} directory...'.format(subdir))
		try:
			shutil.rmtree(join(rootDir, subdir))
		except:
			log('  Warning: failed to remove {} directory...'.format(subdir))
