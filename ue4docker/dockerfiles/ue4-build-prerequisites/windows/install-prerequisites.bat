@rem Install the chocolatey packages we need
choco install -y git --params "'/GitOnlyOnPath /NoAutoCrlf /WindowsTerminal /NoShellIntegration /NoCredentialManager'" || goto :error
@rem pdbcopy.exe from Windows SDK is needed for creating an Installed Build of the Engine
choco install -y curl vcredist-all windows-sdk-10-version-1809-windbg || goto :error
choco install -y python --version=3.7.5 || goto :error

@rem Reload our environment variables from the registry so the `git` command works
call refreshenv
@echo on

@rem Forcibly disable the git credential manager
git config --system credential.helper "" || goto :error

@rem Gather the required DirectX runtime files, since Windows Server Core does not include them
curl --progress-bar -L "https://download.microsoft.com/download/8/4/A/84A35BF1-DAFE-4AE8-82AF-AD2AE20B6B14/directx_Jun2010_redist.exe" --output %TEMP%\directx_redist.exe && ^
start /wait %TEMP%\directx_redist.exe /Q /T:%TEMP% && ^
expand %TEMP%\APR2007_xinput_x64.cab -F:xinput1_3.dll C:\Windows\System32\ && ^
expand %TEMP%\Jun2010_D3DCompiler_43_x64.cab -F:D3DCompiler_43.dll C:\Windows\System32\ && ^
expand %TEMP%\Feb2010_X3DAudio_x64.cab -F:X3DAudio1_7.dll C:\Windows\System32\ && ^
expand %TEMP%\Jun2010_XAudio_x64.cab -F:XAPOFX1_5.dll C:\Windows\System32\ && ^
expand %TEMP%\Jun2010_XAudio_x64.cab -F:XAudio2_7.dll C:\Windows\System32\ || goto :error

@rem Retrieve the DirectX shader compiler files needed for DirectX Raytracing (DXR)
curl --progress -L "https://github.com/microsoft/DirectXShaderCompiler/releases/download/v1.6.2104/dxc_2021_04-20.zip" --output %TEMP%\dxc.zip && ^
powershell -Command "Expand-Archive -Path \"$env:TEMP\dxc.zip\" -DestinationPath $env:TEMP" && ^
xcopy /y %TEMP%\bin\x64\dxcompiler.dll C:\Windows\System32\ && ^
xcopy /y %TEMP%\bin\x64\dxil.dll C:\Windows\System32\ || goto :error

@rem Gather the Vulkan runtime library
curl --progress-bar -L "https://sdk.lunarg.com/sdk/download/latest/windows/vulkan-runtime-components.zip?u=" --output %TEMP%\vulkan-runtime-components.zip && ^
powershell -Command "Expand-Archive -Path \"$env:TEMP\vulkan-runtime-components.zip\" -DestinationPath $env:TEMP" && ^
powershell -Command "Copy-Item -Path \"*\x64\vulkan-1.dll\" -Destination C:\Windows\System32" || goto :error

set VISUAL_STUDIO_BUILD_NUMBER=%~1

@rem Install the Visual Studio Build Tools workloads and components we need
@rem NOTE: We use the Visual Studio 2019 installer even for Visual Studio 2017 here because the old installer now breaks
@rem NOTE: VS2019 Build Tools doesn't have 4.6.2 .NET SDK and what actually gets installed is 4.8
@rem NOTE: Microsoft.NetCore.Component.SDK only exists for VS2019. And it is actually *needed* only for UE5
curl --progress-bar -L "https://aka.ms/vs/16/release/vs_buildtools.exe" --output %TEMP%\vs_buildtools.exe || goto :error
%TEMP%\vs_buildtools.exe --quiet --wait --norestart --nocache ^
	--installPath C:\BuildTools ^
	--channelUri "https://aka.ms/vs/%VISUAL_STUDIO_BUILD_NUMBER%/release/channel" ^
	--installChannelUri "https://aka.ms/vs/%VISUAL_STUDIO_BUILD_NUMBER%/release/channel" ^
	--channelId VisualStudio.%VISUAL_STUDIO_BUILD_NUMBER%.Release ^
	--productId Microsoft.VisualStudio.Product.BuildTools ^
	--locale en-US ^
	--add Microsoft.VisualStudio.Workload.VCTools ^
	--add Microsoft.VisualStudio.Workload.MSBuildTools ^
	--add Microsoft.VisualStudio.Component.NuGet ^
	--add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 ^
	--add Microsoft.VisualStudio.Component.Windows10SDK.17763 ^
	--add Microsoft.Net.Component.4.5.TargetingPack ^
	--add Microsoft.Net.ComponentGroup.4.6.2.DeveloperTools ^
	--add Microsoft.NetCore.Component.SDK

python C:\buildtools-exitcode.py %ERRORLEVEL% || goto :error

@rem Clean up any temp files generated during prerequisite installation
rmdir /S /Q \\?\%TEMP%
mkdir %TEMP%

@rem Something that gets installed in ue4-build-prerequisites creates a bogus NuGet config file
@rem Just remove it, so a proper one will be generated on next NuGet run
@rem See https://github.com/adamrehn/ue4-docker/issues/171#issuecomment-852136034
if exist %APPDATA%\NuGet rmdir /s /q %APPDATA%\NuGet

@rem Display a human-readable completion message
@echo off
@echo Finished installing build prerequisites and cleaning up temporary files.
goto :EOF

@rem If any of our essential commands fail, propagate the error code
:error
@echo off
exit /b %ERRORLEVEL%
