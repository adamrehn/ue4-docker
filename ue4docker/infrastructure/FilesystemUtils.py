class FilesystemUtils(object):
	
	@staticmethod
	def writeFile(filename, data):
		'''
		Writes data to a file
		'''
		with open(filename, 'wb') as f:
			f.write(data.encode('utf-8'))
