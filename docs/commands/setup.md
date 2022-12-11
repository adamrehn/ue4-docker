---
title:  ue4-docker setup
blurb: Automatically configures the host system where possible.
pagenum: 7
---

{{ page.blurb | escape }}

**Usage syntax:**

{% highlight bash %}
ue4-docker setup
{% endhighlight %}

This command will automatically configure a Linux or Windows Server host system with the settings required in order to build and run containers produced by ue4-docker.

**Under Linux:**

- If an active firewall is detected then a firewall rule will be created to allow Docker containers to communicate with the host system, which is required during the build of the [ue4-source](../building-images/available-container-images#ue4-source) image.

**Under Windows Server:**

- The Docker daemon will be configured to set the maximum image size for Windows containers to 400GB.
- A Windows Firewall rule will be created to allow Docker containers to communicate with the host system, which is required during the build of the [ue4-source](../building-images/available-container-images#ue4-source) image.
- Under Windows Server Core version 1809 and newer, any required DLL files will be copied to the host system from the [full Windows base image](https://hub.docker.com/_/microsoft-windows). Note that the full base image was only introduced in Windows Server version 1809, so this step will not be performed under older versions of Windows Server.

**Under Windows 10 and macOS** this command will print a message informing the user that automatic configuration is not supported under their platform and that they will need to configure the system manually.
