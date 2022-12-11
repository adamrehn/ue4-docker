---
title:  Configuring Windows 10 and 11
pagenum: 4
---

{% capture _alert_content %}
Windows 10 and 11 provide an optimal experience when running Windows containers, but **only when process isolation mode is used**. Using [Hyper-V isolation mode](https://docs.microsoft.com/en-us/virtualization/windowscontainers/manage-containers/hyperv-container) will result in a sub-optimal experience due to [several issues that impact performance and stability](../read-these-first/windows-container-primer). The default isolation mode depends on the specific version of Windows being used:

- Under Windows 10, Hyper-V isolation mode is the default isolation mode and [process isolation mode must manually enabled](https://docs.microsoft.com/en-us/virtualization/windowscontainers/about/faq#can-i-run-windows-containers-in-process-isolated-mode-on-windows-10-) each time a container is built or run. The [ue4-docker build](../commands/build) command will automatically pass the flag to enable process isolation mode where possible. **This requires Windows 10 version 1809 or newer.**

- Under Windows 11, process isolation mode is the default isolation mode.
{% endcapture %}
{% include alerts/warning.html content=_alert_content %}


## Requirements

- 64-bit Windows 10 Pro, Enterprise, or Education (Version 1607 or newer)
- Hardware-accelerated virtualisation enabled in the system BIOS/EFI
- Minimum 8GB of RAM
- Minimum {{ site.data.ue4-docker.common.diskspace_windows | escape }} available disk space for building container images


## Step 1: Install Docker CE for Windows

Download and install [Docker CE for Windows from the Docker Store](https://store.docker.com/editions/community/docker-ce-desktop-windows).


## Step 2: Install Python 3 via Chocolatey

The simplest way to install Python and pip under Windows is to use the [Chocolatey package manager](https://chocolatey.org/). To do so, run the following command from an elevated PowerShell prompt:

{% highlight powershell %}
Set-ExecutionPolicy Bypass -Scope Process -Force;
iex ((New-Object System.Net.WebClient).DownloadString(
	'https://chocolatey.org/install.ps1'
))
{% endhighlight %}

You may need to restart your shell for it to recognise the updates that the Chocolatey installer makes to the system `PATH` environment variable. Once these changes are recognised, you can install Python by running the following command from either an elevated PowerShell prompt or an elevated Command Prompt:

{% highlight powershell %}
choco install -y python
{% endhighlight %}


## Step 3: Install ue4-docker

Install the ue4-docker Python package by running the following command from an elevated Command Prompt:

{% highlight console %}
pip install ue4-docker
{% endhighlight %}


## Step 4: Manually configure Docker daemon settings

For building and running Windows containers:

- Configure the Docker daemon to [use Windows containers](https://docs.docker.com/desktop/windows/#switch-between-windows-and-linux-containers) rather than Linux containers.
- Configure the Docker daemon to increase the maximum container disk size from the default 20GB limit by following [the instructions provided by Microsoft](https://docs.microsoft.com/en-us/virtualization/windowscontainers/manage-containers/container-storage#storage-limits). The 120GB limit specified in the instructions is not quite enough, so set a 400GB limit instead. **Be sure to restart the Docker daemon after applying the changes to ensure they take effect.**

{% include alerts/warning.html content="**The ue4-docker maintainers do not provide support for building and running Linux containers under Windows**, due to the various technical limitations of the Hyper-V and WSL2 backends for Docker Desktop. (See [this issue](https://github.com/adamrehn/ue4-docker/issues/205) for details of these limitations.) This functionality is still present in ue4-docker for those who choose to use it, but users are solely responsible for troubleshooting any issues they encounter when doing so." %}

For building and running Linux containers:

- Configure the Docker daemon to [use Linux containers](https://docs.docker.com/desktop/windows/#switch-between-windows-and-linux-containers) rather than Windows containers.

- **If you are using the Hyper-V backend** then use [the Advanced section under the Resources tab of the Docker Desktop settings pane](https://docs.docker.com/desktop/windows/#resources) to set the memory allocation for the Moby VM to 8GB and the maximum VM disk image size to {{ site.data.ue4-docker.common.diskspace_linux | escape }}.

- **If you are using the WSL2 backend** then [expand the WSL2 virtual hard disk](https://docs.microsoft.com/en-us/windows/wsl/compare-versions#expanding-the-size-of-your-wsl-2-virtual-hard-disk) to at least {{ site.data.ue4-docker.common.diskspace_linux | escape }}.
