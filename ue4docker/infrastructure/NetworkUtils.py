import socket

class NetworkUtils(object):
	
	@staticmethod
	def hostIP():
		'''
		Determines the IP address of the host
		'''
		# Code from <https://stackoverflow.com/a/28950776>
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		try:
			s.connect(('10.255.255.255', 1))
			IP = s.getsockname()[0]
		except:
			IP = '127.0.0.1'
		finally:
			s.close()
		return IP
