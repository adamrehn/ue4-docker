<p align="center"><img src="./resources/images/banner.svg" alt="Unreal Engine and Docker Logos" height="100"></p>
<h1 align="center"><strong>Unreal Engine 4 Docker Containers</strong></h1>
<h3 align="center">Continuous Integration &bull; Cloud Rendering &bull; UE4-Powered Microservices</h3>
<p>&nbsp;</p>

**Looking for a place to start? Interactive documentation is coming soon with step-by-step instructions.**

The ue4-docker Python package contains a set of Dockerfiles and accompanying build infrastructure that allows you to build Docker images for Epic Games' [Unreal Engine 4](https://www.unrealengine.com/). Key features include:

- Unreal Engine 4.19.0 and newer is supported.
- Both Windows containers and Linux containers are supported.
- Building and packaging UE4 projects is supported.
- Running automation tests is supported.
- The `ue4-engine` image contains a full source build of the Engine and is suitable for developing Engine patches.
- The `ue4-minimal` and `ue4-full` images contain an [Installed Build](https://docs.unrealengine.com/en-us/Programming/Deployment/Using-an-Installed-Build) of the Engine suitable for use in Continuous Integration (CI) pipelines.
- The `ue4-full` image includes support for integrating third-party libraries via [conan-ue4cli](https://github.com/adamrehn/conan-ue4cli), including [UE4Capture](https://github.com/adamrehn/UE4Capture) when building GPU-enabled Linux images.

For a detailed discussion on how the build process works, see [the accompanying article on my website](http://adamrehn.com/articles/building-docker-images-for-unreal-engine-4).


## Contents

- [Important legal notice](#important-legal-notice)
- [Requirements](#requirements)
- [Build command usage](#build-command-usage)
    - [Building images](#building-images)
    - [Specifying the Git credentials](#specifying-the-git-credentials)
    - [Building a custom version of the Unreal Engine](#building-a-custom-version-of-the-unreal-engine)
    - [Specifying the Windows Server Core base image tag](#specifying-the-windows-server-core-base-image-tag)
    - [Specifying the isolation mode under Windows](#specifying-the-isolation-mode-under-windows)
    - [Specifying the directory from which to copy required Windows DLL files](#specifying-the-directory-from-which-to-copy-required-Windows-dll-files)
    - [Building Linux container images under Windows](#building-linux-container-images-under-windows)
    - [Using GPU-enabled Linux container images with NVIDIA Docker](#using-gpu-enabled-linux-container-images-with-nvidia-docker)
    - [Performing a dry run](#performing-a-dry-run)
    - [Upgrading from a previous version](#upgrading-from-a-previous-version)
- [Running automation tests](#running-automation-tests)
  - [Invocation approaches](#invocation-approaches)
  - [Container limitations](#container-limitations)
- [Usage with Continuous Integration systems](#usage-with-continuous-integration-systems)
  - [Jenkins](#jenkins)
- [Performing cloud rendering using the NVIDIA Docker images](#performing-cloud-rendering-using-the-nvidia-docker-images)
  - [Basic usage](#basic-usage)
  - [Audio support](#audio-support)
  - [WebRTC streaming demo](#webrtc-streaming-demo)
- [Troubleshooting common issues](#troubleshooting-common-issues)
- [Windows `hcsshim` timeout issues](#windows-hcsshim-timeout-issues)
- [Frequently Asked Questions](#frequently-asked-questions)
- [Legal](#legal)


## Important legal notice

**The Docker images produced by the code in this repository contain the UE4 Engine Tools in both source code and object code form. As per Section 1A of the [Unreal Engine EULA](https://www.unrealengine.com/eula), Engine Licensees are prohibited from public distribution of the Engine Tools unless such distribution takes place via the Unreal Marketplace or a fork of the Epic Games UE4 GitHub repository. [Public distribution of the built images via an openly accessible Docker Registry (e.g. Docker Hub) is a direct violation of the license terms.](https://www.unrealengine.com/eula) It is your responsibility to ensure that any private distribution to other Engine Licensees (such as via an organisation's internal Docker Registry) complies with the terms of the Unreal Engine EULA.**


## Requirements

The common requirements for both Windows and Linux containers are:

- A minimum of 300GB available disk space (400GB under Windows)
- A minimum of 8GB of available memory (10GB under Windows)
- [Python](https://www.python.org/) 3.6 or newer with `pip`
- The ue4-docker package itself, which can be installed by running `pip3 install ue4-docker`

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
- Note that the three DLL files listed above must be copied from the **same version of Windows** as the Windows Server Core host system (e.g. Windows Server 1709 needs DLLs from Windows 10 1709, Windows Server 1803 needs DLLs from Windows 10 1803, etc.) Although DLLs from an older system version may potentially work, Windows will refuse to load these DLL files if they have been copied from a version of Windows that is newer than the host.

Building **Linux containers** also requires:

- Windows 10 Pro/Enterprise, Linux or macOS (only Linux is supported for running GPU-enabled images with NVIDIA Docker)
- [Docker For Windows](https://www.docker.com/docker-windows) (under Windows 10), [Docker CE](https://www.docker.com/community-edition) (under Linux) or [Docker For Mac](https://www.docker.com/docker-mac) (under macOS)
- Under Windows 10, the Docker daemon must be configured to use Linux containers instead of Windows containers
- Under Windows 10 and macOS, Docker must be configured in the "Advanced" settings pane to allocate 8GB of memory and a maximum disk image size of 200GB


## Build command usage

### Building images

First, install the ue4-docker package using `pip3 install ue4-docker`. (You may need to prefix this command with `sudo` under Linux and macOS.)

Then, simply invoke the build command by specifying the UE4 release that you would like to build using full [semver](https://semver.org/) version syntax. For example, to build Unreal Engine 4.19.1:

```
ue4-docker build 4.19.1
```

You will be prompted for the Git credentials to be used when cloning the UE4 GitHub repository (this will be the GitHub username and password you normally use when cloning <https://github.com/EpicGames/UnrealEngine>.) See the section [Specifying the Git credentials](#specifying-the-git-credentials) for details of the different methods by which credentials can be specified. The build process will then start automatically, displaying progress output from each of the `docker build` commands that are being run.

Once the build process is complete, you will have up to five new Docker images on your system (where `RELEASE` is the release that you specified when invoking the build command):

|Image                                     |Description |
|------------------------------------------|------------|
|`adamrehn/ue4-build-prerequisites:latest` |Contains the build prerequisites common to all Engine versions and should be kept in order to speed up subsequent builds of additional Engine versions.|
|`adamrehn/ue4-source:RELEASE`             |Contains the cloned source code for UE4. This image is separated from the `ue4-engine` image to isolate the effects of changing environment variables related to git credentials, so that they don't interfere with the build cache for the subsequent steps.|
|`adamrehn/ue4-engine:RELEASE`             |Contains a source build of the Engine. You can disable the build for this image by specifying `--no-engine` when you run the build command.<br><br>**Use this image for developing changes to the Engine itself.**|
|`adamrehn/ue4-minimal:RELEASE`            |Contains the absolute minimum set of functionality required for use in a Continuous Integration (CI) pipeline, consisting of only the build prerequisites and an Installed Build of the Engine. You can disable the build for this image by specifying `--no-minimal` when you run the build command.<br><br>**Use this image for CI pipelines that do not require ue4cli or conan-ue4cli.**|
|`adamrehn/ue4-full:RELEASE`               |Contains everything from the `ue4-minimal` image, and adds the following:<ul><li>ue4cli</li><li>conan-ue4cli</li><li>UE4Capture (Linux image only)</li></ul>You can disable the build for this image by specifying `--no-full` when you run the build command.<br><br>**Use this image for any of the following:**<ul><li><strong>CI pipelines that require ue4cli or conan-ue4cli</strong></li><li><strong>Packaging or running cloud rendering projects that utilise UE4Capture under Linux</strong></li><li><strong>Packaging UE4-powered server applications</strong></li></ul>|

### Specifying the Git credentials

The build command supports three methods for specifying the credentials that will be used to clone the UE4 Git repository:

- **Command-line arguments**: the `-username` and `-password` command-line arguments can be used to specify the username and password, respectively.

- **Environment variables**: the `UE4DOCKER_USERNAME` and `UE4DOCKER_PASSWORD` environment variables can be used to specify the username and password, respectively. Note that credentials specified via command-line arguments will take precedence over values defined in environment variables.

- **Standard input**: if either the username or password has not been specified via a command-line argument or environment variable then the build command will prompt the user to enter the credential(s) for which values have not already been specified.

Note that the username and password are handled independently, which means you can use different methods to specify the two credentials (e.g. username specified via command-line argument and password supplied via standard input.)

### Building a custom version of the Unreal Engine

If you would like to build a custom version of UE4 rather than one of the official releases from Epic, you can specify "custom" as the release string and specify the Git repository and branch/tag that should be cloned:

```
ue4-docker build custom -repo=https://github.com/MyUser/UnrealEngine.git -branch=MyBranch
```

When building a custom Engine version, both the repository URL and branch/tag must be specified. If you are performing multiple custom builds and wish to differentiate between them, it is recommended to add a custom suffix to the Docker tag of the built images:

```
ue4-docker build custom -repo=https://github.com/MyUser/UnrealEngine.git -branch=MyBranch -suffix=-MySuffix
```

This will produce images tagged `adamrehn/ue4-source:custom-MySuffix`, `adamrehn/ue4-engine:custom-MySuffix`, etc.

### Specifying the Windows Server Core base image tag

By default, Windows container images are based on the Windows Server Core release that best matches the version of the host operating system. However, Windows containers cannot run a newer kernel version than that of the host operating system, rendering the latest images unusable under older versions of Windows 10 and Windows Server. (See the [Windows Container Version Compatibility](https://docs.microsoft.com/en-us/virtualization/windowscontainers/deploy-containers/version-compatibility) page for a table detailing which configurations are supported.)

If you are building images with the intention of subsequently running them under an older version of Windows 10 or Windows Server, you will need to build images based on the same kernel version as the target system (or older.) The kernel version can be specified by providing the appropriate base OS image tag via the `-basetag=TAG` flag when invoking the build command:

```
ue4-docker build 4.19.2 -basetag=ltsc2016  # Uses Windows Server 2016 (Long Term Support Channel)
```

For a list of supported base image tags, see the [Windows Server Core base image on Docker Hub](https://hub.docker.com/r/microsoft/windowsservercore/).

### Specifying the isolation mode under Windows

The isolation mode can be specified via the `-isolation=MODE` flag when invoking the build command. Valid values are `process` (supported under Windows Server only) or `hyperv` (supported under both Windows 10 and Windows Server.)

### Specifying the directory from which to copy required Windows DLL files

By default, DLL files are copied from `%SystemRoot%\System32`. However, when building container images with an older kernel version than the host, the copied DLL files will be too new and the container OS will refuse to load them. A custom directory containing the correct DLL files for the container kernel version can be specified via the `-dlldir=DIR` flag when invoking the build command. 

### Building Linux container images under Windows

By default, Windows container images are built when running the build command under Windows. To build Linux container images instead, simply specify the `--linux` flag when invoking the build command.

### Using GPU-enabled Linux container images with NVIDIA Docker

[NVIDIA Docker](https://github.com/NVIDIA/nvidia-docker) provides a container runtime for Docker that allows Linux containers to access NVIDIA GPU devices present on the host system. This facilitates hardware acceleration for applications that use OpenGL or NVIDIA CUDA, and can be useful for Unreal projects that need to perform offscreen rendering from within a container or utilise plugins that rely on CUDA functionality.

All Linux container images built by the build command support both the regular Docker runtime and NVIDIA Docker, allowing them to be used for CPU-only workloads (such as CI/CD) as well as GPU-enabled workloads (such as cloud rendering.) By default, the images support hardware-accelerated OpenGL when run via NVIDIA Docker. If you would like CUDA support in addition to OpenGL support, simply specify the `--cuda` flag when invoking the build command.

Key things to note:

- NVIDIA Docker is not required in order to build the images, or to run the built images for CPU-only workloads.
- NVIDIA Docker version 2.x is required to run the built images with GPU support. **NVIDIA Docker version 1.x is not supported.**
- The images can only be run via NVIDIA Docker under a Linux host system with one or more NVIDIA GPUs. Images with CUDA support also have [additional requirements](https://github.com/NVIDIA/nvidia-docker/wiki/CUDA#requirements) on top of the requirements for OpenGL support.

### Performing a dry run

If you would like to see what `docker build` commands will be run without actually building anything, you can specify the `--dry-run` flag when invoking the build command. Execution will proceed as normal, except that all `docker build` commands will be printed to standard output instead of being executed as child processes.

### Upgrading from a previous version

When upgrading to a newer version of the code in this repository, be sure to specify the `--rebuild` flag when invoking the build command. This will ensure all images are rebuilt using the updated Dockerfiles.


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
|Editor   |<ul><li>`ue4-engine`</li><li>`ue4-minimal`</li><li>`ue4-full`</li></ul>|<ul><li>Maximum control and flexibility</li></ul>|<ul><li>Extremely verbose syntax</li><li>Requires the full path to the platform-specific `UE4Editor` binary (must be `UE4Editor-Cmd.exe` under Windows)</li><li>Project must already be built, as the Editor will not prompt to build missing modules and will instead simply crash</li><li>Exit code is always non-zero, so log output must be parsed to detect failures</li><li>[Exact placement of quotes matters under Windows prior to 4.21.0.](https://adamrehn.com/articles/idiosyncratic-argument-parsing-behaviour-in-unreal-engine-4/)</li></ul>|
|UAT      |<ul><li>`ue4-engine`</li><li>`ue4-minimal`</li><li>`ue4-full`</li></ul>|<ul><li>Supports advanced functionality (e.g. running both client and server)</li></ul>|<ul><li>Restricts which arguments can be passed to the Editor (although most are supported)</li><li>Requires the full path to the platform-specific `RunUAT` batch file or shell script</li><li>Project must already be built, or else the relevant arguments must be included to perform the build</li><li>Exit code will be zero so long as the Editor didn't crash, test failures are merely reported in the log output</li><li>If the Editor crashes then UAT will wait for a 30 second grace period before reporting the error</li></ul> |
|ue4cli   |<ul><li>`ue4-full`</li></ul>|<p>When using `ue4 test`:</p><ul><li>Concise syntax</li><li>Determines the path to the Editor automatically</li><li>Automatically builds the project if not already built</li><li>Exit code actually reflects test success or failure (in addition to being non-zero for errors or crashes)</li><li>Reports Editor crashes immediately</li></ul><p>When using `ue4 uat`:</p><ul><li>Determines the path to `RunUAT` automatically</li><li>All the benefits of using UAT listed above</li></ul>|<p>Irrespective of subcommand:</p><ul><li>Must be run from the directory containing the `.uproject` file</li></ul><p>When using `ue4 test`:</p><ul><li>Restricts which arguments can be passed to the Editor (although I've included all the arguments I believe are necessary)</li></ul><p>When using `ue4 uat`:</p><ul><li>All the limitations of using UAT listed above (with the exception of requiring the full path to `RunUAT`)</li></ul>|

### Container limitations

Irrespective of the invocation approach utilised, the following limitations apply when running automation tests inside Docker containers:

- Tests requiring sound output will not function correctly.
- Tests that require Virtual Reality (VR) or Augmented Reality (AR) devices or runtimes to be present will not function correctly.
- The Windows-specific plugins `WindowsMoviePlayer` and `WmfMedia` that are enabled by default as of UE4.19 both require [Microsoft Media Foundation](https://msdn.microsoft.com/en-us/library/windows/desktop/ms694197(v=vs.85).aspx) in order to function correctly. Under Windows Server Core, Media Foundation is [provided by the `Server-Media-Foundation` optional feature](https://docs.microsoft.com/en-us/windows-server/administration/server-core/server-core-roles-and-services#features-included-in-server-core). However, this feature has a history of being problematic inside Docker containers, and was [removed from the Server Core container image in Windows Server, version 1803](https://docs.microsoft.com/en-us/windows-server/administration/server-core/server-core-container-removed-roles). As such, any tests that rely on these plugins will not function correctly.


## Usage with Continuous Integration systems

### Jenkins

The following resources document the use of these Docker images with the [Jenkins](https://jenkins.io/) Continuous Integration system:

- <https://github.com/adamrehn/ue4-opencv-demo> - provides an example of using Jenkins to build a UE4 project that consumes a third-party library package via [conan-ue4cli](https://github.com/adamrehn/conan-ue4cli).


## Performing cloud rendering using the NVIDIA Docker images

### Basic usage

The `ue4-full` image can be used with NVIDIA Docker to either run Unreal projects directly or to build and package them for use inside any Docker container that is based on the [nvidia/opengl](https://hub.docker.com/r/nvidia/opengl/) or [nvidia/cudagl](https://hub.docker.com/r/nvidia/cudagl/) base images. For more details on using NVIDIA Docker images, see the [official documentation](https://github.com/NVIDIA/nvidia-docker).

When running inside an OpenGL-enabled NVIDIA Docker container, the Unreal Engine will automatically default to offscreen rendering. You can capture the contents of the framebuffer using the [UE4Capture](https://github.com/adamrehn/UE4Capture) plugin in exactly the same way as when running outside of a container.

### Audio support

To enable audio support inside an NVIDIA Docker container, you will need to be running a PulseAudio server on the host system and bind-mount the current user's PulseAudio socket by specifying the argument `-v/run/user/$UID/pulse:/run/user/1000/pulse` when invoking the `docker run` command. Note that this will not work for the root user, so you will need to run the command as a non-root user as described by the [Post-installation steps for Linux](https://docs.docker.com/install/linux/linux-postinstall/) page of the Docker documentation.

If you are running containers inside a virtual machine that does not have access to any physical audio devices, you will need to utilise an alternative such as an [ALSA loopback device](https://www.alsa-project.org/main/index.php/Matrix:Module-aloop), which can be enabled on most Linux distributions by using the command `sudo modprobe snd_aloop`. Note that this module is not available in the AWS-tuned Linux kernel that is used by default for AWS virtual machines, so you will need to [switch to a vanilla Linux kernel](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/UserProvidedKernels.html) in order to make use of an ALSA loopback.

If you are using the [UE4Capture](https://github.com/adamrehn/UE4Capture) plugin to capture audio, you will need to ensure that you specify the argument `-AudioMixer` when running the Unreal project from which audio will be captured.

### WebRTC streaming demo

For an example that demonstrates performing cloud rendering in the `ue4-full` NVIDIA Docker image and then streaming the video to a web browser via WebRTC, see the **[ue4-cloud-rendering-demo](https://github.com/adamrehn/ue4-cloud-rendering-demo)** repository.


## Troubleshooting common issues

- **Building Windows containers fails with the message `hcsshim: timeout waiting for notification extra info` or the message `This operation ended because the timeout has expired`:**
  
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
  
  This typically indicates that the firewall on the host system is blocking connections from the Docker container, preventing it from retrieving the Git credentials supplied by the build command. (This is particularly noticeable under a clean installation of Windows Server, which blocks connections from other subnets by default.) The firewall will need to be configured appropriately to allow the connection, or else temporarily disabled. (Use the command `netsh advfirewall set allprofiles state off` under Windows Server.)

- **Building the Engine in a Windows container fails with the message `The process cannot access the file because it is being used by another process`:**
  
  This is a known bug in some older versions of UnrealBuildTool when using a memory limit that is not a multiple of 4GB. To alleviate this issue, specify an appropriate memory limit override (e.g. `-m 8GB` or `-m 12GB`.) For more details on this issue, see the last paragraph of the [Windows `hcsshim` timeout issues](#windows-hcsshim-timeout-issues) section below.

- **Building the Engine in a Windows container fails with the message `fatal error LNK1318: Unexpected PDB error; OK (0)`:**
  
  This is a known bug in some versions of Visual Studio, which only appears to occur intermittently. The simplest fix is to simply reboot the host system and then re-run the build command. Insufficient available memory may also contribute to triggering this bug.

- **Building an Unreal project in a Windows container fails when the project files are located in a directory that is bind-mounted from the host operating system:**
  
  Evidently the paths associated with Windows bind-mounted directories can cause issues for certain build tools, including UnrealBuildTool and CMake. As a result, building Unreal projects located in Windows bind-mounted directories is not advised. The solution is to copy the Unreal project to a temporary directory within the container's filesystem and build it there, copying any produced build artifacts back to the host system via the bind-mounted directory as necessary.
  
  ***Note 1:** This problem has currently only been observed when running containers under Hyper-V isolation mode and has not yet been observed to affect containers running under process isolation mode. However, it is still recommended that you implement the copy-based workaround in your own CI pipelines to ensure compatibility with both isolation modes.*
  
  ***Note 2:** This problem does not apply to Linux containers.*

- **Building the Derived Data Cache (DDC) for the Installed Build of the Engine fails with a message about failed shader compilation or being unable to open a `.uasset` file:**
  
  This is typically caused by insufficient available disk space. To fix this, simply free up some disk space and run the build again. Running `docker system prune` can be helpful for freing up space occupied by untagged images. Note that restarting the Docker daemon and/or rebooting the host system may also help, since some versions of Docker have a bug that results in the amount of required disk space slowly increasing as more and more builds are run.


## Windows `hcsshim` timeout issues

Recent versions of Docker under Windows may sometimes encounter the error [hcsshim: timeout waiting for notification extra info](https://github.com/Microsoft/hcsshim/issues/152) when building or running Windows containers. **This issue appears to be related to [Hyper-V isolation](https://docs.microsoft.com/en-us/virtualization/windowscontainers/manage-containers/hyperv-container) mode and has not been observed to affect containers running in process isolation mode.** At the time of writing, Microsoft have stated that they are aware of the problem, but an official fix is yet to be released.

As a workaround until a proper fix is issued, it seems that altering the memory limit for containers between subsequent invocations of the `docker` command can reduce the frequency with which this error occurs. (Changing the memory limit when using Hyper-V isolation likely forces Docker to provision a new Hyper-V VM, preventing it from re-using an existing one that has become unresponsive.) Please note that this workaround has been devised based on my own testing under Windows 10 and may not hold true when using Hyper-V isolation under Windows Server.

To enable the workaround, specify the `--random-memory` flag when invoking the build command. This will set the container memory limit to a random value between 10GB and 12GB when the build command starts. If a build fails with the `hcsshim` timeout error, simply re-run the build command and in most cases the build will continue successfully, even if only for a short while. Restarting the Docker daemon may also help.

Note that some older versions of UnrealBuildTool will crash with an error stating *"The process cannot access the file because it is being used by another process"* when using a memory limit that is not a multiple of 4GB. If this happens, simply run the build command again with an appropriate memory limit (e.g. `-m 8GB` or `-m 12GB`.) If the access error occurs even when using an appropriate memory limit, this likely indicates that Windows is unable to allocate the full amount of memory to the container. Rebooting the host system may help to alleviate this issue.


## Frequently Asked Questions

- **Why are the Dockerfiles written in such an inefficient manner? There are a large number of `RUN` directives that could be combined to improve both build efficiency and overall image size.**
  
  With the exception of the `ue4-build-prerequisites` and `ue4-minimal` images, the Dockerfiles have been deliberately written in an inefficient way because doing so serves two very important purposes.
  
  The first purpose is self-documentation. These Docker images are the first publicly-available Windows and Linux images to provide comprehensive build capabilities for Unreal Engine 4. Along with the supporting documentation and [articles on adamrehn.com](https://adamrehn.com/articles/tag/Unreal%20Engine/), the code in this repository represents an important source of information regarding the steps that must be taken to get UE4 working correctly inside a container. The readability of the Dockerfiles is key, which is why they contain so many individual `RUN` directives with explanatory comments. Combining `RUN` directives would reduce readability and potentially obfuscate the significance of critical steps.
  
  The second purpose is debuggability. Updating the Dockerfiles to ensure compatibility with new Unreal Engine releases is an extremely involved process that typically requires building the Engine many times over. By breaking the Dockerfiles into many fine-grained `RUN` directives, the Docker build cache can be leveraged to ensure only the failing steps need to be repeated when rebuilding the images during debugging. Combining `RUN` directives would increase the amount of processing that needs to be redone each time one of the commands in a given directive fails, significantly increasing overall debugging times.

- **Can the Windows containers be used to perform cloud rendering in the same manner as the Linux NVIDIA Docker containers?**
  
  Unfortunately not. [NVIDIA Docker only supports Linux at this time](https://github.com/NVIDIA/nvidia-docker/wiki/Frequently-Asked-Questions#platform-support) and I am aware of no available equivalent for Windows containers. It is possible that this situation may change in the future as Windows containers mature and become more widely adopted.

- **Is it possible to build Unreal projects for macOS or iOS using the Docker containers?**
  
  Building projects for macOS or iOS requires a copy of macOS and Xcode. Since macOS cannot run inside a Docker container, there is unfortunately no way to perform macOS or iOS builds using Docker containers.


## Legal

Copyright &copy; 2018, Adam Rehn. Licensed under the MIT License, see the file [LICENSE](./LICENSE) for details.

Unreal and its logo are Epic Games' trademarks or registered trademarks in the US and elsewhere.

Docker and the Docker logo are trademarks or registered trademarks of Docker in the United States and other countries.
