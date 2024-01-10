$ErrorActionPreference = "stop"

function RunProcessChecked
{
    param ([string] $Cmd, [string[]] $Argv)

    Write-Output "Executing comand: $Cmd $Argv"

    $process = Start-Process -NoNewWindow -PassThru -Wait -FilePath $Cmd -ArgumentList $Argv
    if ($process.ExitCode -ne 0)
    {
        throw "Exit code: $($process.ExitCode)"
    }
}

# TODO: Why `Update-SessionEnvironment` doesn't Just Work without this?
# Taken from https://stackoverflow.com/a/46760714
# Make `Update-SessionEnvironment` available right away, by defining the $env:ChocolateyInstall
# variable and importing the Chocolatey profile module.
$env:ChocolateyInstall = Convert-Path "$( (Get-Command choco).Path )\..\.."
Import-Module "$env:ChocolateyInstall\helpers\chocolateyProfile.psm1"

# Install the chocolatey packages we need
RunProcessChecked "choco" @("install", "--no-progress", "-y", "git", "--params", @'
"'/GitOnlyOnPath /NoAutoCrlf /WindowsTerminal /NoShellIntegration /NoCredentialManager'`"
'@)

# pdbcopy.exe from Windows SDK is needed for creating an Installed Build of the Engine
RunProcessChecked "choco" @("install", "--no-progress", "-y", "choco-cleaner", "python", "vcredist-all", "windows-sdk-10-version-1809-windbg")

# Reload our environment variables from the registry so the `git` command works
Update-SessionEnvironment

# Forcibly disable the git credential manager
RunProcessChecked "git" @("config", "--system", "--unset", "credential.helper")

# Gather the required DirectX runtime files, since Windows Server Core does not include them
Invoke-WebRequest -Uri "https://download.microsoft.com/download/8/4/A/84A35BF1-DAFE-4AE8-82AF-AD2AE20B6B14/directx_Jun2010_redist.exe" -OutFile "$env:TEMP\directx_redist.exe"
RunProcessChecked "$env:TEMP\directx_redist.exe" @("/Q", "/T:$env:TEMP")
RunProcessChecked "expand" @("$env:TEMP\APR2007_xinput_x64.cab", "-F:xinput1_3.dll", "C:\Windows\System32\")
RunProcessChecked "expand" @("$env:TEMP\Jun2010_D3DCompiler_43_x64.cab", "-F:D3DCompiler_43.dll", "C:\Windows\System32\")
RunProcessChecked "expand" @("$env:TEMP\Feb2010_X3DAudio_x64.cab", "-F:X3DAudio1_7.dll", "C:\Windows\System32\")
RunProcessChecked "expand" @("$env:TEMP\Jun2010_XAudio_x64.cab", "-F:XAPOFX1_5.dll", "C:\Windows\System32\")
RunProcessChecked "expand" @("$env:TEMP\Jun2010_XAudio_x64.cab", "-F:XAudio2_7.dll", "C:\Windows\System32\")

# Retrieve the DirectX shader compiler files needed for DirectX Raytracing (DXR)
Invoke-WebRequest -Uri "https://github.com/microsoft/DirectXShaderCompiler/releases/download/v1.6.2104/dxc_2021_04-20.zip" -OutFile "$env:TEMP\dxc.zip"
Expand-Archive -Path "$env:TEMP\dxc.zip" -DestinationPath "$env:TEMP"
Copy-Item -Path "$env:TEMP\bin\x64\dxcompiler.dll" C:\Windows\System32\
Copy-Item -Path "$env:TEMP\bin\x64\dxil.dll" C:\Windows\System32\

# Gather the Vulkan runtime library
Invoke-WebRequest -Uri "https://sdk.lunarg.com/sdk/download/latest/windows/vulkan-runtime-components.zip?u=" -OutFile "$env:TEMP\vulkan-runtime-components.zip"
Expand-Archive -Path "$env:TEMP\vulkan-runtime-components.zip" -DestinationPath "$env:TEMP"
Copy-Item -Path "*\x64\vulkan-1.dll" -Destination C:\Windows\System32\

$visual_studio_build = $args[0]

# Use the latest available Windows SDK. The motivation behind this is:
# 1. Newer SDKs allow developers to use newer APIs. Developers can guard that API usage with runtime version checks if they want to continue to support older Windows releases.
# 2. Unreal Engine slowly moves to newer Windows SDK. 4.27.0 no longer compiles with SDKs older than 18362 and even if it will be fixed in 4.27.x,
#    this is just a question of a time when older SDKs support will be dropped completely
# 3. UE5 doesn't support VS2017 at all, so in the future that argument for continuing to use Windows SDK 17763 from VS2017 era will be weaker and weaker.
#
# We can't use newer SDK for VS2017 that is used to compile older engines because 18362 SDK support was only added in UE-4.23.
#
# See https://github.com/adamrehn/ue4-docker/issues/192
# See https://forums.unrealengine.com/t/ndis_miniport_major_version-is-not-defined-error/135058
# See https://github.com/EpicGames/UnrealEngine/blame/4.23.0-release/Engine/Source/Programs/UnrealBuildTool/Platform/Windows/UEBuildWindows.cs#L1822-L1823
# See https://github.com/EpicGames/UnrealEngine/commit/ecc4872c3269e75a24adc40734cc8bcc9bbed1ca
# See https://udn.unrealengine.com/s/question/0D54z000079HcjJCAS/d3d12h427-error-c4668-winapipartitiongames-is-not-defined-as-a-preprocessor-macro-replacing-with-0-for-ifelif
#
# Keywords for Google:
# error C4668: 'NDIS_MINIPORT_MAJOR_VERSION' is not defined as a preprocessor macro, replacing with '0' for '#if/#elif
# d3d12.h(427): error C4668: 'WINAPI_PARTITION_GAMES' is not defined as a preprocessor macro, replacing with '0' for '#if/#elif'
if ($visual_studio_build -eq "15")
{
    $windows_sdk_version = 17763
}
else
{
    $windows_sdk_version = 20348
}

# NOTE: We use the Visual Studio 2022 installer even for Visual Studio 2019 and 2017 here because the old (2017) installer now breaks
Invoke-WebRequest -Uri "https://aka.ms/vs/17/release/vs_buildtools.exe" -OutFile "$env:TEMP\vs_buildtools.exe"

# NOTE: Microsoft.NetCore.Component.SDK only exists for VS2019+. And it is actually *needed* only for UE5
# NOTE: .NET 4.5 is required for some programs even in UE5, for example https://github.com/EpicGames/UnrealEngine/blob/5.0.1-release/Engine/Source/Programs/UnrealSwarm/SwarmCoordinator/SwarmCoordinator.csproj#L26
# NOTE: Microsoft.NetCore.Component.Runtime.3.1 is required by the AutomationTool tool and does not come installed with VS2022 so it needs targetting here.
$vs_args = @(
    "--quiet",
    "--wait",
    "--norestart",
    "--nocache",
    "--installPath", "C:\BuildTools",
    "--channelUri", "https://aka.ms/vs/$visual_studio_build/release/channel",
    "--installChannelUri", "https://aka.ms/vs/$visual_studio_build/release/channel",
    "--channelId", "VisualStudio.$visual_studio_build.Release",
    "--productId", "Microsoft.VisualStudio.Product.BuildTools",
    "--locale", "en-US",
    "--add", "Microsoft.VisualStudio.Workload.VCTools",
    "--add", "Microsoft.VisualStudio.Workload.MSBuildTools",
    "--add", "Microsoft.VisualStudio.Component.NuGet",
    "--add", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
    "--add", "Microsoft.VisualStudio.Component.Windows10SDK.$windows_sdk_version",
    "--add", "Microsoft.Net.Component.4.5.TargetingPack",
    "--add", "Microsoft.Net.Component.4.6.2.TargetingPack",
    "--add", "Microsoft.Net.ComponentGroup.DevelopmentPrerequisites",
    "--add", "Microsoft.NetCore.Component.SDK",
    "--add", "Microsoft.NetCore.Component.Runtime.3.1"
)

# Install the Visual Studio Build Tools workloads and components we need
RunProcessChecked "$env:TEMP\vs_buildtools.exe" $vs_args

# NOTE: Install the .Net 4.5 Framework Pack via NuGet as it is no longer available via Visual Studio, but still needed
# NOTE: some programs even in UE5, for example https://github.com/EpicGames/UnrealEngine/blob/5.0.1-release/Engine/Source/Programs/UnrealSwarm/SwarmCoordinator/SwarmCoordinator.csproj#L26
Invoke-WebRequest -Uri "https://www.nuget.org/api/v2/package/Microsoft.NETFramework.ReferenceAssemblies.net45/1.0.3" -OutFile "$env:TEMP\DotNet45.zip"
Expand-Archive -Path "$env:TEMP\DotNet45.zip" -DestinationPath "$env:TEMP"
Copy-Item -Path "$env:TEMP\build\.NETFramework\v4.5\*" -Destination "C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.5\" -Recurse -Force

# Clean up any temp files generated during prerequisite installation
Remove-Item -LiteralPath "$env:TEMP" -Recurse -Force
New-Item -Type directory -Path "$env:TEMP"

# This shaves off ~300MB as of 2021-08-31
RunProcessChecked "choco-cleaner" @("--dummy")

# Something that gets installed in ue4-build-prerequisites creates a bogus NuGet config file
# Just remove it, so a proper one will be generated on next NuGet run
# See https://github.com/adamrehn/ue4-docker/issues/171#issuecomment-852136034
if (Test-Path "$env:APPDATA\NuGet")
{
    Remove-Item -LiteralPath "$env:APPDATA\NuGet" -Recurse -Force
}

# Display a human-readable completion message
Write-Output "Finished installing build prerequisites and cleaning up temporary files."
