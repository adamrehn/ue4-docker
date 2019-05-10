from pkg_resources import parse_version
import os, requests


# The default namespace for our tagged container images
DEFAULT_TAG_NAMESPACE = 'adamrehn'


class GlobalConfiguration(object):
	'''
	Manages access to the global configuration settings for ue4-docker itself
	'''
	
	@staticmethod
	def getLatestVersion():
		'''
		Queries PyPI to determine the latest available release of ue4-docker
		'''
		releases = [parse_version(release) for release in requests.get('https://pypi.org/pypi/ue4-docker/json').json()['releases']]
		return sorted(releases)[-1]
	
	@staticmethod
	def getTagNamespace():
		'''
		Returns the currently-configured namespace for container image tags
		'''
		return os.environ.get('UE4DOCKER_TAG_NAMESPACE', DEFAULT_TAG_NAMESPACE)
	
	@staticmethod
	def resolveTag(tag):
		'''
		Resolves a Docker image tag with respect to our currently-configured namespace
		'''
		
		# If the specified tag already includes a namespace, simply return it unmodified
		return tag if '/' in tag else '{}/{}'.format(GlobalConfiguration.getTagNamespace(), tag)
