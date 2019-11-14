import logging, multiprocessing, os, platform, secrets, time, urllib.parse
from .NetworkUtils import NetworkUtils
from flask import Flask, request

class CredentialEndpoint(object):
	
	def __init__(self, username, password):
		'''
		Creates an endpoint manager for the supplied credentials
		'''
		
		# Make sure neither our username or password are blank, since that can cause `git clone` to hang indefinitely
		self.username = username if username is not None and len(username) > 0 else ' '
		self.password = password if password is not None and len(password) > 0 else ' '
		self.endpoint = None
		
		# Generate a security token to require when requesting credentials 
		self.token = secrets.token_hex(16)
	
	def args(self):
		'''
		Returns the Docker build arguments for creating containers that require Git credentials
		'''
		
		# Resolve the IP address for the host system
		hostAddress = NetworkUtils.hostIP()
		
		# Provide the host address and security token to the container
		return [
			'--build-arg', 'HOST_ADDRESS_ARG=' + urllib.parse.quote_plus(hostAddress),
			'--build-arg', 'HOST_TOKEN_ARG=' + urllib.parse.quote_plus(self.token)
		]
	
	def start(self):
		'''
		Starts the HTTP endpoint as a child process
		'''
		
		# Create a child process to run the credential endpoint
		self.endpoint = multiprocessing.Process(
			target = CredentialEndpoint._endpoint,
			args=(self.username, self.password, self.token)
		)
		
		# Spawn the child process and give the endpoint time to start
		self.endpoint.start()
		time.sleep(2)
		
		# Verify that the endpoint started correctly
		if self.endpoint.is_alive() == False:
			raise RuntimeError('failed to start the credential endpoint')
	
	def stop(self):
		'''
		Stops the HTTP endpoint child process
		'''
		self.endpoint.terminate()
		self.endpoint.join()
	
	@staticmethod
	def _endpoint(username, password, token):
		'''
		Implements a HTTP endpoint to provide Git credentials to Docker containers
		'''
		server = Flask(__name__)
		
		# Disable the first-run banner message
		os.environ['WERKZEUG_RUN_MAIN'] = 'true'
		
		# Disable Flask log output (from <https://stackoverflow.com/a/18379764>)
		log = logging.getLogger('werkzeug')
		log.setLevel(logging.ERROR)
		
		@server.route('/', methods=['POST'])
		def credentials():
			if 'token' in request.args and request.args['token'] == token:
				prompt = request.data.decode('utf-8')
				return password if "Password for" in prompt else username
			else:
				return 'Invalid security token'
		
		server.run(host='0.0.0.0', port=9876)
