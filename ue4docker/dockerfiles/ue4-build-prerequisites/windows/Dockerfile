# escape=`
ARG BASEIMAGE
FROM ${BASEIMAGE}
SHELL ["cmd", "/S", "/C"]

# Add a label so we can easily identify derived images
LABEL com.adamrehn.ue4-docker.sentinel="1"

# Install chocolatey
RUN powershell -NoProfile -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"

# Install Git (make sure we forcibly disable the credential manager)
RUN choco install -y git --params "'/GitOnlyOnPath /NoAutoCrlf /WindowsTerminal /NoShellIntegration /NoCredentialManager'"
RUN git config --system credential.helper ""

# Install 7-Zip, curl, wget, Python 3.x, and the Visual C++ runtime libraries
RUN choco install -y 7zip curl wget python vcredist-all

# Install CMake and add it to the system PATH
RUN choco install -y cmake --installargs "ADD_CMAKE_TO_PATH=System"

# Install our Python dependencies
RUN pip install setuptools wheel --no-warn-script-location

# Download the Visual Studio 2017 Build Tools bootstrapper
RUN curl --progress -L "https://aka.ms/vs/15/release/vs_buildtools.exe" --output %TEMP%\vs_buildtools.exe

# Install the Build Tools workloads and components we need, excluding components with known issues in containers
RUN %TEMP%\vs_buildtools.exe --quiet --wait --norestart --nocache `
	--installPath C:\BuildTools `
	--add Microsoft.VisualStudio.Workload.VCTools;includeRecommended;includeOptional `
	--add Microsoft.VisualStudio.Workload.ManagedDesktopBuildTools;includeRecommended;includeOptional `
	--add Microsoft.VisualStudio.Workload.UniversalBuildTools `
	--add Microsoft.VisualStudio.Workload.NetCoreBuildTools `
	--add Microsoft.VisualStudio.Workload.MSBuildTools `
	--add Microsoft.VisualStudio.Component.NuGet `
	--remove Microsoft.VisualStudio.Component.Windows10SDK.10240 `
	--remove Microsoft.VisualStudio.Component.Windows10SDK.10586 `
	--remove Microsoft.VisualStudio.Component.Windows10SDK.14393 `
	--remove Microsoft.VisualStudio.Component.Windows81SDK `
 || IF "%ERRORLEVEL%"=="3010" EXIT 0

# Install WinDbg, which contains pdbcopy.exe (needed for creating an Installed Build of the Engine)
RUN choco install -y windbg

# Copy pdbcopy.exe to the expected location for UE4 versions prior to the UE-51362 fix (https://issues.unrealengine.com/issue/UE-51362)
RUN echo f | xcopy "C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\pdbcopy.exe" "C:\Program Files (x86)\MSBuild\Microsoft\VisualStudio\v12.0\AppxPackage\PDBCopy.exe" /Q /Y
RUN echo f | xcopy "C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\pdbcopy.exe" "C:\Program Files (x86)\MSBuild\Microsoft\VisualStudio\v14.0\AppxPackage\PDBCopy.exe" /Q /Y

# Install the required DirectX runtime files, since Windows Server Core does not include them
RUN curl --progress -L "https://download.microsoft.com/download/8/4/A/84A35BF1-DAFE-4AE8-82AF-AD2AE20B6B14/directx_Jun2010_redist.exe" --output %TEMP%\directx_redist.exe
RUN start /wait %TEMP%\directx_redist.exe /Q /T:%TEMP% && `
	expand %TEMP%\APR2007_xinput_x64.cab -F:xinput1_3.dll C:\Windows\System32\ && `
	expand %TEMP%\Jun2010_D3DCompiler_43_x64.cab -F:D3DCompiler_43.dll C:\Windows\System32\ && `
	expand %TEMP%\Feb2010_X3DAudio_x64.cab -F:X3DAudio1_7.dll C:\Windows\System32\ && `
	expand %TEMP%\Jun2010_XAudio_x64.cab -F:XAPOFX1_5.dll C:\Windows\System32\ && `
	expand %TEMP%\Jun2010_XAudio_x64.cab -F:XAudio2_7.dll C:\Windows\System32\

# Install the Vulkan runtime library
RUN curl --progress -L "https://sdk.lunarg.com/sdk/download/1.1.73.0/windows/VulkanSDK-1.1.73.0-Installer.exe?Human=true" --output %TEMP%\VulkanSDK.exe
RUN 7z e %TEMP%\VulkanSDK.exe -oC:\Windows\System32 -y RunTimeInstaller\x64\vulkan-1.dll

# Copy the required DirectSound and OpenGL DLL files from the host system (since these ship with Windows and don't have installers)
COPY dsound.dll C:\Windows\System32\dsound.dll
COPY opengl32.dll C:\Windows\System32\opengl32.dll
COPY glu32.dll C:\Windows\System32\glu32.dll
