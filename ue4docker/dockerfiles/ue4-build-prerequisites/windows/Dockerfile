# escape=`
ARG BASEIMAGE
ARG DLLSRCIMAGE

FROM ${DLLSRCIMAGE} as dlls

FROM ${BASEIMAGE} as prerequisites
SHELL ["cmd", "/S", "/C"]

# Gather the system DLLs that we need from the full Windows base image
COPY --from=dlls `
    C:\Windows\System32\avicap32.dll `
    C:\Windows\System32\avifil32.dll `
    C:\Windows\System32\avrt.dll `
    C:\Windows\System32\d3d10warp.dll `
    C:\Windows\System32\D3DSCache.dll `
    C:\Windows\System32\dsound.dll `
    C:\Windows\System32\dxva2.dll `
    C:\Windows\System32\glu32.dll `
    C:\Windows\System32\mf.dll `
    C:\Windows\System32\mfplat.dll `
    C:\Windows\System32\mfplay.dll `
    C:\Windows\System32\mfreadwrite.dll `
    C:\Windows\System32\msacm32.dll `
    C:\Windows\System32\msdmo.dll `
    C:\Windows\System32\msvfw32.dll `
    C:\Windows\System32\opengl32.dll `
    C:\Windows\System32\ResampleDMO.dll `
    C:\Windows\System32\ResourcePolicyClient.dll `
    C:\Windows\System32\

{% if not disable_labels %}
# Add a sentinel label so we can easily identify all derived images, including intermediate images
LABEL com.adamrehn.ue4-docker.sentinel="1"
{% endif %}

# Enable long path support
RUN reg add HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1 /f

# Install Chocolatey
RUN powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"

# Install the rest of our build prerequisites and clean up afterwards to minimise image size
COPY buildtools-exitcode.py install-prerequisites.bat C:\
ARG VISUAL_STUDIO_BUILD_NUMBER
RUN C:\install-prerequisites.bat %VISUAL_STUDIO_BUILD_NUMBER%
