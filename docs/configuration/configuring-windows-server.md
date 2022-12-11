---
title:  Configuring Windows Server
pagenum: 3
---

{% capture _alert_content %}
Windows Server provides an optimal experience when running Windows containers, but **only when process isolation mode is used**. Using [Hyper-V isolation mode](https://docs.microsoft.com/en-us/virtualization/windowscontainers/manage-containers/hyperv-container) will result in a sub-optimal experience due to [several issues that impact performance and stability](../read-these-first/windows-container-primer). Process isolation mode is the default isolation mode under Windows Server.
{% endcapture %}
{% include alerts/warning.html content=_alert_content %}


## Requirements

- Windows Server 2016 or newer
- Minimum 8GB of RAM
- Minimum {{ site.data.ue4-docker.common.diskspace_windows | escape }} available disk space for building container images


## Step 1: Install Docker EE

As per the instructions provided by the [Install Docker Engine - Enterprise on Windows Servers](https://docs.docker.com/install/windows/docker-ee/) page of the Docker Documentation, run the following commands from an elevated PowerShell prompt:

{% highlight powershell %}
# Add the Docker provider to the PowerShell package manager
Install-Module DockerMsftProvider -Force

# Install Docker EE
Install-Package Docker -ProviderName DockerMsftProvider -Force

# Restart the computer to enable the containers feature
Restart-Computer
{% endhighlight %}


## Step 2: Install Python 3 via Chocolatey

The simplest way to install Python and pip under Windows is to use the [Chocolatey package manager](https://chocolatey.org/). To do so, run the following command from an elevated PowerShell prompt:

{% highlight powershell %}
Set-ExecutionPolicy Bypass -Scope Process -Force;
iex ((New-Object System.Net.WebClient).DownloadString(
	'https://chocolatey.org/install.ps1'
))
{% endhighlight %}

You may need to restart the system for your shell to recognise the updates that the Chocolatey installer makes to the system `PATH` environment variable. Once these changes are recognised, you can install Python by running the following command from either an elevated PowerShell prompt or an elevated Command Prompt:

{% highlight powershell %}
choco install -y python
{% endhighlight %}


## Step 3: Install ue4-docker

Install the ue4-docker Python package by running the following command from an elevated Command Prompt:

{% highlight console %}
pip install ue4-docker
{% endhighlight %}


## Step 4: Use ue4-docker to automatically configure Docker and Windows Firewall

To automatically configure the required system settings, run the [ue4-docker setup](../commands/setup) command from an elevated Command Prompt:

{% highlight console %}
ue4-docker setup
{% endhighlight %}

This will configure the Docker daemon to set the maximum image size to 400GB, create a Windows Firewall rule to allow Docker containers to communicate with the host system (which is required during the build of the [ue4-source](../building-images/available-container-images#ue4-source) image), and download any required DLL files under Windows Server version 1809 and newer.


## Step 5: Copy required DLL files (Windows Server Core version 1803 and older only)

{% capture _alert_content %}
**This step is only required under when building the [ue4-build-prerequisites](../building-images/available-container-images#ue4-build-prerequisites) image locally under older versions of Windows Server.**

Starting from Windows Server version 1809 (base image tag `ltsc2019`), the [ue4-docker setup](../commands/setup) command will automatically extract the required DLL files from the [full Windows base image](https://hub.docker.com/_/microsoft-windowsfamily-windows). Manual configuration is only required under Windows Server version 1803 and older when you are building the [ue4-build-prerequisites](../building-images/available-container-images#ue4-build-prerequisites) image locally rather than [pulling the prebuilt version](../building-images/advanced-build-options#pulling-a-prebuilt-version-of-the-ue4-build-prerequisites-image).
{% endcapture %}
{% include alerts/info.html content=_alert_content %}

Under Windows Server Core, you will need to copy a number of DLL files from a copy of Windows 10 (or Windows Server [with the Desktop Experience feature](https://docs.microsoft.com/en-us/windows-server/get-started/getting-started-with-server-with-desktop-experience)) and place them in the `C:\Windows\System32` directory. Note that these DLL files must be copied from the **same version of Windows** as the Windows Server Core host system (e.g. Windows Server 1709 needs DLLs from Windows 10 1709, Windows Server 1803 needs DLLs from Windows 10 1803, etc.) Although DLLs from an older system version may potentially work, Windows containers will refuse to load these DLL files if they have been copied from a version of Windows that is newer than the container.

The required DLL files for each version of Windows Server Core are listed in the tables below, along with the minimum and maximum versions of these DLLs that have been tested and are known to work.

{% for server in site.data.ue4-docker.dlls %}
### {{ server.name | escape }} (base image tag `{{ server.basetag | escape }}`)

{::nomarkdown}
{% if server.notes != "" %}
	{% assign content = server.notes | markdownify %}
	{% include alerts/info.html content=content %}
{% endif %}

<table>
	<thead>
		<tr>
			<th>DLL File</th>
			<th>Min Version</th>
			<th>Max Version</th>
		</tr>
	</thead>
	<tbody>
		{% for dll in server.dlls %}
			<tr>
				<td>{{ dll.name | escape }}</td>
				<td>{{ dll.minVersion | escape }}</td>
				<td>{{ dll.maxVersion | escape }}</td>
			</tr>
		{% endfor %}
	</tbody>
</table>
{:/}
{% endfor %}
