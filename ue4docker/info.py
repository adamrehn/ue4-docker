import humanfriendly, platform, psutil, shutil, sys
from .version import __version__
from .infrastructure import *

def _osName(dockerInfo):
	if platform.system() == 'Windows':
		return WindowsUtils.systemStringLong()
	elif platform.system() == 'Darwin':
		return DarwinUtils.systemString()
	else:
		return 'Linux ({}, {})'.format(dockerInfo['OperatingSystem'], dockerInfo['KernelVersion'])

def _formatSize(size):
	return humanfriendly.format_size(size, binary=True)

def info():
	
	# Verify that Docker is installed
	if DockerUtils.installed() == False:
		print('Error: could not detect Docker version. Please ensure Docker is installed.', file=sys.stderr)
		sys.exit(1)
	
	# Gather our information about the Docker daemon
	dockerInfo = DockerUtils.info()
	nvidiaDocker = platform.system() == 'Linux' and 'nvidia' in dockerInfo['Runtimes']
	maxSize = DockerUtils.maxsize()
	rootDir = dockerInfo['DockerRootDir']
	
	# If we are communicating with a Linux Docker daemon under Windows or macOS then we can't query the available disk space
	canQueryDisk = dockerInfo['OSType'].lower() == platform.system().lower()
	
	# Gather our information about the host system
	diskSpace = _formatSize(shutil.disk_usage(rootDir).free) if canQueryDisk == True else 'Unknown (typically means the Docker daemon is running in a Moby VM, e.g. Docker Desktop)'
	memPhysical = psutil.virtual_memory().total
	memVirtual = psutil.swap_memory().total
	cpuPhysical = psutil.cpu_count(False)
	cpuLogical = psutil.cpu_count()
	
	# Attempt to query PyPI to determine the latest version of ue4-docker
	# (We ignore any errors here to ensure the `ue4-docker info` command still works without network access)
	try:
		latestVersion = GlobalConfiguration.getLatestVersion()
	except:
		latestVersion = None
	
	# Prepare our report items
	items = [
		('ue4-docker version', '{}{}'.format(__version__, '' if latestVersion is None else ' (latest available version is {})'.format(latestVersion))),
		('Operating system', _osName(dockerInfo)),
		('Docker daemon version', dockerInfo['ServerVersion']),
		('NVIDIA Docker supported', 'Yes' if nvidiaDocker == True else 'No'),
		('Maximum image size', '{:.0f}GB'.format(maxSize) if maxSize != -1 else 'No limit detected'),
		('Available disk space', diskSpace),
		('Total system memory', '{} physical, {} virtual'.format(_formatSize(memPhysical), _formatSize(memVirtual))),
		('Number of processors', '{} physical, {} logical'.format(cpuPhysical, cpuLogical))
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
