import docker, os, platform, requests, shutil, subprocess, sys
from .infrastructure import *

# Runs a command without displaying its output and returns the exit code
def _runSilent(command):
	result = SubprocessUtils.capture(command, check=False)
	return result.returncode

# Performs setup for Linux hosts
def _setupLinux():
	
	# Pull the latest version of the Alpine container image
	alpineImage = 'alpine:latest'
	SubprocessUtils.capture(['docker', 'pull', alpineImage])
	
	# Start the credential endpoint with blank credentials
	endpoint = CredentialEndpoint('', '')
	endpoint.start()
	
	try:
		
		# Run an Alpine container to see if we can access the host port for the credential endpoint
		SubprocessUtils.capture([
			'docker', 'run', '--rm', alpineImage,
			'wget', '--timeout=1', '--post-data=dummy', 'http://{}:9876'.format(NetworkUtils.hostIP())
		], check=True)
		
		# If we reach this point then the host port is accessible
		print('No firewall configuration required.')
		
	except:
		
		# The host port is blocked, so we need to perform firewall configuration
		print('Creating firewall rule for credential endpoint...')
		
		# Create the firewall rule
		subprocess.run(['iptables', '-A', 'INPUT', '-p', 'tcp', '--dport', '9876', '-j', 'ACCEPT'], check=True)
		
		# Ensure the firewall rule persists after reboot
		# (Requires the `iptables-persistent` service to be installed and running)
		os.makedirs('/etc/iptables', exist_ok=True)
		subprocess.run('iptables-save > /etc/iptables/rules.v4', shell=True, check=True)
		
		# Inform users of the `iptables-persistent` requirement
		print('Firewall rule created. Note that the `iptables-persistent` service will need to')
		print('be installed for the rule to persist after the host system reboots.')
		
	finally:
		
		# Stop the credential endpoint
		endpoint.stop()

# Performs setup for Windows Server hosts
def _setupWindowsServer():
	
	# Check if we need to configure the maximum image size
	requiredLimit = WindowsUtils.requiredSizeLimit()
	if DockerUtils.maxsize() < requiredLimit:
		
		# Attempt to stop the Docker daemon
		print('Stopping the Docker daemon...')
		subprocess.run(['sc.exe', 'stop', 'docker'], check=True)
		
		# Attempt to set the maximum image size
		print('Setting maximum image size to {}GB...'.format(requiredLimit))
		config = DockerUtils.getConfig()
		sizeOpt = 'size={}GB'.format(requiredLimit)
		if 'storage-opts' in config:
			config['storage-opts'] = list([o for o in config['storage-opts'] if o.lower().startswith('size=') == False])
			config['storage-opts'].append(sizeOpt)
		else:
			config['storage-opts'] = [sizeOpt]
		DockerUtils.setConfig(config)
		
		# Attempt to start the Docker daemon
		print('Starting the Docker daemon...')
		subprocess.run(['sc.exe', 'start', 'docker'], check=True)
		
	else:
		print('Maximum image size is already correctly configured.')
	
	# Determine if we need to configure Windows firewall
	ruleName = 'Open TCP port 9876 for ue4-docker credential endpoint'
	ruleExists = _runSilent(['netsh', 'advfirewall', 'firewall', 'show', 'rule', 'name={}'.format(ruleName)]) == 0
	if ruleExists == False:
		
		# Add a rule to ensure Windows firewall allows access to the credential helper from our containers
		print('Creating firewall rule for credential endpoint...')
		subprocess.run([
			'netsh', 'advfirewall',
			'firewall', 'add', 'rule',
			'name={}'.format(ruleName), 'dir=in', 'action=allow', 'protocol=TCP', 'localport=9876'
		], check=True)
		
	else:
		print('Firewall rule for credential endpoint is already configured.')
	
	# Determine if the host system is Windows Server Core and lacks the required DLL files for building our containers
	hostRelease = WindowsUtils.getWindowsRelease()
	requiredDLLs = WindowsUtils.requiredHostDlls(hostRelease)
	dllDir = os.path.join(os.environ['SystemRoot'], 'System32')
	existing = [dll for dll in requiredDLLs if os.path.exists(os.path.join(dllDir, dll))]
	if len(existing) != len(requiredDLLs):
		
		# Determine if we can extract DLL files from the full Windows base image (version 1809 and newer only)
		tags = requests.get('https://mcr.microsoft.com/v2/windows/tags/list').json()['tags']
		if hostRelease in tags:
			
			# Pull the full Windows base image with the appropriate tag if it does not already exist
			image = 'mcr.microsoft.com/windows:{}'.format(hostRelease)
			print('Pulling full Windows base image "{}"...'.format(image))
			subprocess.run(['docker', 'pull', image], check=True)
			
			# Start a container from which we will copy the DLL files, bind-mounting our DLL destination directory
			print('Starting a container to copy DLL files from...')
			mountPath = 'C:\\dlldir'
			container = DockerUtils.start(
				image,
				['timeout', '/t', '99999', '/nobreak'],
				mounts = [docker.types.Mount(mountPath, dllDir, 'bind')],
				stdin_open = True,
				tty = True,
				remove = True
			)
			
			# Copy the DLL files to the host
			print('Copying DLL files to the host system...')
			DockerUtils.execMultiple(container, [['xcopy', '/y', os.path.join(dllDir, dll), mountPath + '\\'] for dll in requiredDLLs])
			
			# Stop the container
			print('Stopping the container...')
			container.stop()
			
		else:
			print('The following DLL files will need to be manually copied into {}:'.format(dllDir))
			print('\n'.join(['- {}'.format(dll) for dll in requiredDLLs if dll not in existing]))
		
	else:
		print('All required DLL files are already present on the host system.')

def setup():
	
	# We don't currently support auto-config for VM-based containers
	if platform.system() == 'Darwin' or (platform.system() == 'Windows' and WindowsUtils.isWindowsServer() == False):
		print('Manual configuration is required under Windows 10 and macOS. Automatic configuration is not available.')
		return
	
	# Perform setup based on the host system type
	if platform.system() == 'Linux':
		_setupLinux()
	else:
		_setupWindowsServer()
