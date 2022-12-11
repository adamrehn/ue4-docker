---
title:  Introduction to ue4-docker
pagenum: 1
---

## Overview

The ue4-docker Python package contains a set of Dockerfiles and accompanying build infrastructure that allows you to build Docker images for Epic Games' [Unreal Engine 4](https://www.unrealengine.com/). The images also incorporate the infrastructure from [ue4cli]({{ site.data.common.projects.ue4cli.repo }}), [conan-ue4cli]({{ site.data.common.projects.conan-ue4cli.repo }}), and [ue4-ci-helpers]({{ site.data.common.projects.ue4-ci-helpers.repo }}) to facilitate a wide variety of use cases.

Key features include:

- Unreal Engine 4.20.0 and newer is supported.
- Both Windows containers and Linux containers are supported.
- Building and packaging UE4 projects is supported.
- Running automation tests is supported.
- Running built UE4 projects with offscreen rendering is supported via the NVIDIA Container Toolkit under Linux.


## Important legal notice

**With the exception of the [ue4-build-prerequisites](../building-images/available-container-images#ue4-build-prerequisites) image, the Docker images produced by the ue4-docker Python package contain the UE4 Engine Tools in both source code and object code form. As per Section 1A of the [Unreal Engine EULA](https://www.unrealengine.com/eula), Engine Licensees are prohibited from public distribution of the Engine Tools unless such distribution takes place via the Unreal Marketplace or a fork of the Epic Games UE4 GitHub repository.** {::nomarkdown}<strong class="text-danger">Public distribution of the built images via an openly accessible Docker Registry (e.g. Docker Hub) is a direct violation of the license terms.</strong>{:/} **It is your responsibility to ensure that any private distribution to other Engine Licensees (such as via an organisation's internal Docker Registry) complies with the terms of the Unreal Engine EULA.**

For more details, see the [Unreal Engine EULA Restrictions](https://unrealcontainers.com/docs/obtaining-images/eula-restrictions) page on the [Unreal Containers community hub](https://unrealcontainers.com/).


## Getting started

Multi-purpose Docker images for large, cross-platform projects such as the Unreal Engine involve a great deal more complexity than most typical Docker images. Before you start using ue4-docker it may be helpful to familiarise yourself with some of these complexities:

- If you've never built large (multi-gigabyte) Docker images before, be sure to read the [Large container images primer](./large-container-images-primer).
- If you've never used Windows containers before, be sure to read the [Windows containers primer](./windows-container-primer).
- If you've never used GPU-accelerated Linux containers with the NVIDIA Container Toolkit before, be sure to read the [NVIDIA Container Toolkit primer](./nvidia-docker-primer).

Once you're familiar with all of the relevant background material, you can dive right in:

1. First up, head to the [Configuration](../configuration) section for details on how to install ue4-docker and configure your host system so that it is ready to build and run the Docker images.
2. Next, check out the [Use Cases](../use-cases) section for details on the various scenarios in which the Docker images can be used. Once you've selected the use case you're interested in, you'll find step-by-step instructions on how to build the necessary container images and start using them.
3. If you run into any issues or want to customise your build with advanced options, the [Building Images](../building-images) section provides all of the relevant details.
4. For more information, check out the [FAQ](./frequently-asked-questions) and the [Command Reference](../commands) section.


## Links

- [ue4-docker GitHub repository]({{ site.data.common.projects.ue4-docker.repo }})
- [ue4-docker package on PyPI](https://pypi.org/project/ue4-docker/)
- [Related articles on adamrehn.com](https://adamrehn.com/articles/tag/Unreal%20Engine/)
- [Unreal Containers community hub](https://unrealcontainers.com/)
