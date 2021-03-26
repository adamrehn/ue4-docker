@rem Install the chocolatey packages we need
choco install -y git --params "'/GitOnlyOnPath /NoAutoCrlf /WindowsTerminal /NoShellIntegration /NoCredentialManager'" || goto :error
choco install -y curl vcredist-all || goto :error
choco install -y python --version=3.7.5 || goto :error

@rem Reload our environment variables from the registry so the `git` command works
call refreshenv
@echo on

@rem Forcibly disable the git credential manager
git config --system credential.helper "" || goto :error

@rem Install the Visual Studio 2017 Build Tools workloads and components we need
@rem (Note that we use the Visual Studio 2019 installer here because the old installer now breaks, but explicitly install the VS2017 Build Tools)
curl --progress -L "https://aka.ms/vs/16/release/vs_buildtools.exe" --output %TEMP%\vs_buildtools.exe || goto :error
%TEMP%\vs_buildtools.exe --quiet --wait --norestart --nocache ^
	--installPath C:\BuildTools ^
	--channelUri "https://aka.ms/vs/15/release/channel" ^
	--installChannelUri "https://aka.ms/vs/15/release/channel" ^
	--channelId VisualStudio.15.Release ^
	--productId Microsoft.VisualStudio.Product.BuildTools ^
	--add Microsoft.VisualStudio.Workload.VCTools ^
	--add Microsoft.VisualStudio.Workload.MSBuildTools ^
	--add Microsoft.VisualStudio.Component.NuGet ^
	--add Microsoft.VisualStudio.Component.Roslyn.Compiler ^
	--add Microsoft.VisualStudio.Component.Windows10SDK.17763 ^
	--add Microsoft.Net.Component.4.5.TargetingPack ^
	--add Microsoft.Net.Component.4.6.2.SDK ^
	--add Microsoft.Net.Component.4.6.2.TargetingPack
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
