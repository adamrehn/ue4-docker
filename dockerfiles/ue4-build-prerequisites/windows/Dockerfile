# escape=`
FROM microsoft/dotnet-framework-build:4.7.1
SHELL ["cmd", "/S", "/C"]

# Install chocolatey
RUN powershell -NoProfile -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"

# Install Git (make sure we disable the credential manager)
RUN choco install -y git --params "'/GitOnlyOnPath /NoAutoCrlf /WindowsTerminal /NoShellIntegration /NoCredentialManager'"

# Install curl and wget
RUN choco install -y curl wget

# Install 7-Zip
RUN choco install -y 7zip

# Install CMake and add it to the system PATH
RUN choco install -y cmake --installargs "ADD_CMAKE_TO_PATH=System"

# Install Python 3.x
RUN choco install -y python

# Download the Visual Studio 2017 Build Tools bootstrapper
RUN curl --progress -L "https://aka.ms/vs/15/release/vs_buildtools.exe" --output %TEMP%\vs_buildtools.exe

# Install the Build Tools, excluding the web tools and those components with known issues in containers
RUN %TEMP%\vs_buildtools.exe --quiet --wait --norestart --nocache `
	--installPath C:\BuildTools `
	--all `
	--remove Microsoft.VisualStudio.Component.Windows10SDK.10240 `
	--remove Microsoft.VisualStudio.Component.Windows10SDK.10586 `
	--remove Microsoft.VisualStudio.Component.Windows10SDK.14393 `
	--remove Microsoft.VisualStudio.Component.Windows81SDK `
	--remove Microsoft.VisualStudio.Workload.WebBuildTools `
 || IF "%ERRORLEVEL%"=="3010" EXIT 0

# Install the required DirectX runtime files, since Windows Server Core does not include them
RUN curl --progress -L "https://download.microsoft.com/download/8/4/A/84A35BF1-DAFE-4AE8-82AF-AD2AE20B6B14/directx_Jun2010_redist.exe" --output %TEMP%\directx_redist.exe
RUN start /wait %TEMP%\directx_redist.exe /Q /T:%TEMP%
RUN expand %TEMP%\APR2007_xinput_x64.cab -F:xinput1_3.dll C:\windows\system32\
