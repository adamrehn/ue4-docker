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
	
	# Remove all *.debug and *.sym files
	log('User opted to exclude debug symbols, removing all *.debug and *.sym files.')
	log('Scanning for debug symbols in directory {}...'.format(rootDir))
	symbolFiles = glob.glob(join(rootDir, '**', '*.debug'), recursive=True) + glob.glob(join(rootDir, '**', '*.sym'), recursive=True)
	for symbolFile in symbolFiles:
		log('Removing debug symbol file {}...'.format(symbolFile))
		try:
			os.unlink(symbolFile, 0)
		except:
			log('  Warning: failed to remove debug symbol file {}.'.format(symbolFile))

# Determine if we are excluding the Engine's template projects and samples
excludeTemplates = len(sys.argv) > 3 and sys.argv[3] == '1'
if excludeTemplates == True:
	log('User opted to exclude templates and samples.')
	for subdir in ['FeaturePacks', 'Samples', 'Templates']:
		log('Removing {} directory...'.format(subdir))
		try:
			shutil.rmtree(join(rootDir, currDir))
		except:
			log('  Warning: failed to remove {} directory...'.format(subdir))
