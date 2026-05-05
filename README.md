<p align="center"><img src="https://raw.githubusercontent.com/adamrehn/ue4-docker/master/resources/images/banner.svg?sanitize=true" alt="Unreal Engine and Docker Logos" height="100"></p>
<h1 align="center"><strong>Unreal Engine Docker Containers</strong></h1>
<h3 align="center"><a href="https://unrealcontainers.com/docs/use-cases/continuous-integration">Continuous Integration</a> &bull; <a href="https://unrealcontainers.com/docs/use-cases/pixel-streaming">Pixel Streaming</a> &bull; <a href="https://unrealcontainers.com/docs/use-cases/microservices">Unreal Engine Powered Microservices</a></h3>
<p>&nbsp;</p>

**Looking for a place to start? Check out the [Unreal Containers community hub](https://unrealcontainers.com/) for implementation-agnostic information on using the Unreal Engine inside Docker containers, and then head to the [comprehensive ue4-docker documentation](https://adamrehn.github.io/ue4-docker) to view details specific to using the ue4-docker project.**

The ue4-docker Python package contains a set of Dockerfiles and accompanying build infrastructure that allows you to build Docker images for Epic Games' [Unreal Engine](https://www.unrealengine.com/). The images also incorporate the infrastructure from [ue4cli](https://github.com/adamrehn/ue4cli), [conan-ue4cli](https://github.com/adamrehn/conan-ue4cli), and [ue4-ci-helpers](https://github.com/adamrehn/ue4-ci-helpers) to facilitate a wide variety of use cases.

## Key features

- Both Windows containers and Linux containers are supported.
- Building and packaging Unreal Engine projects is supported.
- Running automation tests is supported.
- Running built Unreal Engine projects with offscreen rendering is supported via the NVIDIA Container Toolkit under Linux.

## Supported engine versions

Unreal Engine 4.27 and five most recent versions of Unreal Engine 5 are supported. 

### 4.27

No known issues.

### 5.2

You need to apply [this fix](https://forums.unrealengine.com/t/need-help-building-5-2-0-from-github/1441996/4) to your engine fork in order to build on Windows.

### 5.3

No known issues.

### 5.4

No known issues.

### 5.5

You need to apply [this patch](https://github.com/EpicGames/UnrealEngine/commit/b86e244161df5bb32030818a48ffeccd3ed310ef) to your engine fork in order to build on Windows.

### 5.6

You need to apply [this](https://github.com/EpicGames/UnrealEngine/commit/467f8b31124c89b61c00ba73c26229897cafd7bd) and [this](https://github.com/EpicGames/UnrealEngine/commit/cdda65cecacd9a1278020925c357bf4cc0b17e8c) patches to your engine fork in order to build on Windows.

## Resources

- **Documentation:** <https://adamrehn.github.io/ue4-docker>
- **GitHub repository:** <https://github.com/adamrehn/ue4-docker>
- **Package on PyPI:** <https://pypi.org/project/ue4-docker>
- **Related articles:** <https://adamrehn.com/articles/tag/Unreal%20Engine/>
- **Unreal Containers community hub:** <https://unrealcontainers.com/>
- **Development channel on the Unreal Containers Community Discord server**: <https://discord.gg/46CJg9fyJ9>


## Contributing

See the file [CONTRIBUTING.adoc](https://github.com/adamrehn/ue4-docker/blob/master/CONTRIBUTING.adoc) for guidelines on how to contribute to the development of ue4-docker.


## Legal

Copyright &copy; 2018 - 2024, Adam Rehn. Licensed under the MIT License, see the file [LICENSE](https://github.com/adamrehn/ue4-docker/blob/master/LICENSE) for details.

Unreal and its logo are Epic Games' trademarks or registered trademarks in the US and elsewhere.

Docker and the Docker logo are trademarks or registered trademarks of Docker in the United States and other countries.
