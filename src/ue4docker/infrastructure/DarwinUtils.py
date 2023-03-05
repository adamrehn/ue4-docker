import platform

from packaging.version import Version


class DarwinUtils(object):
    @staticmethod
    def minimumRequiredVersion() -> Version:
        """
        Returns the minimum required version of macOS, which is 10.10.3 Yosemite

        (10.10.3 is the minimum required version for Docker for Mac, as per:
        <https://store.docker.com/editions/community/docker-ce-desktop-mac>)
        """
        return Version("10.10.3")

    @staticmethod
    def systemString():
        """
        Generates a human-readable version string for the macOS host system
        """
        return "macOS {} (Kernel Version {})".format(
            platform.mac_ver()[0], platform.uname().release
        )

    @staticmethod
    def getMacOsVersion() -> Version:
        """
        Returns the version number for the macOS host system
        """
        return Version(platform.mac_ver()[0])

    @staticmethod
    def isSupportedMacOsVersion():
        """
        Verifies that the macOS host system meets our minimum version requirements
        """
        return DarwinUtils.getMacOsVersion() >= DarwinUtils.minimumRequiredVersion()
