# escape=`
{% if combine %}
FROM source as builder
{% else %}
ARG NAMESPACE
ARG TAG
ARG PREREQS_TAG
FROM ${NAMESPACE}/ue4-source:${TAG}-${PREREQS_TAG} AS builder
{% endif %}

# Remove the .git directory to disable UBT `git status` calls and speed up the build process
RUN rmdir /s /q C:\UnrealEngine\.git

# Set the changelist number in Build.version to ensure our Build ID is generated correctly
COPY set-changelist.py C:\set-changelist.py
RUN python C:\set-changelist.py C:\UnrealEngine\Engine\Build\Build.version

{% if (not disable_all_patches) and (not disable_buildgraph_patches) %}
# Patch out problematic entries in InstalledEngineFilters.xml introduced in UE4.20.0
COPY patch-filters-xml.py C:\patch-filters-xml.py
RUN python C:\patch-filters-xml.py C:\UnrealEngine\Engine\Build\InstalledEngineFilters.xml

# Patch out problematic entries in InstalledEngineBuild.xml introduced in UE4.23.0
COPY patch-build-graph.py C:\patch-build-graph.py
RUN python C:\patch-build-graph.py C:\UnrealEngine\Engine\Build\InstalledEngineBuild.xml
{% endif %}

# Create an Installed Build of the Engine
ARG BUILD_DDC
WORKDIR C:\UnrealEngine
COPY exclude-components.py C:\exclude-components.py
RUN .\Engine\Build\BatchFiles\RunUAT.bat BuildGraph -target="Make Installed Build Win64" -script=Engine/Build/InstalledEngineBuild.xml -set:HostPlatformOnly=true -set:WithDDC=%BUILD_DDC% {{ buildgraph_args }} && `
	(if exist C:\UnrealEngine\LocalBuilds\InstalledDDC rmdir /s /q C:\UnrealEngine\LocalBuilds\InstalledDDC)

# Determine if we are removing debug symbols and/or template projects in order to reduce the final container image size
ARG EXCLUDE_DEBUG
ARG EXCLUDE_TEMPLATES
RUN python C:\exclude-components.py C:\UnrealEngine\LocalBuilds\Engine\Windows %EXCLUDE_DEBUG% %EXCLUDE_TEMPLATES%

{% if (not disable_all_patches) and (not disable_target_patches) %}
# Ensure Client and Server targets have their `PlatformType` field set correctly in BaseEngine.ini
COPY fix-targets.py C:\fix-targets.py
RUN python C:\fix-targets.py C:\UnrealEngine\LocalBuilds\Engine\Windows\Engine\Config\BaseEngine.ini
{% endif %}

# Copy the Installed Build into a clean image, discarding the source tree
{% if combine %}
FROM prerequisites as minimal
{% else %}
FROM adamrehn/ue4-build-prerequisites:${PREREQS_TAG}
{% endif %}
COPY --from=builder C:\UnrealEngine\LocalBuilds\Engine\Windows C:\UnrealEngine
WORKDIR C:\UnrealEngine

{% if not disable_labels %}
# Add labels to the built image to identify which components (if any) were excluded from the build that it contains
# (Note that we need to redeclare the relevant ARG directives here because they are scoped to each individual stage in a multi-stage build)
ARG EXCLUDE_DEBUG
ARG EXCLUDE_TEMPLATES
LABEL com.adamrehn.ue4-docker.excluded.debug=${EXCLUDE_DEBUG}
LABEL com.adamrehn.ue4-docker.excluded.templates=${EXCLUDE_TEMPLATES}
{% endif %}
