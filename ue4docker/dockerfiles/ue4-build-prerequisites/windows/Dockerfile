# escape=`
ARG BASEIMAGE
FROM ${BASEIMAGE} AS dlls
SHELL ["cmd", "/S", "/C"]

{% if not disable_labels %}
# Include our sentinel so `ue4-docker clean` can find this intermediate image
LABEL com.adamrehn.ue4-docker.sentinel="1"
{% endif %}

# Create a directory in which to gather the DLL files we need 
RUN mkdir C:\GatheredDlls

# Install 7-Zip, curl, and Python using Chocolatey
# (Note that these need to be separate RUN directives for `choco` to work)
RUN powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
RUN choco install -y 7zip curl && choco install -y python --version=3.7.5

# Copy the required DirectSound/DirectDraw and OpenGL DLL files from the host system (since these ship with Windows and don't have installers)
COPY *.dll C:\GatheredDlls\

# Verify that the DLL files copied from the host can be loaded by the container OS
ARG HOST_VERSION
RUN pip install pywin32
COPY copy.py verify-host-dlls.py C:\
RUN C:\copy.py "C:\GatheredDlls\*.dll" C:\Windows\System32\
RUN python C:\verify-host-dlls.py %HOST_VERSION% C:\GatheredDlls

# Gather the required DirectX runtime files, since Windows Server Core does not include them
RUN curl --progress-bar -L "https://download.microsoft.com/download/8/4/A/84A35BF1-DAFE-4AE8-82AF-AD2AE20B6B14/directx_Jun2010_redist.exe" --output %TEMP%\directx_redist.exe
RUN start /wait %TEMP%\directx_redist.exe /Q /T:%TEMP% && `
	expand %TEMP%\APR2007_xinput_x64.cab -F:xinput1_3.dll C:\GatheredDlls\ && `
	expand %TEMP%\Jun2010_D3DCompiler_43_x64.cab -F:D3DCompiler_43.dll C:\GatheredDlls\ && `
	expand %TEMP%\Feb2010_X3DAudio_x64.cab -F:X3DAudio1_7.dll C:\GatheredDlls\ && `
	expand %TEMP%\Jun2010_XAudio_x64.cab -F:XAPOFX1_5.dll C:\GatheredDlls\ && `
	expand %TEMP%\Jun2010_XAudio_x64.cab -F:XAudio2_7.dll C:\GatheredDlls\

# Gather the Vulkan runtime library
RUN curl --progress-bar -L "https://sdk.lunarg.com/sdk/download/latest/windows/vulkan-runtime-components.zip?u=" --output %TEMP%\vulkan-runtime-components.zip
RUN 7z e %TEMP%\vulkan-runtime-components.zip -oC:\GatheredDlls -y "*\x64\vulkan-1.dll"

# Gather pdbcopy.exe (needed for creating an Installed Build of the Engine)
RUN choco install -y windows-sdk-10-version-1809-windbg
RUN C:\copy.py "C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\pdbcopy.exe" C:\GatheredDlls\

# Copy our gathered DLLs (and pdbcopy.exe) into a clean image to reduce image size
FROM ${BASEIMAGE} as prerequisites
SHELL ["cmd", "/S", "/C"]
COPY --from=dlls C:\GatheredDlls\ C:\Windows\System32\

{% if not disable_labels %}
# Add a sentinel label so we can easily identify all derived images, including intermediate images
LABEL com.adamrehn.ue4-docker.sentinel="1"
{% endif %}

# Enable long path support
RUN reg add HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1 /f

# Install Chocolatey
RUN powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"

# Install the rest of our build prerequisites and clean up afterwards to minimise image size
COPY buildtools-exitcode.py copy.py copy-pdbcopy.py install-prerequisites.bat C:\
RUN C:\install-prerequisites.bat
