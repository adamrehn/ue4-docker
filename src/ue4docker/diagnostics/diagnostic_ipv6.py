from .base import DiagnosticBase


class diagnosticIPv6(DiagnosticBase):
    # The tag we use for built images
    IMAGE_TAG = "adamrehn/ue4-docker/diagnostics:ipv6"

    def __init__(self):
        pass

    def getName(self):
        """
        Returns the human-readable name of the diagnostic
        """
        return "Check that Linux containers can access the IPv6 loopback address"

    def getDescription(self):
        """
        Returns a description of what the diagnostic does
        """
        return "\n".join(
            [
                "This diagnostic determines whether Linux containers are able to access the IPv6,",
                "loopback address ::1, which is required by Unreal Engine 5.4 and newer for",
                "local ZenServer communication.",
                "",
                "This should work automatically under Docker 26.0.0 and newer, but older versions",
                "require manual configuration by the user.",
            ]
        )

    def getPrefix(self):
        """
        Returns the short name of the diagnostic for use in log output
        """
        return "ipv6"

    def run(self, logger, args=[]):
        """
        Runs the diagnostic
        """

        # This diagnostic only applies to Linux containers
        containerPlatform = "linux"

        # Verify that the user isn't trying to test Linux containers under Windows 10 when in Windows container mode
        try:
            self._checkPlatformMistmatch(logger, containerPlatform, False)
        except RuntimeError:
            return False

        # Attempt to build the Dockerfile
        logger.action(
            "[network] Attempting to build an image that accesses the IPv6 loopback address...",
            False,
        )
        built = self._buildDockerfile(
            logger, containerPlatform, diagnosticIPv6.IMAGE_TAG, []
        )

        # Inform the user of the outcome of the diagnostic
        if built == True:
            logger.action(
                "[network] Diagnostic succeeded! Linux containers can access the IPv6 loopback address without any issues.\n"
            )
        else:
            logger.error(
                "[network] Diagnostic failed! Linux containers cannot access the IPv6 loopback address. Update to Docker 26.0.0+ or manually enable IPv6:",
                True,
            )
            logger.error(
                "[network] https://docs.docker.com/config/daemon/ipv6/#use-ipv6-for-the-default-bridge-network\n",
                False,
            )

        return built
