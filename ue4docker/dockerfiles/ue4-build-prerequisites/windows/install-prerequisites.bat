@rem Install the chocolatey packages we need
choco install -y git --params "'/GitOnlyOnPath /NoAutoCrlf /WindowsTerminal /NoShellIntegration /NoCredentialManager'" || goto :error
choco install -y curl vcredist2010 vcredist140 || goto :error
choco install -y python --version=3.7.5 || goto :error

@rem Reload our environment variables from the registry so the `git` command works
call refreshenv
@echo on

@rem Forcibly disable the git credential manager
git config --system credential.helper "" || goto :error

set VISUAL_STUDIO_BUILD_NUMBER=%~1

@rem Install the Visual Studio Build Tools workloads and components we need
@rem NOTE: We use the Visual Studio 2019 installer even for Visual Studio 2017 here because the old installer now breaks
@rem NOTE: VS2019 Build Tools doesn't have 4.6.2 .NET SDK and what actually gets installed is 4.8
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
	--add Microsoft.VisualStudio.Component.Roslyn.Compiler ^
	--add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 ^
	--add Microsoft.VisualStudio.Component.Windows10SDK.17763 ^
	--add Microsoft.Net.Component.4.5.TargetingPack ^
	--add Microsoft.Net.ComponentGroup.4.6.2.DeveloperTools

python C:\buildtools-exitcode.py %ERRORLEVEL% || goto :error

@rem Copy pdbcopy.exe to the expected location(s)
python C:\copy-pdbcopy.py || goto :error

@rem Clean up any temp files generated during prerequisite installation
rmdir /S /Q \\?\%TEMP%
mkdir %TEMP%

@rem Display a human-readable completion message
@echo off
@echo Finished installing build prerequisites and cleaning up temporary files.
goto :EOF

@rem If any of our essential commands fail, propagate the error code
:error
@echo off
exit /b %ERRORLEVEL%
