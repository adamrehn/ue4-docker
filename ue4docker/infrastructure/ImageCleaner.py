from .DockerUtils import DockerUtils
import humanfriendly, os, subprocess, time

class ImageCleaner(object):
	
	def __init__(self, logger):
		self.logger = logger
	
	def clean(self, image, dryRun=False):
		'''
		Removes the specified image
		'''
		
		# Determine if we are running in "dry run" mode
		self.logger.action('Removing image "{}"...'.format(image))
		cleanCommand = ['docker', 'rmi', image]
		if dryRun == True:
			print(cleanCommand)
		else:
			subprocess.call(cleanCommand)
	
	def cleanMultiple(self, images, dryRun=False):
		'''
		Removes all of the images in the supplied list
		'''
		for image in images:
			self.clean(image, dryRun)
