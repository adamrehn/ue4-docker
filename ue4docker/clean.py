import argparse, subprocess, sys
from .infrastructure import *

def _isIntermediateImage(image):
	sentinel = 'com.adamrehn.ue4-docker.sentinel'
	labels = image.attrs['ContainerConfig']['Labels']
	return labels is not None and sentinel in labels

def _cleanMatching(cleaner, filter, tag, dryRun):
	tagSuffix = ':{}'.format(tag) if tag is not None else '*'
	matching = DockerUtils.listImages(tagFilter = filter + tagSuffix)
	cleaner.cleanMultiple([image.tags[0] for image in matching], dryRun)

def clean():
	
	# Create our logger to generate coloured output on stderr
	logger = Logger(prefix='[{} clean] '.format(sys.argv[0]))
	
	# Our supported command-line arguments
	parser = argparse.ArgumentParser(
		prog='{} clean'.format(sys.argv[0]),
		description =
			'Cleans built container images. ' + 
			'By default, only dangling intermediate images leftover from ue4-docker multi-stage builds are removed.'
	)
	parser.add_argument('-tag', default=None, help='Only clean images with the specified tag')
	parser.add_argument('--source', action='store_true', help='Clean ue4-source images')
	parser.add_argument('--engine', action='store_true', help='Clean ue4-engine images')
	parser.add_argument('--all', action='store_true', help='Clean all ue4-docker images')
	parser.add_argument('--dry-run', action='store_true', help='Print docker commands instead of running them')
	parser.add_argument('--prune', action='store_true', help='Run `docker system prune` after cleaning')
	
	# Parse the supplied command-line arguments
	args = parser.parse_args()
	
	# Create our image cleaner
	cleaner = ImageCleaner(logger)
	
	# Remove any intermediate images leftover from our multi-stage builds
	dangling = DockerUtils.listImages(filters = {'dangling': True})
	dangling = [image.id for image in dangling if _isIntermediateImage(image)]
	cleaner.cleanMultiple(dangling, args.dry_run)
	
	# If requested, remove ue4-source images
	if args.source == True:
		_cleanMatching(cleaner, GlobalConfiguration.resolveTag('ue4-source'), args.tag, args.dry_run)
		
	# If requested, remove ue4-engine images
	if args.engine == True:
		_cleanMatching(cleaner, GlobalConfiguration.resolveTag('ue4-engine'), args.tag, args.dry_run)
	
	# If requested, remove everything
	if args.all == True:
		_cleanMatching(cleaner, GlobalConfiguration.resolveTag('ue4-*'), args.tag, args.dry_run)
	
	# If requested, run `docker system prune`
	if args.prune == True:
		logger.action('Running `docker system prune`...')
		pruneCommand = ['docker', 'system', 'prune', '-f']
		if args.dry_run == True:
			print(pruneCommand)
		else:
			subprocess.call(pruneCommand)
