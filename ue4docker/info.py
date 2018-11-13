#!/usr/bin/env python3
import humanfriendly, platform, psutil, sys
from .infrastructure import *

def _osName(dockerInfo):
	if platform.system() == 'Windows':
		return dockerInfo['OperatingSystem']
	elif platform.system() == 'Darwin':
		return 'macOS'
	else:
		return 'Linux ({}, {})'.format(dockerInfo['OperatingSystem'], dockerInfo['KernelVersion'])

def info():
	
	# Verify that Docker is installed
	if DockerUtils.installed() == False:
		print('Error: could not detect Docker version. Please ensure Docker is installed.', file=sys.stderr)
		sys.exit(1)
	
	# Gather our information on the Docker daemon
	dockerInfo = DockerUtils.info()
	nvidiaDocker = platform.system() == 'Linux' and 'nvidia' in dockerInfo['Runtimes']
	maxSize = DockerUtils.maxsize()
	
	# Prepare our report items
	items = [
		('Operating system', _osName(dockerInfo)),
		('Docker daemon version', dockerInfo['ServerVersion']),
		('NVIDIA Docker supported', 'Yes' if nvidiaDocker == True else 'No'),
		('Maximum image size', '{:.0f}GB'.format(maxSize) if maxSize != -1 else 'No limit detected'),
		('Total system memory', humanfriendly.format_size(psutil.virtual_memory().total, binary=True)),
		('Number of processors', '{} physical, {} logical'.format(psutil.cpu_count(False), psutil.cpu_count()))
	]
	
	# Determine the longest item name so we can format our list in nice columns
	longestName = max([len(i[0]) for i in items])
	minSpaces = 4
	
	# Print our report
	for item in items:
		print('{}:{}{}'.format(
			item[0],
			' ' * ((longestName + minSpaces) - len(item[0])),
			item[1]
		))
