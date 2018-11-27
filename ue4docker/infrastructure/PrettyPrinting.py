class PrettyPrinting(object):
	
	@staticmethod
	def printColumns(pairs, indent = 2, minSpaces = 6):
		'''
		Prints a list of paired values in two nicely aligned columns
		'''
		
		# Determine the length of the longest item in the left-hand column
		longestName = max([len(pair[0]) for pair in pairs])
		
		# Print the two columns
		for pair in pairs:
			whitespace = ' ' * ((longestName + minSpaces) - len(pair[0]))
			print('{}{}{}{}'.format(' ' * indent, pair[0], whitespace, pair[1]))
