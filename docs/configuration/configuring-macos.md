---
title:  Configuring macOS
pagenum: 5
---

{% capture _alert_content %}
macOS provides a sub-optimal experience when running Linux containers, due to the following factors:

- Linux containers are unable to use GPU acceleration via the [NVIDIA Container Toolkit](../read-these-first/nvidia-docker-primer).
{% endcapture %}
{% include alerts/warning.html content=_alert_content %}


## Requirements

- 2010 or newer model Mac hardware
- macOS 10.10.3 Yosemite or newer
- Minimum 8GB of RAM
- Minimum {{ site.data.ue4-docker.common.diskspace_linux | escape }} available disk space for building container images


## Step 1: Install Docker CE for Mac

Download and install [Docker CE for Mac from the Docker Store](https://store.docker.com/editions/community/docker-ce-desktop-mac).


## Step 2: Install Python 3 via Homebrew

The simplest way to install Python 3 and pip under macOS is to use the [Homebrew package manager](https://brew.sh/). To do so, run the following commands from a Terminal prompt:

{% highlight bash %}
# Install Homebrew
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

# Install Python
brew install python
{% endhighlight %}


## Step 3: Install ue4-docker

Install the ue4-docker Python package by running the following command from a Terminal prompt:

{% highlight console %}
sudo pip3 install ue4-docker
{% endhighlight %}


## Step 4: Manually configure Docker daemon settings

Use [the Advanced section under the Resources tab of the Docker Desktop settings pane](https://docs.docker.com/desktop/mac/#resources) to set the memory allocation for the Moby VM to 8GB and the maximum VM disk image size to {{ site.data.ue4-docker.common.diskspace_linux | escape }}.
