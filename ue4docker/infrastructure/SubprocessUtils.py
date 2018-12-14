import subprocess


class VerboseCalledProcessError(RuntimeError):
	''''
	A verbose wrapper for `subprocess.CalledProcessError` that prints stdout and stderr
	'''
	
	def __init__(self, wrapped):
		self.wrapped = wrapped
	
	def __str__(self):
		return '{}\nstdout: {}\nstderr: {}'.format(
			self.wrapped,
			self.wrapped.output,
			self.wrapped.stderr
		)


class SubprocessUtils(object):
	
	@staticmethod
	def extractLines(output):
		'''
		Extracts the individual lines from the output of a child process
		'''
		return output.decode('utf-8').replace('\r\n', '\n').strip().split('\n')
	
	@staticmethod
	def capture(command, check = True, **kwargs):
		'''
		Executes a child process and captures its output.
		
		If the child process fails and `check` is True then a verbose exception will be raised.
		'''
		try:
			return subprocess.run(
				command,
				stdout = subprocess.PIPE,
				stderr = subprocess.PIPE,
				check = check,
				**kwargs
			)
		except subprocess.CalledProcessError as e:
			raise VerboseCalledProcessError(e) from None
	
	@staticmethod
	def run(command, check = True, **kwargs):
		'''
		Executes a child process.
		
		If the child process fails and `check` is True then a verbose exception will be raised.
		'''
		return SubprocessUtils.capture(command, check, **kwargs)
