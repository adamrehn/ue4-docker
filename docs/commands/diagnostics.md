---
title:  ue4-docker diagnostics
blurb: Runs diagnostics to detect issues with the host system configuration.
pagenum: 4
---

{{ page.blurb | escape }}

**Usage syntax:**

{% highlight bash %}
ue4-docker diagnostics DIAGNOSTIC
{% endhighlight %}

This command can be used to run the following diagnostics:

* TOC
{:toc}


## Checking for the Docker 8GiB filesystem layer bug

Some versions of Docker contain one or more of a series of separate but related bugs that prevent the creation of filesystem layers which are 8GiB in size or larger. This also causes `COPY` directives to fail when copying data in excess of 8GiB in size, [breaking Dockerfile steps during the creation of Installed Builds that contain debug symbols](../building-images/troubleshooting-build-issues#building-the-ue4-minimal-image-fails-on-the-copy---frombuilder-directive-that-copies-the-installed-build-from-the-intermediate-image-into-the-final-image).

This diagnostic tests whether the host system's Docker daemon suffers from this issue, by attempting to build a simple test Dockerfile with an 8GiB filesystem layer:

{% highlight bash %}
ue4-docker diagnostics 8gig
{% endhighlight %}


## Checking for the Windows Host Compute Service (HCS) `storage-opt` bug

Windows Server versions 1903 and 1909 and Windows 10 versions 1903 and 1909 contain [a bug in the Host Compute Service (HCS)](https://github.com/docker/for-win/issues/4100) that prevents users from increasing the maximum allowed image size using Docker's `storage-opt` configuration key. Since Unreal Engine containers require a far higher limit than the default during builds, this bug prevents the [ue4-docker build](./build) command from functioning correctly on affected systems.

This diagnostic tests whether the host system is affected this bug, by attempting to run a container with a non-default `storage-opt` value:

{% highlight bash %}
ue4-docker diagnostics maxsize
{% endhighlight %}


## Checking for container network connectivity issues

This diagnostic tests whether running containers are able to access the internet, resolve DNS entries, and download remote files:

{% highlight bash %}
ue4-docker diagnostics network
{% endhighlight %}
