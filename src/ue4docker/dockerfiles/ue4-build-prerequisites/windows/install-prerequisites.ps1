$ErrorActionPreference = "stop"

function RunProcessChecked
{
    param ([string] $Cmd, [string[]] $Argv)

    Write-Output "Executing command: $Cmd $Argv"

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
RunProcessChecked "choco" @("install", "--no-progress", "-y", "git.install", "--params", @'
"'/GitOnlyOnPath /NoAutoCrlf /WindowsTerminal /NoShellIntegration /NoCredentialManager'`"
'@)

# pdbcopy.exe from Windows SDK is needed for creating an Installed Build of the Engine
RunProcessChecked "choco" @("install", "--no-progress", "-y", "choco-cleaner", "python", "vcredist-all", "windowsdriverkit10")

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
Invoke-WebRequest -Uri "https://sdk.lunarg.com/sdk/download/1.4.304.0/windows/VulkanRT-1.4.304.0-Components.zip?u=" -OutFile "$env:TEMP\vulkan-runtime-components.zip"
Expand-Archive -Path "$env:TEMP\vulkan-runtime-components.zip" -DestinationPath "$env:TEMP"
Copy-Item -Path "*\x64\vulkan-1.dll" -Destination C:\Windows\System32\

# Clean up any temp files generated during prerequisite installation
Remove-Item -LiteralPath "$env:TEMP" -Recurse -Force
New-Item -Type directory -Path "$env:TEMP"

# This shaves off ~300MB as of 2021-08-31
RunProcessChecked "choco-cleaner" @("--dummy")

# Display a human-readable completion message
Write-Output "Finished installing build prerequisites and cleaning up temporary files."
