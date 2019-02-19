from ..infrastructure import DockerUtils, FilesystemUtils, Logger, SubprocessUtils
import docker, os, subprocess, sys, tempfile

# The name we use for our temporary Conan remote
REMOTE_NAME = '_ue4docker_export_temp'

# Our conan_server config file data
CONAN_SERVER_CONFIG = '''
[server]
jwt_secret: jwt_secret
jwt_expire_minutes: 120
ssl_enabled: False
port: 9300
public_port: 9300
host_name: {}
authorize_timeout: 1800
disk_storage_path: {}
disk_authorize_timeout: 1800
updown_secret: updown_secret

[write_permissions]
*/*@*/*: *

[read_permissions]
*/*@*/*: *

[users]
user: password
'''


def exportPackages(image, destination, extraArgs):
	
	# Create our logger to generate coloured output on stderr
	logger = Logger()
	
	# Verify that the destination is "cache"
	if destination.lower() != 'cache':
		logger.error('Error: the only supported package export destination is "cache".')
		sys.exit(1)
	
	# Verify that Conan is installed on the host
	try:
		SubprocessUtils.run(['conan', '--version'])
	except:
		logger.error('Error: Conan must be installed on the host system to export packages.')
		sys.exit(1)
	
	# Determine if the container image is a Windows image or a Linux image
	imageOS = DockerUtils.listImages(image)[0].attrs['Os']
	
	# Use the appropriate commands and paths for the container platform
	cmdsAndPaths = {
		
		'linux': {
			'rootCommand':  ['bash', '-c', 'sleep infinity'],
			'mkdirCommand': ['mkdir'],
			'copyCommand':  ['cp', '-f'],
			
			'dataDir':   '/home/ue4/.conan_server/data',
			'configDir': '/home/ue4/.conan_server/',
			'bindMount': '/hostdir/'
		},
		
		'windows': {
			'rootCommand':  ['timeout', '/t', '99999', '/nobreak'],
			'mkdirCommand': ['cmd', '/S', '/C', 'mkdir'],
			'copyCommand':  ['python', 'C:\\copy.py'],
			
			'dataDir':   'C:\\Users\\ContainerAdministrator\\.conan_server\\data',
			'configDir': 'C:\\Users\\ContainerAdministrator\\.conan_server\\',
			'bindMount': 'C:\\hostdir\\'
		}
		
	}[imageOS]
	
	# Create an auto-deleting temporary directory to hold our server config file
	with tempfile.TemporaryDirectory() as tempDir:
		
		# Progress output
		print('Starting conan_server in a container...')
		
		# Start a container from which we will export packages, bind-mounting our temp directory
		container = DockerUtils.start(
			image,
			cmdsAndPaths['rootCommand'],
			ports = {'9300/tcp': 9300},
			mounts = [docker.types.Mount(cmdsAndPaths['bindMount'], tempDir, 'bind')],
			stdin_open = imageOS == 'windows',
			tty = imageOS == 'windows',
			remove = True
		)
		
		# Reload the container attributes from the Docker daemon to ensure the networking fields are populated
		container.reload()
		
		# Under Linux we can simply access the container from the host over the loopback address, but this doesn't work under Windows
		# (See <https://blog.sixeyed.com/published-ports-on-windows-containers-dont-do-loopback/>)
		externalAddress = '127.0.0.1' if imageOS == 'linux' else container.attrs['NetworkSettings']['Networks']['nat']['IPAddress']
		
		# Generate our server config file in the temp directory
		FilesystemUtils.writeFile(os.path.join(tempDir, 'server.conf'), CONAN_SERVER_CONFIG.format(externalAddress, cmdsAndPaths['dataDir']))
		
		# Keep track of the `conan_server` log output so we can display it in case of an error
		serverOutput = None
		
		try:
			
			# Copy the server config file to the expected location inside the container
			DockerUtils.execMultiple(container, [
				cmdsAndPaths['mkdirCommand'] + [cmdsAndPaths['configDir']],
				cmdsAndPaths['copyCommand'] + [cmdsAndPaths['bindMount'] + 'server.conf', cmdsAndPaths['configDir']]
			])
			
			# Start `conan_server`
			serverOutput = DockerUtils.exec(container, ['conan_server'], stream = True)
			
			# Progress output
			print('Uploading packages to the server...')
			
			# Upload all of the packages in the container's local cache to the server
			DockerUtils.execMultiple(container, [
				['conan', 'remote', 'add', 'localhost', 'http://127.0.0.1:9300'],
				['conan', 'user', 'user', '-r', 'localhost', '-p', 'password'],
				['conan', 'upload', '*/4.*', '--all', '--confirm', '-r=localhost']
			])
			
			# Configure the server as a temporary remote on the host system
			SubprocessUtils.run(['conan', 'remote', 'add', REMOTE_NAME, 'http://{}:9300'.format(externalAddress)])
			SubprocessUtils.run(['conan', 'user', 'user', '-r', REMOTE_NAME, '-p', 'password'])
			
			# Retrieve the list of packages that were uploaded to the server
			packages = SubprocessUtils.extractLines(SubprocessUtils.capture(['conan', 'search', '-r', REMOTE_NAME, '*']).stdout)
			packages = [package for package in packages if '/' in package and '@' in package]
			
			# Download each package in turn
			for package in packages:
				print('Downloading package {} to host system local cache...'.format(package))
				SubprocessUtils.run(['conan', 'download', '-r', REMOTE_NAME, package])
			
			# Once we reach this point, everything has worked and we don't need to output any logs
			serverOutput = None
			
		finally:
			
			# Stop the container, irrespective of whether or not the export succeeded
			print('Stopping conan_server...')
			container.stop()
			
			# If something went wrong then output the logs from `conan_server` to assist in diagnosing the failure
			if serverOutput is not None:
				print('Log output from conan_server:')
				for chunk in serverOutput:
					logger.error(chunk.decode('utf-8'))
			
			# Remove the temporary remote if it was created successfully
			SubprocessUtils.run(['conan', 'remote', 'remove', REMOTE_NAME], check = False)
