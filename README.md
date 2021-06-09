<p align="center"><img src="https://raw.githubusercontent.com/adamrehn/ue4-docker/master/resources/images/banner.svg?sanitize=true" alt="Unreal Engine and Docker Logos" height="100"></p>
<h1 align="center"><strong>Unreal Engine 4 Docker Containers</strong></h1>
<h3 align="center"><a href="https://docs.adamrehn.com/ue4-docker/use-cases/continuous-integration">Continuous Integration</a> &bull; <a href="https://docs.adamrehn.com/ue4-docker/use-cases/cloud-rendering">Cloud Rendering</a> &bull; <a href="https://docs.adamrehn.com/ue4-docker/use-cases/microservices">UE4-Powered Microservices</a></h3>
<p>&nbsp;</p>

**Looking for a place to start? Check out the [Unreal Containers community hub](https://unrealcontainers.com/) for implementation-agnostic information on using the Unreal Engine inside Docker containers, and then head to the [comprehensive ue4-docker documentation](https://docs.adamrehn.com/ue4-docker/) to view details specific to using the ue4-docker project.**

The ue4-docker Python package contains a set of Dockerfiles and accompanying build infrastructure that allows you to build Docker images for Epic Games' [Unreal Engine 4](https://www.unrealengine.com/). The images also incorporate the infrastructure from [ue4cli](https://github.com/adamrehn/ue4cli), [conan-ue4cli](https://github.com/adamrehn/conan-ue4cli), and [ue4-ci-helpers](https://github.com/adamrehn/ue4-ci-helpers) to facilitate a wide variety of use cases.

Key features include:

- Unreal Engine 4.20.0 and newer is supported.
- Both Windows containers and Linux containers are supported.
- Building and packaging UE4 projects is supported.
- Running automation tests is supported.
- Running built UE4 projects with offscreen rendering is supported via NVIDIA Docker under Linux.

Resources:

- **Documentation:** <https://docs.adamrehn.com/ue4-docker/>
- **GitHub repository:** <https://github.com/adamrehn/ue4-docker>
- **Package on PyPI:** <https://pypi.org/project/ue4-docker/>
- **Related articles:** <https://adamrehn.com/articles/tag/Unreal%20Engine/>
- **Unreal Containers community hub:** <https://unrealcontainers.com/>
- **Development channel on the Unreal Containers Community Discord server**: <https://discord.gg/46CJg9fyJ9>


## Contributing

See the file [CONTRIBUTING.md](https://github.com/adamrehn/ue4-docker/blob/master/.github/CONTRIBUTING.md) for guidelines on how to contribute to the development of ue4-docker.


## Legal

Copyright &copy; 2018 - 2021, Adam Rehn. Licensed under the MIT License, see the file [LICENSE](https://github.com/adamrehn/ue4-docker/blob/master/LICENSE) for details.

Unreal and its logo are Epic Games' trademarks or registered trademarks in the US and elsewhere.

Docker and the Docker logo are trademarks or registered trademarks of Docker in the United States and other countries.
