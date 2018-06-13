# escape=`
ARG TAG
FROM adamrehn/conan-ue4cli:${TAG}

# Pre-build the components needed for creating Shipping builds of projects using Unreal Automation Tool
# (UAT will build these automatically, but pre-building them will speed up builds that use this image.)
WORKDIR C:\UnrealEngine
RUN .\Engine\Build\BatchFiles\Build.bat ShaderCompileWorker Win64 Development -WaitMutex
RUN .\Engine\Build\BatchFiles\Build.bat UnrealPak Win64 Development -WaitMutex
RUN .\Engine\Build\BatchFiles\Build.bat UE4Game Win64 Shipping -WaitMutex

# Generate the DDC data for all Engine content
RUN .\Engine\Binaries\Win64\UE4Editor-Cmd.exe -run=DerivedDataCache -fill -TargetPlatform=Windows
