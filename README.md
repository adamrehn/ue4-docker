Dockerfiles for Unreal Engine 4
===============================

**IMPORTANT LEGAL NOTICE: the Docker images produced by the code in this repository contain the UE4 Engine Tools in both source code and object code form. As per Section 1A of the [Unreal Engine EULA](https://www.unrealengine.com/eula), Engine Licensees are prohibited from public distribution of the Engine Tools unless such distribution takes place via the Unreal Marketplace or a fork of the Epic Games UE4 GitHub repository. [Public distribution of the built images via an openly accessible Docker Registry (e.g. Docker Hub) is a direct violation of the license terms.](https://www.unrealengine.com/eula) It is your responsibility to ensure that any private distribution to other Engine Licensees (such as via an organisation's internal Docker Registry) complies with the terms of the Unreal Engine EULA.**

This repository contains a set of Dockerfiles and an accompanying Python build script that allow you to build Docker images for Epic Games' [Unreal Engine 4](https://www.unrealengine.com/). Key features include:

- The images contain a full source build of the Engine and are suitable for use in a Continuous Integration (CI) pipeline.
- **Both Windows containers and Linux containers are supported.**
- When building UE4 version 4.19.0 or newer, [conan-ue4cli](https://github.com/adamrehn/conan-ue4cli) support is also built by default, although this behaviour can be disabled by using the `--no-ue4cli` flag when invoking the build script.

For a detailed discussion on how the build process works, see [the accompanying article on my website](http://adamrehn.com/articles/building-docker-images-for-unreal-engine-4).


## Contents

- [Requirements](#requirements)
- [Build script usage](#build-script-usage)
    - [Building images](#building-images)
    - [Building Linux container images under Windows](#building-linux-container-images-under-windows)
    - [Performing a dry run](#performing-a-dry-run)
    - [Upgrading from a previous version](#upgrading-from-a-previous-version)
- [Windows `hcsshim` timeout issues](#windows-hcsshim-timeout-issues)


## Requirements

The common requirements for both Windows and Linux containers are:

- A minimum of 100GB of available disk space
- A minimum of 8GB of available memory
- [Python](https://www.python.org/) 3.x with `pip`
- The dependency packages listed in [requirements.txt](./requirements.txt), which can be installed by running `pip3 install -r requirements.txt`

Building **Windows containers** also requires:

- Windows 10 Pro/Enterprise or Windows Server 2016
- [Docker For Windows](https://www.docker.com/docker-windows) (under Windows 10) or [Docker EE For Windows Server](https://www.docker.com/docker-windows-server) (under Windows Server 2016)
- Under Windows 10, the Docker daemon must be configured to use Windows containers instead of Linux containers
- The Docker daemon must be configured to increase the maximum container disk size from the default 20GB limit by following [the instructions provided by Microsoft](https://docs.microsoft.com/en-us/visualstudio/install/build-tools-container#step-4-expand-maximum-container-disk-size). The 120GB limit specified in the instructions is sufficient.

Building **Linux containers** also requires:

- Windows 10 Pro/Enterprise, Linux or macOS
- [Docker For Windows](https://www.docker.com/docker-windows) (under Windows 10), [Docker CE](https://www.docker.com/community-edition) (under Linux) or [Docker For Mac](https://www.docker.com/docker-mac) (under macOS)
- Under Windows 10, the Docker daemon must be configured to use Linux containers instead of Windows containers
- Under Windows 10 and macOS, Docker must be configured in the "Advanced" settings pane to allocate 8GB of memory and a maximum disk image size of 120GB


## Build script usage

### Building images

First, ensure you have installed the dependencies of the Python build script by running `pip3 install -r requirements.txt`. (You may need to prefix this command with `sudo` under Linux and macOS.)

Then, simply invoke the build script by specifying the UE4 release that you would like to build using full [semver](https://semver.org/) version syntax. For example, to build Unreal Engine 4.19.1:

```
python3 build.py 4.19.1
```

*(Note that you may need to replace the command `python3` with `python` under Windows.)*

You will be prompted for the Git credentials to be used when cloning the UE4 GitHub repository (this will be the GitHub username and password you normally use when cloning <https://github.com/EpicGames/UnrealEngine>.) The build process will then start automatically, displaying progress output from each of the `docker build` commands that are being run.

Once the build process is complete, you will have five new Docker images on your system (where `RELEASE` is the release that you specified when invoking the build script):

- `adamrehn/ue4-build-prerequisites:latest` - this contains the build prerequisites common to all Engine versions and should be kept in order to speed up subsequent builds of additional Engine versions.
- `adamrehn/ue4-source:RELEASE` - this contains the cloned source code for UE4. This image is separated from the `ue4-build` image to isolate the effects of changing environment variables related to git credentials, so that they don't interfere with the build cache for the subsequent steps.
- `adamrehn/ue4-build:RELEASE` - this contains the source build for UE4.
- `adamrehn/conan-ue4cli:RELEASE` - this extends the source build with [conan-ue4cli](https://github.com/adamrehn/conan-ue4cli) support for building Conan packages that are compatible with UE4. This image will only be built for UE4 versions >= 4.19.0, which is the minimum Engine version required by ue4cli. You can disable the build for this image by specifying `--no-ue4cli` when you run the build script.
- `adamrehn/ue4-package:RELEASE` - this extends the `conan-ue4cli` image and is designed for packaging Shipping builds of UE4 projects. Note that the image simply pre-builds components needed for packaging in order to speed up subsequent build time, and is not required in order to package projects (both the `ue4-build` and `conan-ue4cli` images can be used to package projects, albeit with longer build times.) This image will only be built if the `conan-ue4cli` image is built. You can disable the build for this image by specifying `--no-package` when you run the build script.

### Building Linux container images under Windows

By default, Windows container images are built when running the build script under Windows. To build Linux container images instead, simply specify the `--linux` flag when invoking the build script.

### Performing a dry run

If you would like to see what `docker build` commands will be run without actually building anything, you can specify the `--dry-run` flag when invoking the build script. Execution will proceed as normal, except that all `docker build` commands will be printed to standard output instead of being executed as child processes.

### Upgrading from a previous version

When upgrading to a newer version of the code in this repository, be sure to specify the `--rebuild` flag when invoking the build script. This will ensure all images are rebuilt using the updated Dockerfiles.


## Windows `hcsshim` timeout issues

Recent versions of Docker For Windows may sometimes encounter the error [hcsshim: timeout waiting for notification extra info](https://github.com/Microsoft/hcsshim/issues/152) when building or running Windows containers. At the time of writing, Microsoft have stated that they are aware of the problem, but an official fix is yet to be released.

As a workaround until a proper fix is issued, it seems that altering the memory limit for containers between subsequent invocations of the `docker` command can reduce the frequency with which this error occurs. (Changing the memory limit when using Hyper-V isolation likely forces Docker to provision a new Hyper-V VM, preventing it from re-using an existing one that has become unresponsive.) **Please note that this workaround has been devised based on my own testing under Windows 10 and may not hold true for Windows Server 2016.**

To enable the workaround, specify the `--random-memory` flag when invoking the build script. This will set the container memory limit to a random value between 8GB and 10GB when the build script starts. If a build fails with the `hcsshim` timeout error, simply re-run the build script and in most cases the build will continue successfully, even if only for a short while. Restarting the Docker daemon may also help.

Note that in some cases, using a memory limit that is not a multiple of 4GB can cause UnrealBuildTool to crash with an error stating *"The process cannot access the file because it is being used by another process."* If this happens, simply run the build script again without the `--random-memory` flag. If the access error occurs when using the default memory limit, this likely indicates that Windows is unable to allocate the full 8GB to the container. Rebooting the host system may help to alleviate this issue.
