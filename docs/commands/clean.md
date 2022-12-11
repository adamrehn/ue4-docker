---
title:  ue4-docker clean
blurb: Cleans built container images.
pagenum: 3
---

{{ page.blurb | escape }}

**Usage syntax:**

{% highlight bash %}
ue4-docker clean [-tag TAG] [--source] [--engine] [--all] [--dry-run]
{% endhighlight %}

By default, only dangling intermediate images leftover from ue4-docker multi-stage builds are removed. You can customise this behaviour using these flags:

- `-tag TAG`: Applies a filter for the three flags below, restricting them to removing only images with the specified tag (e.g. `-tag 4.21.0` will only remove images for 4.21.0.)
- `--source`: Removes [ue4-source](../building-images/available-container-images#ue4-source) images, applying the tag filter if one was specified
- `--engine`: Removes [ue4-engine](../building-images/available-container-images#ue4-engine) images, applying the tag filter if one was specified
- `--all`: Removes all ue4-docker images, applying the tag filter if one was specified

If you're unsure as to exactly what images will be removed by a given invocation of the command, append the `--dry-run` flag to have ue4-docker print the generated `docker rmi` commands instead of running them.