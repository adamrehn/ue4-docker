---
title:  ue4-docker build
blurb: Builds container images for a specific version of UE4.
pagenum: 2
---

{{ page.blurb | escape }}

**Usage syntax:**

{% highlight bash %}
ue4-docker build [-h] [--linux] [--rebuild] [--dry-run]
                 [--pull-prerequisites] [--no-engine] [--no-minimal] [--no-full]
                 [--no-cache] [--random-memory]
                 [--exclude {debug,templates}] [--opt OPT] [--cuda VERSION]
                 [-username USERNAME] [-password PASSWORD]
                 [-repo REPO] [-branch BRANCH] [-isolation ISOLATION]
                 [-basetag BASETAG] [-dlldir DLLDIR] [-suffix SUFFIX]
                 [-m M]
                 [-ue4cli UE4CLI] [-conan-ue4cli CONAN_UE4CLI]
                 [-layout LAYOUT] [--combine]
                 [--monitor] [-interval INTERVAL]
                 [--ignore-blacklist]
                 [--visual-studio VISUAL_STUDIO]
                 [-v]
                 release
{% endhighlight %}


## Basic usage

To build container images for a specific version of the Unreal Engine, simply specify the UE4 release that you would like to build using full [semver](https://semver.org/) version syntax. For example, to build Unreal Engine 4.20.3, run:

{% highlight bash %}
ue4-docker build 4.20.3
{% endhighlight %}

You will be prompted for the Git credentials to be used when cloning the UE4 GitHub repository (this will be the GitHub username and password you normally use when cloning <https://github.com/EpicGames/UnrealEngine>.) The build process will then start automatically, displaying progress output from each of the `docker build` commands that are being run in turn.

By default, all available images will be built. See the [List of available container images](../building-images/available-container-images) page for details on customising which images are built.


## Advanced usage

See the [Advanced build options](../building-images/advanced-build-options) page for details on all of the supported flags for customising build behaviour.
