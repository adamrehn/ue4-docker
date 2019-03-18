# escape=`
ARG TAG
ARG PREREQS_TAG
FROM adamrehn/ue4-source:${TAG}-${PREREQS_TAG} AS builder

# Set the changelist number in Build.version to ensure our Build ID is generated correctly
COPY set-changelist.py C:\set-changelist.py
RUN python C:\set-changelist.py C:\UnrealEngine\Engine\Build\Build.version

# Patch out problematic entries in InstalledEngineFilters.xml introduced in UE4.20.0
COPY patch-filters-xml.py C:\patch-filters-xml.py
RUN python C:\patch-filters-xml.py C:\UnrealEngine\Engine\Build\InstalledEngineFilters.xml

# Create an Installed Build of the Engine
# (By default we truncate all .pdb files in order to reduce the final container image size)
ARG KEEP_DEBUG=0
WORKDIR C:\UnrealEngine
COPY truncate-pdb-files.py C:\truncate-pdb-files.py
RUN .\Engine\Build\BatchFiles\RunUAT.bat BuildGraph -target="Make Installed Build Win64" -script=Engine/Build/InstalledEngineBuild.xml -set:HostPlatformOnly=true && `
	python C:\truncate-pdb-files.py C:\UnrealEngine\LocalBuilds\Engine\Windows %KEEP_DEBUG%

# Copy our legacy toolchain installation script into the Installed Build
# (This ensures we only need one COPY directive below)
RUN C:\copy.py C:\legacy-toolchain-fix.py C:\UnrealEngine\LocalBuilds\Engine\Windows\

# Copy the Installed Build into a clean image, discarding the source tree
FROM adamrehn/ue4-build-prerequisites:${PREREQS_TAG}
COPY --from=builder C:\UnrealEngine\LocalBuilds\Engine\Windows C:\UnrealEngine
WORKDIR C:\UnrealEngine

# Install legacy toolchain components if we're building UE4.19
# (This call is a no-op under newer Engine versions)
RUN python C:\UnrealEngine\legacy-toolchain-fix.py
