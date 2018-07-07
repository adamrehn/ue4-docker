Dockerfiles for Unreal Engine 4
===============================

**IMPORTANT LEGAL NOTICE: the Docker images produced by the code in this repository contain the UE4 Engine Tools in both source code and object code form. As per Section 1A of the [Unreal Engine EULA](https://www.unrealengine.com/eula), Engine Licensees are prohibited from public distribution of the Engine Tools unless such distribution takes place via the Unreal Marketplace or a fork of the Epic Games UE4 GitHub repository. [Public distribution of the built images via an openly accessible Docker Registry (e.g. Docker Hub) is a direct violation of the license terms.](https://www.unrealengine.com/eula) It is your responsibility to ensure that any private distribution to other Engine Licensees (such as via an organisation's internal Docker Registry) complies with the terms of the Unreal Engine EULA.**

This repository contains a set of Dockerfiles and an accompanying Python build script that allow you to build Docker images for Epic Games' [Unreal Engine 4](https://www.unrealengine.com/). Key features include:

- The images contain a full source build of the Engine and are suitable for use in a Continuous Integration (CI) pipeline.
- **Both Windows containers and Linux containers are supported.**
- Running automation tests is supported.
- When building UE4 version 4.19.0 or newer, [conan-ue4cli](https://github.com/adamrehn/conan-ue4cli) support is also built by default, although this behaviour can be disabled by using the `--no-ue4cli` flag when invoking the build script.
- When building UE4 version 4.19.0 or newer and building the `conan-ue4cli` image, an additional image containing an [Installed Build](https://docs.unrealengine.com/en-us/Programming/Deployment/Using-an-Installed-Build) of the Engine is also created for use when packaging Shipping builds of projects, although this behaviour can be disabled by using the `--no-package` flag when invoking the build script.
- When building GPU-enabled Linux images for NVIDIA Docker and also building the `ue4-package` image, [UE4Capture](https://github.com/adamrehn/UE4Capture) support is also built by default, although this behaviour can be disabled by using the `--no-capture` flag when invoking the build script.

For a detailed discussion on how the build process works, see [the accompanying article on my website](http://adamrehn.com/articles/building-docker-images-for-unreal-engine-4).


## Contents

- [Requirements](#requirements)
- [Build script usage](#build-script-usage)
    - [Building images](#building-images)
    - [Specifying the Windows Server Core base image tag](#specifying-the-windows-server-core-base-image-tag)
    - [Specifying the isolation mode under Windows](#specifying-the-isolation-mode-under-windows)
    - [Building Linux container images under Windows](#building-linux-container-images-under-windows)
    - [Building GPU-enabled Linux container images for use with NVIDIA Docker](#building-gpu-enabled-linux-container-images-for-use-with-nvidia-docker)
    - [Performing a dry run](#performing-a-dry-run)
    - [Upgrading from a previous version](#upgrading-from-a-previous-version)
- [Running automation tests](#running-automation-tests)
  - [Invocation approaches](#invocation-approaches)
  - [Container limitations](#container-limitations)
- [Usage with Continuous Integration systems](#usage-with-continuous-integration-systems)
  - [Jenkins](#jenkins)
- [Troubleshooting common issues](#troubleshooting-common-issues)
- [Windows `hcsshim` timeout issues](#windows-hcsshim-timeout-issues)


## Requirements

The common requirements for both Windows and Linux containers are:

- A minimum of 200GB of available disk space
- A minimum of 8GB of available memory
- [Python](https://www.python.org/) 3.6 or newer with `pip`
- The dependency packages listed in [requirements.txt](./requirements.txt), which can be installed by running `pip3 install -r requirements.txt`

Building **Windows containers** also requires:

- Windows 10 Pro/Enterprise or Windows Server 2016 or newer
- [Docker For Windows](https://www.docker.com/docker-windows) (under Windows 10) or [Docker EE For Windows Server](https://www.docker.com/docker-windows-server) (under Windows Server)
- Under Windows 10, the Docker daemon must be configured to use Windows containers instead of Linux containers
- The Docker daemon must be configured to increase the maximum container disk size from the default 20GB limit by following [the instructions provided by Microsoft](https://docs.microsoft.com/en-us/visualstudio/install/build-tools-container#step-4-expand-maximum-container-disk-size). The 120GB limit specified in the instructions is not quite enough, so set a 200GB limit instead.
- Under Windows Server, you may need to configure the firewall to allow network access to the host from inside Docker containers
- Under Windows Server Core, you will need to copy the following DLL files from a copy of Windows 10 (or Windows Server 2016 [with the Desktop Experience feature](https://docs.microsoft.com/en-us/windows-server/get-started/getting-started-with-server-with-desktop-experience)) and place them in the `C:\Windows\System32` directory:
    - `dsound.dll`
    - `opengl32.dll`
    - `glu32.dll`

Building **Linux containers** also requires:

- Windows 10 Pro/Enterprise, Linux or macOS
- [Docker For Windows](https://www.docker.com/docker-windows) (under Windows 10), [Docker CE](https://www.docker.com/community-edition) (under Linux) or [Docker For Mac](https://www.docker.com/docker-mac) (under macOS)
- Under Windows 10, the Docker daemon must be configured to use Linux containers instead of Windows containers
- Under Windows 10 and macOS, Docker must be configured in the "Advanced" settings pane to allocate 8GB of memory and a maximum disk image size of 200GB


## Build script usage

### Building images

First, ensure you have installed the dependencies of the Python build script by running `pip3 install -r requirements.txt`. (You may need to prefix this command with `sudo` under Linux and macOS.)

Then, simply invoke the build script by specifying the UE4 release that you would like to build using full [semver](https://semver.org/) version syntax. For example, to build Unreal Engine 4.19.1:

```
python3 build.py 4.19.1
```

*(Note that you may need to replace the command `python3` with `python` under Windows.)*

You will be prompted for the Git credentials to be used when cloning the UE4 GitHub repository (this will be the GitHub username and password you normally use when cloning <https://github.com/EpicGames/UnrealEngine>.) The build process will then start automatically, displaying progress output from each of the `docker build` commands that are being run.

Once the build process is complete, you will have five or six new Docker images on your system (where `RELEASE` is the release that you specified when invoking the build script):

- `adamrehn/ue4-build-prerequisites:latest` - this contains the build prerequisites common to all Engine versions and should be kept in order to speed up subsequent builds of additional Engine versions.
- `adamrehn/ue4-source:RELEASE` - this contains the cloned source code for UE4. This image is separated from the `ue4-build` image to isolate the effects of changing environment variables related to git credentials, so that they don't interfere with the build cache for the subsequent steps.
- `adamrehn/ue4-build:RELEASE` - this contains the source build for UE4.
- `adamrehn/conan-ue4cli:RELEASE` - this extends the source build with [conan-ue4cli](https://github.com/adamrehn/conan-ue4cli) support for building Conan packages that are compatible with UE4. This image will only be built for UE4 versions >= 4.19.0, which is the minimum Engine version required by ue4cli. You can disable the build for this image by specifying `--no-ue4cli` when you run the build script.
- `adamrehn/ue4-package:RELEASE` - this extends the `conan-ue4cli` image and is designed for packaging Shipping builds of UE4 projects. Note that the image simply creates an Installed Build of the Engine in order to speed up subsequent build time, and is not required in order to package projects (both the `ue4-build` and `conan-ue4cli` images can be used to package projects, albeit with longer build times.) This image will only be built if the `conan-ue4cli` image is built. You can disable the build for this image by specifying `--no-package` when you run the build script.
- `adamrehn/ue4-capture:RELEASE` - this extends the `ue4-package` image with support for the [UE4Capture](https://github.com/adamrehn/UE4Capture) plugin and is designed for capturing gameplay footage from inside NVIDIA Docker containers. This image will only be built when the `ue4-package` image is built with NVIDIA Docker compatibility. You can disable the build for this image by specifying `--no-capture` when you run the build script.

### Specifying the Windows Server Core base image tag

By default, Windows container images are based on the latest Windows Server Core release from the [Semi-Annual Channel](https://docs.microsoft.com/en-us/windows-server/get-started/semi-annual-channel-overview) release track (currently **Windows Server, version 1803**.) However, Windows containers cannot run a newer kernel version than that of the host operating system, rendering the latest images unusable under older versions of Windows 10 and Windows Server. (See the [Windows Container Version Compatibility](https://docs.microsoft.com/en-us/virtualization/windowscontainers/deploy-containers/version-compatibility) page for a table detailing which configurations are supported.)

If you are building or running images under an older version of Windows 10 or Windows Server, you will need to build images based on the same kernel version as the host system or older. The kernel version can be specified by providing the appropriate base OS image tag via the `-basetag=TAG` flag when invoking the build script:

```
python3 build.py 4.19.2 -basetag=ltsc2016  # Uses Windows Server 2016 (Long Term Support Channel)
```

For a list of supported base image tags, see the [Windows Server Core base image on Docker Hub](https://hub.docker.com/r/microsoft/windowsservercore/).

### Specifying the isolation mode under Windows

The isolation mode can be specified via the `-isolation=MODE` flag when invoking the build script. Valid values are `process` (supported under Windows Server only) or `hyperv` (supported under both Windows 10 or Windows Server.)

### Building Linux container images under Windows

By default, Windows container images are built when running the build script under Windows. To build Linux container images instead, simply specify the `--linux` flag when invoking the build script.

### Building GPU-enabled Linux container images for use with NVIDIA Docker

[NVIDIA Docker](https://github.com/NVIDIA/nvidia-docker) provides a container runtime for Docker that allows Linux containers to access NVIDIA GPU devices present on the host system. This facilitates hardware acceleration for applications that use OpenGL or NVIDIA CUDA, and can be useful for Unreal projects that need to perform offscreen rendering from within a container. To build Linux container images that support hardware-accelerated OpenGL when run via NVIDIA Docker, simply specify the `--nvidia` flag when invoking the build script.

Note that **NVIDIA Docker version 2.x is required** to run the built images (version 1.x is not supported) and that the images can only be run under a Linux host system with one or more NVIDIA GPUs.

### Performing a dry run

If you would like to see what `docker build` commands will be run without actually building anything, you can specify the `--dry-run` flag when invoking the build script. Execution will proceed as normal, except that all `docker build` commands will be printed to standard output instead of being executed as child processes.

### Upgrading from a previous version

When upgrading to a newer version of the code in this repository, be sure to specify the `--rebuild` flag when invoking the build script. This will ensure all images are rebuilt using the updated Dockerfiles.


## Running automation tests

### Invocation approaches

There are three main approaches for running [Automation Tests](https://docs.unrealengine.com/en-us/Programming/Automation) from the command line. These three approaches are illustrated below, accompanied by the recommended arguments for running correctly inside a Docker container:

- **Invoking the Editor directly:**<br>`path/to/UE4Editor <UPROJECT> -game -buildmachine -stdout -fullstdoutlogoutput -forcelogflush -unattended -nopause -nullrhi -ExecCmds="automation RunTests <TEST1>+<TEST2>+<TESTN>;quit"`

- **Using Unreal AutomationTool (UAT):**<br>`path/to/RunUAT BuildCookRun -project=<UPROJECT> -noP4 -buildmachine -unattended -nullrhi -run "-RunAutomationTest=<TEST1>+<TEST2>+<TESTN>"`

- **Using [ue4cli](https://github.com/adamrehn/ue4cli)**:<br>`ue4 test <TEST1> <TEST2> <TESTN>`
  
  *(Note that it is also possible to use the `uat` subcommand to invoke UAT, e.g. `ue4 uat BuildCookRun <ARGS...>`, but the `test` command is the recommended way of running automation tests using ue4cli.)*

Each of these approaches has its own benefits and limitations:

|Approach |Supported Docker images |Benefits |Limitations |
|---------|------------------------|---------|------------|
|Editor   |<ul><li>`ue4-build`</li><li>`conan-ue4cli`</li><li>`ue4-package`</li></ul>|<ul><li>Maximum control and flexibility</li></ul>|<ul><li>Extremely verbose syntax</li><li>Requires the full path to the platform-specific `UE4Editor` binary (must be `UE4Editor-Cmd.exe` under Windows)</li><li>Project must already be built, as the Editor will not prompt to build missing modules and will instead simply crash</li><li>Exit code is always non-zero, so log output must be parsed to detect failures</li><li>[Exact placement of quotes matters under Windows.](https://adamrehn.com/articles/idiosyncratic-argument-parsing-behaviour-in-unreal-engine-4/)</li></ul>|
|UAT      |<ul><li>`ue4-build`</li><li>`conan-ue4cli`</li><li>`ue4-package`</li></ul>|<ul><li>Supports advanced functionality (e.g. running both client and server)</li></ul>|<ul><li>Restricts which arguments can be passed to the Editor (although most are supported)</li><li>Requires the full path to the platform-specific `RunUAT` batch file or shell script</li><li>Project must already be built, or else the relevant arguments must be included to perform the build</li><li>Exit code will be zero so long as the Editor didn't crash, test failures are merely reported in the log output</li><li>If the Editor crashes then UAT will wait for a 30 second grace period before reporting the error</li></ul> |
|ue4cli   |<ul><li>`conan-ue4cli`</li><li>`ue4-package`</li></ul>|<p>When using `ue4 test`:</p><ul><li>Concise syntax</li><li>Determines the path to the Editor automatically</li><li>Automatically builds the project if not already built</li><li>Exit code actually reflects test success or failure (in addition to being non-zero for errors or crashes)</li><li>Reports Editor crashes immediately</li></ul><p>When using `ue4 uat`:</p><ul><li>Determines the path to `RunUAT` automatically</li><li>All the benefits of using UAT listed above</li></ul>|<p>Irrespective of subcommand:</p><ul><li>Not supported by the `ue4-build` image, which lacks ue4cli</li><li>Must be run from the directory containing the `.uproject` file</li></ul><p>When using `ue4 test`:</p><ul><li>Restricts which arguments can be passed to the Editor (although I've included all the arguments I believe are necessary)</li></ul><p>When using `ue4 uat`:</p><ul><li>All the limitations of using UAT listed above (with the exception of requiring the full path to `RunUAT`)</li></ul>|

### Container limitations

Irrespective of the invocation approach utilised, the following limitations apply when running automation tests inside Docker containers:

- Tests requiring sound output will not function correctly.
- Tests that require Virtual Reality (VR) or Augmented Reality (AR) devices or runtimes to be present will not function correctly.
- The Windows-specific plugins `WindowsMoviePlayer` and `WmfMedia` that are enabled by default as of UE4.19 both require [Microsoft Media Foundation](https://msdn.microsoft.com/en-us/library/windows/desktop/ms694197(v=vs.85).aspx) in order to function correctly. Under Windows Server Core, Media Foundation is [provided by the `Server-Media-Foundation` optional feature](https://docs.microsoft.com/en-us/windows-server/administration/server-core/server-core-roles-and-services#features-included-in-server-core). However, this feature has a history of being problematic inside Docker containers, and was [removed from the Server Core container image in Windows Server, version 1803](https://docs.microsoft.com/en-us/windows-server/administration/server-core/server-core-container-removed-roles). As such, any tests that rely on these plugins will not function correctly.


## Usage with Continuous Integration systems

### Jenkins

The following resources document the use of these Docker images with the [Jenkins](https://jenkins.io/) Continuous Integration system:

- <https://github.com/adamrehn/ue4-opencv-demo> - provides an example of using Jenkins to build a UE4 project that consumes a third-party library package via [conan-ue4cli](https://github.com/adamrehn/conan-ue4cli).


## Troubleshooting common issues

- **The build script refuses to accept valid Engine version numbers (i.e. it fails with a message such as `Error: invalid UE4 release number "4.19.2", full semver format required (e.g. "4.19.0")`):**
  
  This is caused by the package [node-semver](https://pypi.org/project/node-semver/) being present on the system, which conflicts with the [semver](https://pypi.org/project/semver/) package upon which the build script depends. The conflicting package will need to be removed using the command `pip3 uninstall node-semver` (may require `sudo` under macOS and Linux.)

- **Building Windows containers fails with the message `hcsshim: timeout waiting for notification extra info`:**
  
  This is a known issue when using Windows containers in Hyper-V isolation mode. See the [Windows `hcsshim` timeout issues](#windows-hcsshim-timeout-issues) section below for a detailed discussion of this problem and the available workarounds.

- **Building or running Windows containers fails with the message `The operating system of the container does not match the operating system of the host`:**
  
  This error is shown in two situations:
  
    - The host system is running an **older kernel version** than the container image. In this case, you will need to build the images using the same kernel version as the host system or older. See the [Specifying the Windows Server Core base image tag](#specifying-the-windows-server-core-base-image-tag) section above for details on specifying the correct kernel version when building Windows container images.
    - The host system is running a **newer kernel version** than the container image and you are attempting to use process isolation mode instead of Hyper-V isolation mode. (Process isolation mode is the default under Windows Server.) In this case, you will need to use Hyper-V isolation mode instead. See the [Specifying the isolation mode under Windows](#specifying-the-isolation-mode-under-windows) section above for details on how to do this.

- **Building Windows containers fails with the message `hcsshim::ImportLayer failed in Win32: The system cannot find the path specified` or building Linux containers fails with a message about insufficient disk space:**
  
  Assuming you haven't actually run out of disk space, this means that the maximum Docker image size has not been configured correctly.
  
    - For Windows containers, follow [the instructions provided by Microsoft](https://docs.microsoft.com/en-us/visualstudio/install/build-tools-container#step-4-expand-maximum-container-disk-size), making sure you restart the Docker daemon after you've modified the config JSON.
    - For Linux containers, use the [Docker for Windows "Advanced" settings tab](https://docs.docker.com/docker-for-windows/#advanced) under Windows or the [Docker for Mac "Disk" settings tab](https://docs.docker.com/docker-for-mac/#disk) under macOS.

- **Pulling the .NET Framework base image fails with the message `ProcessUtilityVMImage \\?\`(long path here)`\UtilityVM: The system cannot find the path specified`:**
  
  This is a known issue when the host system is running an older kernel version than the container image. Just like in the case of the *"The operating system of the container does not match the operating system of the host"* error mentioned above, you will need to build the images using the same kernel version as the host system or older. See the [Specifying the Windows Server Core base image tag](#specifying-the-windows-server-core-base-image-tag) section above for details on specifying the correct kernel version when building Windows container images.

- **Cloning the UnrealEngine Git repository fails with the message `error: unable to read askpass response from 'C:\git-credential-helper.bat'` (for Windows containers) or `'/tmp/git-credential-helper.sh'` (for Linux containers):**
  
  This typically indicates that the firewall on the host system is blocking connections from the Docker container, preventing it from retrieving the Git credentials supplied by the build script. (This is particularly noticeable under a clean installation of Windows Server, which blocks connections from other subnets by default.) The firewall will need to be configured appropriately to allow the connection, or else temporarily disabled. (Use the command `netsh advfirewall set allprofiles state off` under Windows Server.)


## Windows `hcsshim` timeout issues

Recent versions of Docker under Windows may sometimes encounter the error [hcsshim: timeout waiting for notification extra info](https://github.com/Microsoft/hcsshim/issues/152) when building or running Windows containers. **This issue appears to be related to [Hyper-V isolation](https://docs.microsoft.com/en-us/virtualization/windowscontainers/manage-containers/hyperv-container) mode and has not been observed to affect containers running in process isolation mode.** At the time of writing, Microsoft have stated that they are aware of the problem, but an official fix is yet to be released.

As a workaround until a proper fix is issued, it seems that altering the memory limit for containers between subsequent invocations of the `docker` command can reduce the frequency with which this error occurs. (Changing the memory limit when using Hyper-V isolation likely forces Docker to provision a new Hyper-V VM, preventing it from re-using an existing one that has become unresponsive.) Please note that this workaround has been devised based on my own testing under Windows 10 and may not hold true when using Hyper-V isolation under Windows Server.

To enable the workaround, specify the `--random-memory` flag when invoking the build script. This will set the container memory limit to a random value between 8GB and 10GB when the build script starts. If a build fails with the `hcsshim` timeout error, simply re-run the build script and in most cases the build will continue successfully, even if only for a short while. Restarting the Docker daemon may also help.

Note that in some cases, using a memory limit that is not a multiple of 4GB can cause UnrealBuildTool to crash with an error stating *"The process cannot access the file because it is being used by another process."* If this happens, simply run the build script again without the `--random-memory` flag. If the access error occurs when using the default memory limit, this likely indicates that Windows is unable to allocate the full 8GB to the container. Rebooting the host system may help to alleviate this issue.
