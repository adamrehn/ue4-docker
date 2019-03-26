from .main import main
import os, sys

if __name__ == '__main__':
	
	# Rewrite sys.argv[0] so our help prompts display the correct base command
	interpreter = sys.executable if sys.executable not in [None, ''] else 'python3'
	sys.argv[0] = '{} -m ue4docker'.format(os.path.basename(interpreter))
	main()
