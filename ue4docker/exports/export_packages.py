import docker, os, subprocess, sys, tempfile
from ..infrastructure import DockerUtils

# Our conan_server config file data
CONAN_SERVER_CONFIG = '''
[server]
jwt_secret: {jwt_secret}
jwt_expire_minutes: 120
ssl_enabled: False
port: 9300
public_port:
host_name: 127.0.0.1
authorize_timeout: 1800
disk_storage_path: ~/.conan_server/data
disk_authorize_timeout: 1800
updown_secret: {updown_secret}

[write_permissions]
*/*@*/*: *

[read_permissions]
*/*@*/*: *

[users]
user: password
'''

def _writeFile(filename, data):
	with open(filename, 'wb') as f:
		f.write(data.encode('utf-8'))

def _extractLines(output):
	return output.decode('utf-8').replace('\r\n', '\n').strip().split('\n')

def _capture(command, check = True, **kwargs):
	return subprocess.run(
		command,
		stdout = subprocess.PIPE,
		stderr = subprocess.PIPE,
		check = check,
		**kwargs
	)

def _run(command, check = True, **kwargs):
	return _capture(command, check, **kwargs)

def _exec(container, command, **kwargs):
	result, output = container.exec_run(command, **kwargs)
	if result is not None and result != 0:
		container.stop()
		raise RuntimeError(
			'Failed to run command {} in container. Process returned exit code {} with output: {}'.format(
				command,
				result,
				output
			)
		)

def _execMultiple(container, commands, **kwargs):
	for command in commands:
		_exec(container, command, **kwargs)

def exportPackages(tag, destination, extraArgs):
	
	# Verify that the destination is "cache"
	if destination.lower() != 'cache':
		print('Error: the only supported package export destination is "cache".')
		sys.exit(1)
	
	# Verify that Conan is installed on the host
	try:
		_run(['conan', '--version'])
	except:
		print('Error: Conan must be installed on the host system to export packages.')
		sys.exit(1)
	
	# Determine if the container image is a Windows image or a Linux image
	image = 'adamrehn/ue4-full:{}'.format(tag)
	imageOS = DockerUtils.listImages(image)[0].attrs['Os']
	
	# Use the appropriate commands and paths for the container platform
	cmdsAndPaths = {
		
		'linux': {
			'rootCommand': ['bash', '-c', 'sleep infinity'],
			'copyCommand': ['cp', '-f'],
			
			'configDir': '/home/ue4/.conan_server/',
			'bindMount': '/hostdir/'
		},
		
		'windows': {
			'rootCommand': ['timeout', '/t', '99999', '/nobreak'],
			'copyCommand': ['xcopy', '/y'],
			
			'configDir': 'C:\\Users\\ContainerAdministrator\\.conan_server\\',
			'bindMount': 'C:\\hostdir\\'
		}
		
	}[imageOS]
	
	# Create an auto-deleting temporary directory to hold our server config file
	with tempfile.TemporaryDirectory() as tempDir:
		
		# Generate our server config file in the temp directory
		_writeFile(os.path.join(tempDir, 'server.conf'), CONAN_SERVER_CONFIG)
		
		# Progress output
		print('Starting conan_server in a container...')
		
		# Start a container from which we will export packages, bind-mounting our temp directory
		container = DockerUtils.start(
			image,
			cmdsAndPaths['rootCommand'],
			ports = {'9300/tcp': 9300},
			mounts = [docker.types.Mount(cmdsAndPaths['bindMount'], tempDir, 'bind')]
		)
		
		try:
			
			# Copy the server config file to the expected location inside the container
			_execMultiple(container, [
				['mkdir', cmdsAndPaths['configDir']],
				cmdsAndPaths['copyCommand'] + [cmdsAndPaths['bindMount'] + 'server.conf', cmdsAndPaths['configDir'] + 'server.conf']
			])
			
			# Start `conan_server`
			_exec(container, ['conan_server'], detach = True)
			
			# Progress output
			print('Uploading packages to the server...')
			
			# Upload all of the packages in the container's local cache to the server
			_execMultiple(container, [
				['conan', 'remote', 'add', 'localhost', 'http://127.0.0.1:9300'],
				['conan', 'user', 'user', '-r', 'localhost', '-p', 'password'],
				['conan', 'upload', '*/4.*', '--all', '--confirm', '-r=localhost']
			])
			
			# Configure the server as a temporary remote on the host system
			remoteName = '_ue4docker_export_temp'
			_run(['conan', 'remote', 'add', remoteName, 'http://127.0.0.1:9300'])
			_run(['conan', 'user', 'user', '-r', remoteName, '-p', 'password'])
			
			# Retrieve the list of packages that were uploaded to the server
			packages = _extractLines(_capture(['conan', 'search', '-r', remoteName, '*']).stdout)
			packages = [package for package in packages if '/' in package and '@' in package]
			
			# Download each package in turn
			for package in packages:
				print('Downloading package {} to host system local cache...'.format(package))
				_run(['conan', 'download', '-r', remoteName, '-re', package])
			
		finally:
			
			# Remove the temporary remote if it was created successfully
			_run(['conan', 'remote', 'remove', remoteName], check = False)
			
			# Stop the container, irrespective of whether or not the export succeeded
			print('Stopping conan_server...')
			container.stop()
