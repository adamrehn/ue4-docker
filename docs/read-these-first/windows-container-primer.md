---
title:  Windows containers primer
pagenum: 3
---

{% include alerts/info.html content="The implementation-agnostic information from this page has migrated to the [Unreal Containers community hub](https://unrealcontainers.com/). You can find the new version here: [Key Concepts: Windows Containers](https://unrealcontainers.com/docs/concepts/windows-containers)." %}

**Details specific to ue4-docker:**

Due to the performance and stability issues currently associated with containers running in Hyper-V isolation mode, it is strongly recommended that process isolation mode be used for building and running Windows containers. This necessitates the use of Windows Server as the host system ([or Windows 10 version 1809 or newer for development and testing purposes](https://docs.microsoft.com/en-us/virtualization/windowscontainers/about/faq#can-i-run-windows-containers-in-process-isolated-mode-on-windows-10-enterprise-or-professional)) and requires that all container images use the same Windows version as the host system. A number of ue4-docker commands provide specific functionality to facilitate this:

- The [ue4-docker build](../commands/build) command will automatically attempt to build images based on the same kernel version as the host system, and will default to process isolation mode if the operating system version and Docker daemon version allow it. Hyper-V isolation mode will still be used if the user explicitly [specifies a different kernel version](../building-images/advanced-build-options#specifying-the-windows-server-core-base-image-tag) than that of the host system or [explicitly requests Hyper-V isolation mode](../building-images/advanced-build-options#specifying-the-isolation-mode-under-windows).

- The [ue4-docker setup](../commands/setup) command automates the configuration of Windows Server hosts, in order to provide a smoother experience for users who migrate their container hosts to the latest versions of Windows Server as they are released.
