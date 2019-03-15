import logging, multiprocessing, os, platform, secrets, time, urllib.parse
from .NetworkUtils import NetworkUtils
from flask import Flask, request

class CredentialEndpoint(object):
	
	def __init__(self, username, password):
		'''
		Creates an endpoint manager for the supplied credentials
		'''
		self.username = username
		self.password = password
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
		self.endpoint = multiprocessing.Process(
			target = CredentialEndpoint._endpoint,
			args=(self.username, self.password, self.token)
		)
		self.endpoint.start()
		time.sleep(2)
	
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
