import os

from packaging.version import Version
from urllib.request import urlopen
import json

# The default namespace for our tagged container images
DEFAULT_TAG_NAMESPACE = "adamrehn"


class GlobalConfiguration(object):
    """
    Manages access to the global configuration settings for ue4-docker itself
    """

    @staticmethod
    def getLatestVersion():
        """
        Queries PyPI to determine the latest available release of ue4-docker
        """
        with urlopen("https://pypi.org/pypi/ue4-docker/json") as url:
            data = json.load(url)
            releases = [Version(release) for release in data["releases"]]
            return sorted(releases)[-1]

    @staticmethod
    def getTagNamespace():
        """
        Returns the currently-configured namespace for container image tags
        """
        return os.environ.get("UE4DOCKER_TAG_NAMESPACE", DEFAULT_TAG_NAMESPACE)

    @staticmethod
    def resolveTag(tag):
        """
        Resolves a Docker image tag with respect to our currently-configured namespace
        """

        # If the specified tag already includes a namespace, simply return it unmodified
        return (
            tag
            if "/" in tag
            else "{}/{}".format(GlobalConfiguration.getTagNamespace(), tag)
        )
