class FilesystemUtils(object):
	
	@staticmethod
	def readFile(filename):
		'''
		Reads data from a file
		'''
		with open(filename, 'rb') as f:
			return f.read().decode('utf-8')
	
	@staticmethod
	def writeFile(filename, data):
		'''
		Writes data to a file
		'''
		with open(filename, 'wb') as f:
			f.write(data.encode('utf-8'))
