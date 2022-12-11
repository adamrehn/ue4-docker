---
title:  Advanced build options
pagenum: 2
---

## General options


### Performing a dry run

If you would like to see what `docker build` commands will be run without actually building anything, you can specify the `--dry-run` flag when invoking the [ue4-docker build](../commands/build) command. Execution will proceed as normal, but no Git credentials will be requested and all `docker build` commands will be printed to standard output instead of being executed as child processes.


### Specifying a custom namespace for the image tags

If you would like to override the default `adamrehn/` prefix that is used when generating the tags for all built images, you can do so by specifying a custom value using the `UE4DOCKER_TAG_NAMESPACE` environment variable. **Note that this setting does not effect the [ue4-build-prerequisites](../building-images/available-container-images#ue4-build-prerequisites) image**, which always retains its default name in order to maintain compatibility with the [prebuilt version from Docker Hub](#pulling-a-prebuilt-version-of-the-ue4-build-prerequisites-image).


### Specifying Git credentials

The [ue4-docker build](../commands/build) command supports three methods for specifying the credentials that will be used to clone the UE4 Git repository:

- **Command-line arguments**: the `-username` and `-password` command-line arguments can be used to specify the username and password, respectively.

- **Environment variables**: the `UE4DOCKER_USERNAME` and `UE4DOCKER_PASSWORD` environment variables can be used to specify the username and password, respectively. Note that credentials specified via command-line arguments will take precedence over values defined in environment variables.

- **Standard input**: if either the username or password has not been specified via a command-line argument or environment variable then the build command will prompt the user to enter the credential(s) for which values have not already been specified.

Note that the username and password are handled independently, which means you can use different methods to specify the two credentials (e.g. username specified via command-line argument and password supplied via standard input.)

Users who have enabled [Two-Factor Authentication (2FA)](https://help.github.com/en/articles/about-two-factor-authentication) for their GitHub account will need to generate a [personal access token](https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line) and use that in place of their password.


### Building a custom version of the Unreal Engine

If you would like to build a custom version of UE4 rather than one of the official releases from Epic, you can specify "custom" as the release string and specify the Git repository and branch/tag that should be cloned. When building a custom Engine version, **both the repository URL and branch/tag must be specified**:

{% highlight bash %}
ue4-docker build custom -repo=https://github.com/MyUser/UnrealEngine.git -branch=MyBranch
{% endhighlight %}

This will produce images tagged `adamrehn/ue4-source:custom`, `adamrehn/ue4-engine:custom`, etc.

If you are performing multiple custom builds and wish to differentiate between them, it is recommended to also specify a name for the custom build:

{% highlight bash %}
ue4-docker build custom:my-custom-build -repo=https://github.com/MyUser/UnrealEngine.git -branch=MyBranch
{% endhighlight %}

This will produce images tagged `adamrehn/ue4-source:my-custom-build`, `adamrehn/ue4-engine:my-custom-build`, etc.


### Pulling a prebuilt version of the `ue4-build-prerequisites` image

If you would like to pull the [prebuilt version](https://hub.docker.com/r/adamrehn/ue4-build-prerequisites) of the [ue4-build-prerequisites](../building-images/available-container-images#ue4-build-prerequisites) image from Docker Hub instead of building it locally, simply specify the `--pull-prerequisites` flag when invoking the [ue4-docker build](../commands/build) command. This is primarily useful when building images under versions of Windows Server Core prior to Windows Server 2019, since using the prebuilt image allows you to avoid [copying the required DLL files from Windows 10](../configuration/configuring-windows-server#step-5-copy-required-dll-files-windows-server-core-version-1803-and-older-only). Note however that prebuilt versions of the image are available only for [LTSC versions of Windows](https://docs.microsoft.com/en-us/windows-server/get-started-19/servicing-channels-19), not for SAC versions.


### Excluding Engine components to reduce the final image size

Starting in ue4-docker version 0.0.30, you can use the `--exclude` flag when running the [ue4-docker build](../commands/build) command to specify that certain Engine components should be excluded from the [ue4-minimal](../building-images/available-container-images#ue4-minimal) and [ue4-full](../building-images/available-container-images#ue4-full) images. The following components can be excluded:

- `ddc`: disables building the DDC for the Engine. This significantly speeds up building the Engine itself but results in far longer cook times when subsequently packaging Unreal projects.

- `debug`: removes all debug symbols from the built images. (When building Windows containers the files are actually truncated instead of removed, so they still exist but have a size of zero bytes. This is done for compatibility reasons.)

- `templates`: removes the template projects and samples that ship with the Engine.

You can specify the `--exclude` flag multiple times to exclude as many components as you like. For example:

{% highlight bash %}
# Excludes both debug symbols and template projects
ue4-docker build 4.21.2 --exclude debug --exclude templates
{% endhighlight %}


### Enabling system resource monitoring during builds

Starting in ue4-docker version 0.0.46, you can use the `--monitor` flag to enable a background thread that will log information about system resource usage (available disk space and memory, CPU usage, etc.) at intervals during the build. You can also use the `-interval` flag to override the default interval of 20 seconds:

{% highlight bash %}
# Logs system resource levels every 20 seconds
ue4-docker build 4.24.2 --monitor

# Logs system resource levels every 5 seconds
ue4-docker build 4.24.2 --monitor -interval=5
{% endhighlight %}


### Exporting generated Dockerfiles

Since ue4-docker version 0.0.78, the [ue4-docker build](../commands/build) command supports a flag called `-layout` that allows the generated Dockerfiles to be exported to a filesystem directory instead of being built. In addition, version 0.0.80 of ue4-docker added support for a flag called `--combine` that allows you to combine multiple generated Dockerfiles into a single Dockerfile that performs a [multi-stage build](https://docs.docker.com/develop/develop-images/multistage-build/). You can use these flags like so:

{% highlight bash %}
# Exports Dockerfiles for all images to the specified filesystem directory
ue4-docker build 4.25.4 -layout "/path/to/Dockerfiles"

# Exports Dockerfiles for all images except the ue4-engine image
ue4-docker build 4.25.4 -layout "/path/to/Dockerfiles" --no-engine

# Exports Dockerfiles for all images except the ue4-engine image and combines them into a single Dockerfile
ue4-docker build 4.25.4 -layout "/path/to/Dockerfiles" --no-engine --combine
{% endhighlight %}

Exporting Dockerfiles is useful for debugging or contributing to the development of ue4-docker itself. You can also use the generated Dockerfiles to build container images independently of ue4-docker, but only under the following circumstances:

- When building Windows container images, you must specify the [advanced option](#advanced-options-for-dockerfile-generation) `source_mode` and set it to `copy`. This generates Dockerfiles that copy the Unreal Engine source code from the host filesystem rather than cloning it from a git repository, thus eliminating the dependency on ue4-docker's credential endpoint to securely provide git credentials and allowing container images to be built without the need for ue4-docker itself.

- When building Linux container images, you must either set the [advanced option](#advanced-options-for-dockerfile-generation) `source_mode` to `copy` as detailed above, or else specify the `credential_mode` option and set it to `secrets`. This generates Dockerfiles that use the Linux-only [BuildKit build secrets](https://docs.docker.com/develop/develop-images/build_enhancements/#new-docker-build-secret-information) functionality to securely provide git credentials, eliminating the dependency on ue4-docker's credential endpoint whilst still facilitating the use of a git repository to provide the Unreal Engine source code.


### Advanced options for Dockerfile generation

{% include alerts/info.html content="Note that option names are all listed with underscores between words below (e.g. `source_mode`), but in some examples you will see dashes used as the delimiter instead (e.g. `source-mode`). **These uses are actually equivalent, since ue4-docker automatically converts any dashes in the option name into underscores.** This is because dashes are more stylistically consistent with command-line flags (and thus preferable in examples), but underscores must be used in the underlying Dockerfile template code since dashes cannot be used in [Jinja identifiers](https://jinja.palletsprojects.com/en/2.11.x/api/#notes-on-identifiers)." title="Title" %}

Since ue4-docker version 0.0.78, the [ue4-docker build](../commands/build) command supports a flag called `--opt` that allows users to directly set the context values passed to the underlying [Jinja templating engine](https://jinja.palletsprojects.com/) used to generate Dockerfiles. Some of these options (such as `source_mode`) can only be used when [exporting generated Dockerfiles](#exporting-generated-dockerfiles), whereas others can be used with the regular ue4-docker build process. **Note that incorrect use of these options can break build behaviour, so only use an option if you have read through both this documentation and the ue4-docker source code itself and understand exactly what that option does.** The following options are supported as of the latest version of ue4-docker:

- **`source_mode`**: *(string)* controls how the [ue4-source](../building-images/available-container-images#ue4-source) Dockerfile obtains the source code for the Unreal Engine. Valid options are:
  
  - `git`: the default mode, whereby the Unreal Engine source code is cloned from a git repository. This is the only mode that can be used when not [exporting generated Dockerfiles](#exporting-generated-dockerfiles).
  
  - `copy`: copies the Unreal Engine source code from the host filesystem. The filesystem path can be specified using the `SOURCE_LOCATION` Docker build argument, and of course must be a child path of the build context.

- **`credential_mode`**: *(string)* controls how the [ue4-source](../building-images/available-container-images#ue4-source) Dockerfile securely obtains credentials for authenticating with remote git repositories when `source_mode` is set to `git`. Valid options are:
  
  - `endpoint`: the default mode, whereby ue4-docker exposes an HTTP endpoint that responds with credentials when presented with a randomly-generated security token, which is injected into the [ue4-source](../building-images/available-container-images#ue4-source) container during the build process by way of a Docker build argument. This mode will not work when [exporting generated Dockerfiles](#exporting-generated-dockerfiles), since the credential endpoint will not be available during the build process.
  
  - `secrets`: **(Linux containers only)** uses [BuildKit build secrets](https://docs.docker.com/develop/develop-images/build_enhancements/#new-docker-build-secret-information) to securely inject the git credentials into the [ue4-source](../building-images/available-container-images#ue4-source) container during the build process.

- **`buildgraph_args`**: *(string)* allows you to specify additional arguments to pass to the [BuildGraph system](https://docs.unrealengine.com/en-US/ProductionPipelines/BuildTools/AutomationTool/BuildGraph/index.html) when creating an Installed Build of the Unreal Engine in the [ue4-minimal](../building-images/available-container-images#ue4-minimal) image.

- **`disable_labels`**: *(boolean)* prevents ue4-docker from applying labels to built container images. This includes the labels which specify the [components excluded from the ue4-minimal image](#excluding-engine-components-to-reduce-the-final-image-size) as well as the sentinel labels that the [ue4-docker clean](../commands/clean) command uses to identify container images, and will therefore break the functionality of that command.

- **`disable_all_patches`**: *(boolean)* disables all of the patches that ue4-docker ordinarily applies to the Unreal Engine source code. This is useful when building a custom fork of the Unreal Engine to which the appropriate patches have already been applied, **but will break the build process when used with a version of the Unreal Engine that requires one or more patches**. It is typically safer to disable individual patches using the specific flag for each patch instead of simply disabling everything:
  
  - **`disable_release_patches`**: *(boolean)* disables the patches that ue4-docker ordinarily applies to versions of the Unreal Engine which are known to contain bugs, such as Unreal Engine 4.25.4. This will obviously break the build process when building these known broken releases, but will have no effect when building other versions of the Unreal Engine.
  
  - **`disable_windows_setup_patch`**: *(boolean)* prevents ue4-docker from patching `Setup.bat` under Windows to comment out the calls to the Unreal Engine prerequisites installer and UnrealVersionSelector, both of which are known to cause issues during the build process for Windows containers.
  
  - **`disable_linker_fixup`**: *(boolean)* prevents ue4-docker from replacing the linker in the Unreal Engine's bundled toolchain with a symbolic link to the system linker under Linux.
  
  - **`disable_example_platform_cleanup`**: *(boolean)* prevents ue4-docker from removing the `Engine/Platforms/XXX` directory that was introduced in Unreal Engine 4.24.0 and subsequently removed in Unreal Engine 4.26.0. This directory represents a "dummy" target platform for demonstration purposes, and the presence of this directory will typically break the build process.
  
  - **`disable_ubt_patches`**: *(boolean)* disables the patches that ue4-docker ordinarily applies to fix bugs in UnrealBuildTool (UBT) under various versions of the Unreal Engine.
  
  - **`disable_opengl_patch`**: *(boolean)* prevents ue4-docker from attempting to re-enable the OpenGL RHI under Linux for versions of the Unreal Engine in which it is present but deprecated.
  
  - **`disable_buildgraph_patches`**: *(boolean)* disables the patches that ue4-docker ordinarily applies to the BuildGraph XML files used to create an Installed Build of the Unreal Engine. These patches fix various bugs under both Windows and Linux across multiple versions of the Unreal Engine.
  
  - **`disable_target_patches`**: *(boolean)* disables the patches that ue4-docker ordinarily applies to fix broken `PlatformType` fields for client and server targets in `BaseEngine.ini` under Unreal Engine versions where these values are set incorrectly.
  
  - **`disable_unrealpak_copy`**: *(boolean)* prevents ue4-docker from ensuring the UnrealPak tool is correctly copied into Installed Builds of the Unreal Engine under Linux. Some older versions of the Unreal Engine did not copy this correctly, breaking the functionality of created Installed Builds.
  
  - **`disable_toolchain_copy`**: *(boolean)* prevents ue4-docker from ensuring the bundled clang toolchain is correctly copied into Installed Builds of the Unreal Engine under Linux. Some older versions of the Unreal Engine did not copy this correctly, breaking the functionality of created Installed Builds.


## Windows-specific options


### Specifying the Windows Server Core base image tag

{% capture _alert_content %}
The `-basetag` flag controls how the [ue4-build-prerequisites](../building-images/available-container-images#ue4-build-prerequisites) image is built and tagged, which has a flow-on effect to all of the other images. If you are building multiple related images over separate invocations of the build command (e.g. building the [ue4-source](../building-images/available-container-images#ue4-source) image in one command and then subsequently building the [ue4-minimal](../building-images/available-container-images#ue4-minimal) image in another command), be sure to specify the same `-basetag` flag each time to avoid unintentionally building two sets of unrelated images with different configurations.
{% endcapture %}
{% include alerts/info.html content=_alert_content %}

By default, Windows container images are based on the Windows Server Core release that best matches the version of the host operating system. However, Windows containers cannot run a newer kernel version than that of the host operating system, rendering the latest images unusable under older versions of Windows 10 and Windows Server. (See the [Windows Container Version Compatibility](https://docs.microsoft.com/en-us/virtualization/windowscontainers/deploy-containers/version-compatibility) page for a table detailing which configurations are supported.)

If you are building images with the intention of subsequently running them under an older version of Windows 10 or Windows Server, you will need to build images based on the same kernel version as the target system (or older.) The kernel version can be specified by providing the appropriate base OS image tag via the `-basetag=TAG` flag when invoking the build command:

{% highlight bash %}
ue4-docker build 4.20.3 -basetag=ltsc2016  # Uses Windows Server 2016 (Long Term Support Channel)
{% endhighlight %}

For a list of supported base image tags, see the [Windows Server Core base image on Docker Hub](https://hub.docker.com/r/microsoft/windowsservercore/).


### Specifying the isolation mode under Windows

The isolation mode can be explicitly specified via the `-isolation=MODE` flag when invoking the build command. Valid values are `process` (supported under Windows Server and [Windows 10 version 1809 or newer](https://docs.microsoft.com/en-us/virtualization/windowscontainers/about/faq#can-i-run-windows-containers-in-process-isolated-mode-on-windows-10-enterprise-or-professional)) or `hyperv` (supported under both Windows 10 and Windows Server.) If you do not explicitly specify an isolation mode then the appropriate default for the host system will be used.

### Specifying Visual Studio Build Tools version under Windows

By default, ue4-docker uses Visual Studio Build Tools 2017 to build Unreal Engine.
Starting with Unreal Engine 4.25, you may choose to use Visual Studio Build Tools 2019 instead.
To do so, pass `--visual-studio=2019` flag when invoking the build command.

### Specifying the directory from which to copy required Windows DLL files

By default, DLL files are copied from `%SystemRoot%\System32`. However, when building container images with an older kernel version than the host, the copied DLL files will be too new and the container OS will refuse to load them. A custom directory containing the correct DLL files for the container kernel version can be specified via the `-dlldir=DIR` flag when invoking the build command. 


### Keeping or excluding Installed Build debug symbols under Windows

{% capture _alert_content %}
Excluding debug symbols is necessary under some versions of Docker as a workaround for a bug that limits the amount of data that a `COPY` directive can process to 8GB. See [this section of the Troubleshooting Build Issues page](./troubleshooting-build-issues#building-the-ue4-minimal-image-fails-on-the-copy---frombuilder-directive-that-copies-the-installed-build-from-the-intermediate-image-into-the-final-image) for further details on this issue.
{% endcapture %}
{% include alerts/warning.html content=_alert_content %}

Prior to version 0.0.30, ue4-docker defaulted to truncating all `.pdb` files when building the Installed Build for the [ue4-minimal](../building-images/available-container-images#ue4-minimal) Windows image. This was done primarily to address the bug described in the warning alert above, and also had the benefit of reducing the overall size of the built container images. However, if you required the debug symbols for producing debuggable builds, you had to opt to retain all `.pdb` files by specifying the `--keep-debug` flag when invoking the build command. (This flag was removed in ue4-docker version 0.0.30, when the default behaviour was changed and replaced with a more generic, cross-platform approach.)

Since ue4-docker version 0.0.30, debug symbols are kept intact by default, and can be removed by using the `--exclude debug` flag as described in the section [Excluding Engine components to reduce the final image size](#excluding-engine-components-to-reduce-the-final-image-size).


### Building Linux container images under Windows

By default, Windows container images are built when running the build command under Windows. To build Linux container images instead, simply specify the `--linux` flag when invoking the build command.


## Linux-specific options


### Enabling CUDA support for GPU-enabled Linux images

{% capture _alert_content %}
The `--cuda` flag controls how the [ue4-build-prerequisites](../building-images/available-container-images#ue4-build-prerequisites) image is built and tagged, which has a flow-on effect to all of the other images. If you are building multiple related images over separate invocations of the build command (e.g. building the [ue4-source](../building-images/available-container-images#ue4-source) image in one command and then subsequently building the [ue4-minimal](../building-images/available-container-images#ue4-minimal) image in another command), be sure to specify the same `--cuda` flag each time to avoid unintentionally building two sets of unrelated images with different configurations.
{% endcapture %}
{% include alerts/info.html content=_alert_content %}

By default, the Linux images built by ue4-docker support hardware-accelerated OpenGL when run via the NVIDIA Container Toolkit. If you would like CUDA support in addition to OpenGL support, simply specify the `--cuda` flag when invoking the build command.

You can also control the version of the CUDA base image that is used by appending a version number when specifying the `--cuda` flag, as demonstrated below:

{% highlight bash %}
# Uses the default CUDA base image (currently CUDA 9.2)
ue4-docker build RELEASE --cuda

# Uses the CUDA 10.0 base image
ue4-docker build RELEASE --cuda=10.0
{% endhighlight %}

For a list of supported CUDA versions, see the list of Ubuntu 18.04 image tags for the [nvidia/cudagl](https://hub.docker.com/r/nvidia/cudagl/) base image.
