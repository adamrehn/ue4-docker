# escape=`
ARG NAMESPACE
ARG TAG
ARG PREREQS_TAG
FROM ${NAMESPACE}/ue4-source:${TAG}-${PREREQS_TAG} AS builder

# Set the changelist number in Build.version to ensure our Build ID is generated correctly
COPY set-changelist.py C:\set-changelist.py
RUN python C:\set-changelist.py C:\UnrealEngine\Engine\Build\Build.version

# Patch out problematic entries in InstalledEngineFilters.xml introduced in UE4.20.0
COPY patch-filters-xml.py C:\patch-filters-xml.py
RUN python C:\patch-filters-xml.py C:\UnrealEngine\Engine\Build\InstalledEngineFilters.xml

# Create an Installed Build of the Engine
# (We can optionally remove debug symbols and/or template projects in order to reduce the final container image size)
ARG EXCLUDE_DEBUG
ARG EXCLUDE_TEMPLATES
WORKDIR C:\UnrealEngine
COPY exclude-components.py C:\exclude-components.py
RUN .\Engine\Build\BatchFiles\RunUAT.bat BuildGraph -target="Make Installed Build Win64" -script=Engine/Build/InstalledEngineBuild.xml -set:HostPlatformOnly=true && `
	python C:\exclude-components.py C:\UnrealEngine\LocalBuilds\Engine\Windows %EXCLUDE_DEBUG% %EXCLUDE_TEMPLATES%

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

# Add labels to the built image to identify which components (if any) were excluded from the build that it contains
# (Note that we need to redeclare the relevant ARG directives here because they are scoped to each individual stage in a multi-stage build)
ARG EXCLUDE_DEBUG
ARG EXCLUDE_TEMPLATES
LABEL com.adamrehn.ue4-docker.excluded.debug=${EXCLUDE_DEBUG}
LABEL com.adamrehn.ue4-docker.excluded.templates=${EXCLUDE_TEMPLATES}
