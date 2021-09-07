from .DockerUtils import DockerUtils
from pkg_resources import parse_version
import platform, sys
from typing import Optional

if platform.system() == "Windows":
    import winreg


class WindowsUtils(object):

    # The oldest Windows build we support
    _minimumRequiredBuild = 17763

    # This lookup table is based on the list of valid tags from <https://hub.docker.com/r/microsoft/windowsservercore/>
    # and list of build-to-release mapping from https://docs.microsoft.com/en-us/windows/release-health/release-information
    _knownTagsByBuildNumber = {
        17763: "ltsc2019",
        18362: "1903",
        18363: "1909",
        19041: "2004",
        19042: "20H2",
        19043: "21H1",
        20348: "ltsc2022",
    }

    _knownTags = list(_knownTagsByBuildNumber.values())

    # The list of Windows Server and Windows 10 host OS releases that are blacklisted due to critical bugs
    # (See: <https://unrealcontainers.com/docs/concepts/windows-containers>)
    _blacklistedHosts = [18362, 18363]

    @staticmethod
    def _getVersionRegKey(subkey: str) -> str:
        """
        Retrieves the specified Windows version key from the registry

        @raises FileNotFoundError if registry key doesn't exist
        """
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion"
        )
        value = winreg.QueryValueEx(key, subkey)
        winreg.CloseKey(key)
        return value[0]

    @staticmethod
    def requiredSizeLimit() -> float:
        """
        Returns the minimum required image size limit (in GB) for Windows containers
        """
        return 400.0

    @staticmethod
    def minimumRequiredBuild() -> int:
        """
        Returns the minimum required version of Windows 10 / Windows Server
        """
        return WindowsUtils._minimumRequiredBuild

    @staticmethod
    def systemString() -> str:
        """
        Generates a verbose human-readable version string for the Windows host system
        """
        return "{} (Build {}.{})".format(
            WindowsUtils._getVersionRegKey("ProductName"),
            WindowsUtils.getWindowsBuild(),
            WindowsUtils._getVersionRegKey("UBR"),
        )

    @staticmethod
    def getHostBaseTag() -> Optional[str]:
        """
        Retrieves the tag for the Windows Server Core base image matching the host Windows system
        """

        hostBuild = WindowsUtils.getWindowsBuild()

        return WindowsUtils._knownTagsByBuildNumber.get(hostBuild)

    @staticmethod
    def getWindowsBuild() -> int:
        """
        Returns build number for the Windows host system
        """
        return sys.getwindowsversion().build

    @staticmethod
    def isBlacklistedWindowsHost() -> bool:
        """
        Determines if host Windows version is one with bugs that make it unsuitable for use
        (defaults to checking the host OS release if one is not specified)
        """
        dockerVersion = parse_version(DockerUtils.version()["Version"])
        build = WindowsUtils.getWindowsBuild()
        return (
            build in WindowsUtils._blacklistedHosts
            and dockerVersion < parse_version("19.03.6")
        )

    @staticmethod
    def isWindowsServer() -> bool:
        """
        Determines if the Windows host system is Windows Server
        """
        # TODO: Replace this with something more reliable
        return "Windows Server" in WindowsUtils._getVersionRegKey("ProductName")

    @staticmethod
    def getDllSrcImage(basetag: str) -> str:
        """
        Returns Windows image that can be used as a source for DLLs missing from Windows Server Core base image
        """
        # TODO: we also need to use Windows Server image when user specifies custom tags, like '10.0.20348.169'
        image = {
            "ltsc2022": "mcr.microsoft.com/windows/server",
        }.get(basetag, "mcr.microsoft.com/windows")

        tag = {
            "ltsc2019": "1809",
        }.get(basetag, basetag)

        return f"{image}:{tag}"

    @staticmethod
    def getKnownBaseTags() -> [str]:
        """
        Returns the list of known tags for the Windows Server Core base image, in ascending chronological release order
        """
        return WindowsUtils._knownTags

    @staticmethod
    def isNewerBaseTag(older: str, newer: str) -> Optional[bool]:
        """
        Determines if the base tag `newer` is chronologically newer than the base tag `older`
        """
        try:
            return WindowsUtils._knownTags.index(newer) > WindowsUtils._knownTags.index(
                older
            )
        except ValueError:
            return None
