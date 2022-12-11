---
title:  List of available container images
pagenum: 1
---

You can build the following images using the [ue4-docker build](../commands/build) command:

* TOC
{:toc}

By default, all available images will be built. You can prevent unwanted images from being built by appending the relevant image-specific flag to the build command (see the *"Flag to disable"* entry for each image below.)


{% for image in site.data.ue4-docker.images %}
## {{ image.name | escape }}

**Tags:**

{% for tag in image.tags %}
- {{ tag }}
{% endfor %}

{::nomarkdown}
<p class="dockerfiles">
	<strong>Dockerfiles:</strong> 
	<a href="{{ site.data.ue4-docker.common.dockerfile_root | uri_escape }}/{{ image.name | uri_escape }}/windows/Dockerfile"><span class="fab fa-windows"></span> Windows</a>
	|
	<a href="{{ site.data.ue4-docker.common.dockerfile_root | uri_escape }}/{{ image.name | uri_escape }}/linux/Dockerfile"><span class="fab fa-linux"></span> Linux</a>
</p>
{:/}

**Flag to disable:** {{ image.disable }}

**Contents:** {{ image.contents }}

**Uses:**

{% for use in image.uses %}- {{ use }}
{% endfor %}

{% endfor %}
