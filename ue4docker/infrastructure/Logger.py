from termcolor import colored
import colorama, sys

class Logger(object):
	
	def __init__(self, prefix=''):
		'''
		Creates a logger that will print coloured output to stderr
		'''
		colorama.init()
		self.prefix = prefix
	
	def action(self, output, newline=True):
		'''
		Prints information about an action that is being performed
		'''
		self._print('green', output, newline)
	
	def error(self, output, newline=False):
		'''
		Prints information about an error that has occurred
		'''
		self._print('red', output, newline)
	
	def info(self, output, newline=True):
		'''
		Prints information that does not pertain to an action or an error
		'''
		self._print('yellow', output, newline)
	
	def _print(self, colour, output, newline):
		whitespace = '\n' if newline == True else ''
		print(colored(whitespace + self.prefix + output, color=colour), file=sys.stderr)
