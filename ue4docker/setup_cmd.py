import platform, subprocess, sys
from .infrastructure import *

# Runs a command without displaying its output and returns the exit code
def _runSilent(command):
	result = subprocess.run(command, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	return result.returncode

def setup():
	
	# Under Linux, no config changes are necessary
	if platform.system() == 'Linux':
		print('No configuration changes are needed under Linux.')
		return
	
	# We don't currently support auto-config for VM-based containers
	if platform.system() == 'Darwin' or (platform.system() == 'Windows' and WindowsUtils.isWindowsServer() == False):
		print('Manual configuration is required under Windows 10 and macOS. Automatic configuration is not available.')
		return
	
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
