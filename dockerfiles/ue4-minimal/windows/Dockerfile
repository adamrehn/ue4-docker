# escape=`
ARG TAG
ARG PREREQS_TAG
FROM adamrehn/ue4-engine:${TAG} AS builder

# Patch out problematic entries in InstalledEngineFilters.xml introduced in UE4.20.0
COPY patch-filters-xml.py C:\patch-filters-xml.py
RUN python C:\patch-filters-xml.py C:\UnrealEngine\Engine\Build\InstalledEngineFilters.xml

# Create an Installed Build of the Engine
WORKDIR C:\UnrealEngine
RUN .\Engine\Build\BatchFiles\RunUAT.bat BuildGraph -target="Make Installed Build Win64" -script=Engine/Build/InstalledEngineBuild.xml -set:HostPlatformOnly=true

# Copy the Installed Build into a clean image, discarding the source build
FROM adamrehn/ue4-build-prerequisites:${PREREQS_TAG}
COPY --from=builder C:\UnrealEngine\LocalBuilds\Engine\Windows C:\UnrealEngine
WORKDIR C:\UnrealEngine
