---
title:  Large container images primer
pagenum: 2
---

Although large container images are in no way different to smaller container images at a technical level, there are several aspects of the Docker build process that impact large images to a far greater extent than smaller images. This page provides an overview for users who have never built large (multi-gigabyte) container images before and may therefore be unfamiliar with these impacts. This information applies equally to both Linux containers and Windows containers.


## Filesystem layer commit performance

The time taken to commit filesystem layers to disk when building smaller Docker images is low enough that many users may not even perceive this process as a distinct aspect of a `RUN` step in a Dockerfile. However, when a step generates a filesystem layer that is multiple gigabytes in size, the time taken to commit this data to disk becomes immediately noticeable. For some of the larger layers in the container images built by ue4-docker, the filesystem layer commit process can take well over 40 minutes to complete on consumer-grade hardware. (The Installed Build layer in the the multi-stage build of the [ue4-minimal](../building-images/available-container-images#ue4-minimal) image is the largest of all the filesystem layers, and has been observed to take well over an hour and a half to commit to disk on some hardware.)

Since Docker does not emit any output during the layer commit process, users may become concerned that the build has hung. After the ue4-docker provided output `Performing filesystem layer commit...`, the only indication that any processing is taking place is the high quantity of CPU usage and disk I/O present during this stage. There is no need for concern, as none of the steps in the ue4-docker Dockerfiles can run indefinitely without failing and emitting an error. When a build step ceases to produce output, it is merely a matter of waiting for the filesystem layer commit to complete.


## Disk space consumption during the build process

Due to overheads associated with temporary layers in multi-stage builds and layer difference computation, the Docker build process for an image will consume more disk space than is required to hold the final built image. These overheads are relatively modest when building smaller container images. However, these overheads are exacerbated significantly when building large container images, and it is important to be aware of the quantity of available disk space that is required to build any given image or set of images.

Although none of the container images produced by ue4-docker currently exceed 100GB in size, the build process requires at least {{ site.data.ue4-docker.common.diskspace_linux | escape }} of available disk space under Linux and at least {{ site.data.ue4-docker.common.diskspace_windows | escape }} of available disk space under Windows. Once a build is complete, the [ue4-docker clean](../commands/clean) command can be used to clean up temporary layers leftover from multi-stage builds and reclaim all of the disk space not occupied by the final built images. The [docker system prune](https://docs.docker.com/engine/reference/commandline/system_prune/) command can also be useful for cleaning up data that is not used by any of the tagged images present on the system.
