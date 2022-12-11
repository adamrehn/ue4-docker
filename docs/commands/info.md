---
title:  ue4-docker info
blurb: Displays information about the host system and Docker daemon.
pagenum: 6
---

{{ page.blurb | escape }}

**Usage syntax:**

{% highlight bash %}
ue4-docker info
{% endhighlight %}

The command will output the following information:

- The ue4-docker version
- The host OS version
- The Docker daemon version
- Whether or not the NVIDIA Container Toolkit is supported under the current host configuration
- The detected configuration value for the maximum image size for Windows containers
- The total amount of detected system memory
- The number of detected physical and logical CPUs
