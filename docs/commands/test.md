---
title:  ue4-docker test
blurb: Runs tests to verify the correctness of built container images.
pagenum: 8
---

{{ page.blurb | escape }}

**Usage syntax:**

{% highlight bash %}
ue4-docker test TAG
{% endhighlight %}

This command runs a suite of tests to verify that built [ue4-full](../building-images/available-container-images#ue4-full) container images are functioning correctly and can be used to build and package Unreal projects and plugins. This command is primarily intended for use by developers who are contributing to the ue4-docker project itself.
