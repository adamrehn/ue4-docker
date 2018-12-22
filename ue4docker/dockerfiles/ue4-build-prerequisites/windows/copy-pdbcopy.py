#!/usr/bin/env python3
import os, shutil

# Copy pdbcopy.exe to the expected location for both newer Engine versions, 
# as well as UE4 versions prior to the UE-51362 fix (https://issues.unrealengine.com/issue/UE-51362)
pdbcopyExe = 'C:\\Windows\\System32\\pdbcopy.exe'
destDirTemplate = 'C:\\Program Files (x86)\\MSBuild\\Microsoft\\VisualStudio\\v{}\\AppxPackage'
destDirs = [
	'C:\\Program Files (x86)\\Windows Kits\\10\\Debuggers\\x64',
	destDirTemplate.format('12.0'),
	destDirTemplate.format('14.0')
]
for destDir in destDirs:
	destFile = os.path.join(destDir, 'pdbcopy.exe')
	os.makedirs(destDir, exist_ok=True)
	shutil.copy2(pdbcopyExe, destFile)
