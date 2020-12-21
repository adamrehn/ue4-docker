#!/usr/bin/env python3
import json, os, subprocess, sys
from os.path import join

def readFile(filename):
	with open(filename, 'rb') as f:
		return f.read().decode('utf-8')

def writeFile(filename, data):
	with open(filename, 'wb') as f:
		f.write(data.encode('utf-8'))

# Determine if we are building UE 4.25.4
engineRoot = sys.argv[1]
verboseOutput = len(sys.argv) > 2 and sys.argv[2] == '1'
versionDetails = json.loads(readFile(join(engineRoot, 'Engine', 'Build', 'Build.version')))
if versionDetails['MajorVersion'] == 4 and versionDetails['MinorVersion'] == 25 and versionDetails['PatchVersion'] == 4:
	
	# If `Commit.gitdeps.xml` is missing the changes from CL 14469950 then inject them
	# (See: <https://github.com/EpicGames/UnrealEngine/commit/84e4ea3241c294c04fdf7d8fb63f99a3109c8edd>)
	gitdepsFile = join(engineRoot, 'Engine', 'Build', 'Commit.gitdeps.xml')
	gitdepsXml = readFile(gitdepsFile)
	if '<File Name="cpp.hint"' not in gitdepsXml:
		
		gitdepsXml = gitdepsXml.replace(
			'<File Name=".tgitconfig" Hash="d3d7bbcf9b2fc8b6e4f2965354a5633c4f175589" />',
			'<File Name=".tgitconfig" Hash="d3d7bbcf9b2fc8b6e4f2965354a5633c4f175589" />\n    ' +
			'<File Name="cpp.hint" Hash="7d1daec3c6218ce9f49f9be0280091b98d7168d7" />'
		)
		gitdepsXml = gitdepsXml.replace(
			'<Blob Hash="7d1492e46d159b6979f70a415727a2be7e569e21" Size="342112" PackHash="feb61b7040721b885ad85174cfc802419600bda1" PackOffset="1545471" />',
			'<Blob Hash="7d1492e46d159b6979f70a415727a2be7e569e21" Size="342112" PackHash="feb61b7040721b885ad85174cfc802419600bda1" PackOffset="1545471" />\n    ' +
			'<Blob Hash="7d1daec3c6218ce9f49f9be0280091b98d7168d7" Size="456" PackHash="33e382aea05629bd179a60cf1520f77c025ac0b3" PackOffset="8" />'
		)
		gitdepsXml = gitdepsXml.replace(
			'<Pack Hash="33d0a2949662b327b35a881192e85107ecafc8ac" Size="2097152" CompressedSize="655885" RemotePath="2369826-2acd3c361c9d4a858bd63938a2ab980e" />',
			'<Pack Hash="33d0a2949662b327b35a881192e85107ecafc8ac" Size="2097152" CompressedSize="655885" RemotePath="2369826-2acd3c361c9d4a858bd63938a2ab980e" />\n    ' +
			'<Pack Hash="33e382aea05629bd179a60cf1520f77c025ac0b3" Size="464" CompressedSize="235" RemotePath="UnrealEngine-14572338-da4318c3ab684bc48601f32f0b1b6fe3" />'
		)
		
		writeFile(gitdepsFile, gitdepsXml)
		
		if verboseOutput == True:
			print('PATCHED {}:\n\n{}'.format(gitdepsFile, gitdepsXml), file=sys.stderr)
		else:
			print('PATCHED {}'.format(gitdepsFile), file=sys.stderr)
