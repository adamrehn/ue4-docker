---
title:  Troubleshooting build issues
pagenum: 3
---

## General issues

### Building the `ue4-build-prerequisites` image fails with a network-related error

This indicates an underlying network or proxy server issue outside of ue4-docker itself that you will need to troubleshoot. You can use the [ue4-docker diagnostics](../commands/diagnostics) command to test container network connectivity during the troubleshooting process. Here are some steps to try:

- If your host system accesses the network through a proxy server, make sure that [Docker is configured to use the correct proxy server settings](https://docs.docker.com/network/proxy/).
- If DNS resolution is failing then try adding the following entry to your [Docker daemon configuration file](https://docs.docker.com/engine/reference/commandline/dockerd/#daemon-configuration-file) (accessed through the Docker Engine settings pane if you're using Docker Desktop) and restarting the daemon:
  
```json
"dns": ["8.8.8.8"]
```


### Cloning the UnrealEngine Git repository fails with the message `error: unable to read askpass response from 'C:\git-credential-helper.bat'` (for Windows containers) or `'/tmp/git-credential-helper.sh'` (for Linux containers)

This typically indicates that the firewall on the host system is blocking connections from the Docker container, preventing it from retrieving the Git credentials supplied by the build command. This is particularly noticeable under a clean installation of Windows Server, which blocks connections from other subnets by default. The firewall will need to be configured appropriately to allow the connection, or else temporarily disabled. (Under Windows Server, the [ue4-docker setup](../commands/setup) command can configure the firewall rule for you automatically.)


### Building the Derived Data Cache (DDC) for the Installed Build of the Engine fails with a message about failed shader compilation or being unable to open a `.uasset` file

This is typically caused by insufficient available disk space. To fix this, simply free up some disk space and run the build again. Running [docker system prune](https://docs.docker.com/engine/reference/commandline/system_prune/) can be helpful for freeing up space occupied by untagged images. Note that restarting the Docker daemon and/or rebooting the host system may also help, since some versions of Docker have a bug that results in the amount of required disk space slowly increasing as more and more builds are run.


### Building Windows containers fails with the message `hcsshim::ImportLayer failed in Win32: The system cannot find the path specified` or building Linux containers fails with a message about insufficient disk space

Assuming you haven't actually run out of disk space, this means that the maximum Docker image size has not been configured correctly.

- For Windows containers, follow [the instructions provided by Microsoft](https://docs.microsoft.com/en-us/visualstudio/install/build-tools-container#step-4-expand-maximum-container-disk-size), making sure you restart the Docker daemon after you've modified the config JSON. (Under Windows Server, the [ue4-docker setup](../commands/setup) command can configure this for you automatically.)
- For Linux containers, use the [Docker for Windows "Advanced" settings tab](https://docs.docker.com/docker-for-windows/#advanced) under Windows or the [Docker for Mac "Disk" settings tab](https://docs.docker.com/docker-for-mac/#disk) under macOS.


### Building the `ue4-minimal` image fails on the `COPY --from=builder` directive that copies the Installed Build from the intermediate image into the final image

{% capture _alert_content %}
Modern versions of Docker Desktop for Windows and Docker EE for Windows Server suffer from issues with 8GiB filesystem layers, albeit due to different underlying bugs. Since ue4-docker version 0.0.47, you can use the [ue4-docker diagnostics](../commands/diagnostics) command to check whether the Docker daemon on your system suffers from this issue. If it does, you may need to [exclude debug symbols](./advanced-build-options#excluding-engine-components-to-reduce-the-final-image-size) when building Windows images.
{% endcapture %}
{% include alerts/warning.html content=_alert_content %}

Some versions of Docker contain one or more of a series of separate but related bugs that prevent the creation of filesystem layers which are 8GiB in size or larger:

- <https://github.com/moby/moby/issues/37581> (affects all platforms)
- <https://github.com/moby/moby/issues/40444> (affects Windows containers only)

[#37581](https://github.com/moby/moby/issues/37581) was [fixed](https://github.com/moby/moby/pull/37771) in Docker CE 18.09.0, whilst [#40444](https://github.com/moby/moby/issues/40444) was [fixed](https://github.com/moby/moby/pull/41430) in Docker CE 20.10.0.

If you are using a version of Docker that contains one of these bugs then you will need to [exclude debug symbols](./advanced-build-options#excluding-engine-components-to-reduce-the-final-image-size), which reduces the size of the Installed Build below the 8GiB threshold. If debug symbols are required then it will be necessary to upgrade or downgrade to a version of Docker that does not suffer from the 8GiB size limit issue (although finding such a version under Windows may prove quite difficult.)


## Linux-specific issues

### Building the Engine in a Linux container fails with an error indicating that a compatible version of clang cannot be found or the file `ToolchainVersion.txt` is missing

This is typically caused by the download of the Unreal Engine's toolchain archive from the Epic Games CDN becoming corrupted and failing to extract correctly. This issue can occur both inside containers and when running directly on a host system, and the fix is to simply delete the corrupted files and try again:

1. Untag the [ue4-source](./available-container-images#ue4-source) image.
2. Clear the Docker filesystem layer cache by running [docker system prune](https://docs.docker.com/engine/reference/commandline/system_prune/).
3. Re-run the [ue4-docker build](../commands/build) command.


## Windows-specific issues


### Building the `ue4-build-prerequisites` image fails with an unknown error

Microsoft issued a security update in February 2020 that [broke container compatibility for all versions of Windows Server and caused 32-bit applications to fail silently when run](https://support.microsoft.com/en-us/help/4542617/you-might-encounter-issues-when-using-windows-server-containers-with-t). The issue is resolved by ensuring that both the host system and the container image are using versions of Windows that incorporate the fix:

- Make sure your host system is up-to-date and all available Windows updates are installed.
- Make sure you are using the latest version of ue4-docker, which automatically uses container images that incorporate the fix.


### Building Windows containers fails with the message `hcsshim: timeout waiting for notification extra info` or the message `This operation ended because the timeout has expired`

Recent versions of Docker under Windows may sometimes encounter the error [hcsshim: timeout waiting for notification extra info](https://github.com/Microsoft/hcsshim/issues/152) when building or running Windows containers. This is a known issue when using Windows containers in [Hyper-V isolation mode](https://docs.microsoft.com/en-us/virtualization/windowscontainers/manage-containers/hyperv-container). At the time of writing, Microsoft have stated that they are aware of the problem, but an official fix is yet to be released.

As a workaround until a proper fix is issued, it seems that altering the memory limit for containers between subsequent invocations of the `docker` command can reduce the frequency with which this error occurs. (Changing the memory limit when using Hyper-V isolation likely forces Docker to provision a new Hyper-V VM, preventing it from re-using an existing one that has become unresponsive.) Please note that this workaround has been devised based on my own testing under Windows 10 and may not hold true when using Hyper-V isolation under Windows Server.

To enable the workaround, specify the `--random-memory` flag when invoking the build command. This will set the container memory limit to a random value between 10GB and 12GB when the build command starts. If a build fails with the `hcsshim` timeout error, simply re-run the build command and in most cases the build will continue successfully, even if only for a short while. Restarting the Docker daemon may also help.

Note that some older versions of UnrealBuildTool will crash with an error stating *"The process cannot access the file because it is being used by another process"* when using a memory limit that is not a multiple of 4GB. If this happens, simply run the build command again with an appropriate memory limit (e.g. `-m 8GB` or `-m 12GB`.) If the access error occurs even when using an appropriate memory limit, this likely indicates that Windows is unable to allocate the full amount of memory to the container. Rebooting the host system may help to alleviate this issue.


### Building or running Windows containers fails with the message `The operating system of the container does not match the operating system of the host`

This error is shown in two situations:

- The host system is running an **older kernel version** than the container image. In this case, you will need to build the images using the same kernel version as the host system or older. See [Specifying the Windows Server Core base image tag](./advanced-build-options#specifying-the-windows-server-core-base-image-tag) for details on specifying the correct kernel version when building Windows container images.
- The host system is running a **newer kernel version** than the container image and you are attempting to use process isolation mode instead of Hyper-V isolation mode. (Process isolation mode is the default under Windows Server.) In this case, you will need to use Hyper-V isolation mode instead. See [Specifying the isolation mode under Windows](./advanced-build-options#specifying-the-isolation-mode-under-windows) for details on how to do this.


### Pulling the .NET Framework base image fails with the message `ProcessUtilityVMImage \\?\`(long path here)`\UtilityVM: The system cannot find the path specified`

This is a known issue when the host system is running an older kernel version than the container image. Just like in the case of the *"The operating system of the container does not match the operating system of the host"* error mentioned above, you will need to build the images using the same kernel version as the host system or older. See [Specifying the Windows Server Core base image tag](./advanced-build-options#specifying-the-windows-server-core-base-image-tag) for details on specifying the correct kernel version when building Windows container images.


### Building the Engine in a Windows container fails with the message `The process cannot access the file because it is being used by another process`

This is a known bug in some older versions of UnrealBuildTool when using a memory limit that is not a multiple of 4GB. To alleviate this issue, specify an appropriate memory limit override (e.g. `-m 8GB` or `-m 12GB`.) For more details on this issue, see the last paragraph of the [`hcsshim` timeout issues](#building-windows-containers-fails-with-the-message-hcsshim-timeout-waiting-for-notification-extra-info-or-the-message-this-operation-ended-because-the-timeout-has-expired) section.


### Building the Engine in a Windows container fails with the message `fatal error LNK1318: Unexpected PDB error; OK (0)`

This is a known bug in some versions of Visual Studio which only appears to occur intermittently. The simplest fix is to simply reboot the host system and then re-run the build command. Insufficient available memory may also contribute to triggering this bug. Note that a linker wrapper [was added in Unreal Engine 4.24.0](https://docs.unrealengine.com/en-US/Support/Builds/ReleaseNotes/4_24/index.html) to automatically retry link operations in the event that this bug occurs, so it shouldn't be an issue when building version 4.24.0 or newer.


### Building the Engine in a Windows container fails with the message `fatal error C1060: the compiler is out of heap space`

This error typically occurs when the Windows pagefile size is not large enough. As stated in the [Windows containers primer](../read-these-first/windows-container-primer#hyper-v-isolation-mode-issues), there is currently no exposed mechanism to control the pagefile size for containers running in Hyper-V isolation mode. However, containers running in process isolation mode will use the pagefile settings of the host system. When using process isolation mode, this error can be resolved by increasing the pagefile size on the host system. (Note that the host system will usually need to be rebooted for the updated pagefile settings to take effect.)


### Building an Unreal project in a Windows container fails when the project files are located in a directory that is bind-mounted from the host operating system

As described in the [Windows containers primer](../read-these-first/windows-container-primer#hyper-v-isolation-mode-issues), the paths associated with Windows bind-mounted directories inside Hyper-V isolation mode VMs can cause issues for certain build tools, including UnrealBuildTool and CMake. As a result, building Unreal projects located in Windows bind-mounted directories is not advised when using Hyper-V isolation mode. The solution is to copy the Unreal project to a temporary directory within the container's filesystem and build it there, copying any produced build artifacts back to the host system via the bind-mounted directory as necessary.
