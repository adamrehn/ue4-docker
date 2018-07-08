import importlib.util, pkg_resources

class PackageUtils(object):
	
	@staticmethod
	def getPackageLocation(package):
		'''
		Attempts to retrieve the filesystem location for the specified Python package
		'''
		return pkg_resources.get_distribution(package).location
	
	@staticmethod
	def importFile(moduleName, filePath):
		'''
		Directly imports a Python module from a source file
		'''
		spec = importlib.util.spec_from_file_location(moduleName, filePath)
		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		return module
