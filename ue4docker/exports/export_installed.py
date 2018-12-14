from ..infrastructure import DockerUtils, PackageUtils, SubprocessUtils
import os, platform, subprocess, sys

# Import the `semver` package even when the conflicting `node-semver` package is present
semver = PackageUtils.importFile('semver', os.path.join(PackageUtils.getPackageLocation('semver'), 'semver.py'))

def exportInstalledBuild(tag, destination, extraArgs):
	
	# Verify that we are running under Linux
	if platform.system() != 'Linux':
		print('Error: Installed Builds can only be exported under Linux.', file=sys.stderr)
		sys.exit(1)
	
	# Verify that the Installed Build in the specified image is at least 4.21.0
	image = 'adamrehn/ue4-full:{}'.format(tag)
	versionResult = SubprocessUtils.capture(['docker', 'run', '--rm', '-ti', image, 'ue4', 'version'])
	try:
		version = semver.parse(SubprocessUtils.extractLines(versionResult.stdout)[-1])
		if version['minor'] < 21:
			raise Exception()
	except:
		print('Error: Installed Builds can only be exported for Unreal Engine 4.21.0 and newer.', file=sys.stderr)
		sys.exit(1)
	
	# Start a container from which we will copy files
	container = DockerUtils.start(image, 'bash')
	
	# Attempt to perform the export
	print('Exporting to {}...'.format(destination))
	containerPath = '{}:/home/ue4/UnrealEngine'.format(container.name)
	exportResult = subprocess.call(['docker', 'cp', containerPath, destination])
	
	# Stop the container, irrespective of whether or not the export succeeded
	container.stop()
	
	# Determine if the export succeeded
	if exportResult != 0:
		print('Error: failed to export Installed Build.', file=sys.stderr)
		sys.exit(1)
