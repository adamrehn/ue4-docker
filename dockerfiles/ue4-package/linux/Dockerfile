ARG TAG
FROM adamrehn/conan-ue4cli:${TAG}

# Pre-build the components needed for creating Shipping builds of projects using Unreal Automation Tool
# (UAT will build these automatically, but pre-building them will speed up builds that use this image.)
WORKDIR /home/ue4/UnrealEngine
RUN ./Engine/Build/BatchFiles/Linux/Build.sh ShaderCompileWorker Linux Development -WaitMutex
RUN ./Engine/Build/BatchFiles/Linux/Build.sh UnrealPak Linux Development -WaitMutex
RUN ./Engine/Build/BatchFiles/Linux/Build.sh UE4Game Linux Shipping -WaitMutex

# Generate the DDC data for all Engine content
RUN ./Engine/Binaries/Linux/UE4Editor -run=DerivedDataCache -fill -TargetPlatform=Linux
