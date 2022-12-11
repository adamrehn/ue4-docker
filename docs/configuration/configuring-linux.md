---
title:  Configuring Linux
pagenum: 2
---

## Requirements

- 64-bit version of one of Docker's [supported Linux distributions](https://docs.docker.com/install/#supported-platforms) (CentOS 7+, Debian 7.7+, Fedora 26+, Ubuntu 14.04+)
- Minimum 8GB of RAM
- Minimum {{ site.data.ue4-docker.common.diskspace_linux | escape }} available disk space for building container images


## Step 1: Install Docker CE

Follow the official installation instructions from the Docker Documentation for your distribution:

- [CentOS](https://docs.docker.com/install/linux/docker-ce/centos/)
- [Debian](https://docs.docker.com/install/linux/docker-ce/debian/)
- [Fedora](https://docs.docker.com/install/linux/docker-ce/fedora/)
- [Ubuntu](https://docs.docker.com/install/linux/docker-ce/ubuntu/)

Once Docker is installed, follow the instructions from the [Post-installation steps for Linux](https://docs.docker.com/install/linux/linux-postinstall/#manage-docker-as-a-non-root-user) page of the Docker Documentation to allow Docker commands to be run by a non-root user. This step is required in order to enable audio support when performing cloud rendering using the NVIDIA Container Toolkit.


## Step 2: Install Python 3.6 or newer

{% capture _alert_content %}
Note that older versions of these Linux distributions may not have Python 3.6 available in their system repositories by default. When working with an older distribution it may be necessary to configure community repositories that provide newer versions of Python.
{% endcapture %}
{% include alerts/info.html content=_alert_content %}

Under CentOS, run:

{% highlight bash %}
sudo yum install python3 python3-devel python3-pip
{% endhighlight %}

Under Debian and Ubuntu, run:

{% highlight bash %}
sudo apt-get install python3 python3-dev python3-pip
{% endhighlight %}

Under Fedora, run:

{% highlight bash %}
sudo dnf install python3 python3-devel python3-pip
{% endhighlight %}


## Step 3: Install ue4-docker

Install the ue4-docker Python package by running the following command:

{% highlight console %}
sudo pip3 install ue4-docker
{% endhighlight %}


## Step 4: Use ue4-docker to automatically configure the Linux firewall

If the host system is running an active firewall that blocks access to port 9876 (required during the build of the [ue4-source](../building-images/available-container-images#ue4-source) image) then it is necessary to create a firewall rule to permit access to this port. The [ue4-docker setup](../commands/setup) command will detect this scenario and perform the appropriate firewall configuration automatically. Simply run:

{% highlight console %}
sudo ue4-docker setup
{% endhighlight %}

Note that the `iptables-persistent` service will need to be installed for the newly-created firewall rule to persist after the host system reboots.
