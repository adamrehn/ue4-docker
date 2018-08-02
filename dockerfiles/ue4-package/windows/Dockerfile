# escape=`
ARG TAG
FROM adamrehn/ue4-build:${TAG}

# Patch out problematic entries in InstalledEngineFilters.xml introduced in UE4.20.0
COPY patch-filters-xml.py C:\patch-filters-xml.py
RUN python C:\patch-filters-xml.py C:\UnrealEngine\Engine\Build\InstalledEngineFilters.xml

# Create an Installed Build of the Engine and direct ue4cli to use it
WORKDIR C:\UnrealEngine
RUN .\Engine\Build\BatchFiles\RunUAT.bat BuildGraph -target="Make Installed Build Win64" -script=Engine/Build/InstalledEngineBuild.xml -set:HostPlatformOnly=true
RUN ue4 setroot C:\UnrealEngine\LocalBuilds\Engine\Windows
