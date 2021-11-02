{% if combine %}
FROM source as builder
{% else %}
ARG NAMESPACE
ARG TAG
ARG PREREQS_TAG
FROM ${NAMESPACE}/ue4-source:${TAG}-${PREREQS_TAG} AS builder
{% endif %}

# Remove the .git directory to disable UBT `git status` calls and speed up the build process
RUN rm -rf /home/ue4/UnrealEngine/.git

# Set the changelist number in Build.version to ensure our Build ID is generated correctly
ARG CHANGELIST
COPY set-changelist.py /tmp/set-changelist.py
RUN python3 /tmp/set-changelist.py /home/ue4/UnrealEngine/Engine/Build/Build.version $CHANGELIST

{% if (not disable_all_patches) and (not disable_opengl_patch) %}
# Enable the OpenGL RHI for Engine versions where it is present but deprecated
COPY enable-opengl.py /tmp/enable-opengl.py
RUN python3 /tmp/enable-opengl.py /home/ue4/UnrealEngine/Engine/Config/BaseEngine.ini
{% endif %}

{% if (not disable_all_patches) and (not disable_buildgraph_patches) %}
COPY patch-filters-xml.py /tmp/patch-filters-xml.py
RUN python3 /tmp/patch-filters-xml.py /home/ue4/UnrealEngine/Engine/Build/InstalledEngineFilters.xml

# Patch the default settings in InstalledEngineBuild.xml and increase the output verbosity of the DDC generation step
COPY patch-build-graph.py /tmp/patch-build-graph.py
RUN python3 /tmp/patch-build-graph.py /home/ue4/UnrealEngine/Engine/Build/InstalledEngineBuild.xml /home/ue4/UnrealEngine/Engine/Build/Build.version
{% endif %}

# Ensure UBT is built before we create the Installed Build, since Build.sh explicitly sets the
# target .NET framework version, whereas InstalledEngineBuild.xml just uses the system default,
# which can result in errors when running the built UBT due to the wrong version being targeted
RUN ./Engine/Build/BatchFiles/Linux/Build.sh UnrealHeaderTool Linux Development -SkipBuild

# Create an Installed Build of the Engine
WORKDIR /home/ue4/UnrealEngine
RUN ./Engine/Build/BatchFiles/RunUAT.sh BuildGraph -target="Make Installed Build Linux" -script=Engine/Build/InstalledEngineBuild.xml -set:HostPlatformOnly=true -set:WithDDC={% if excluded_components.ddc == true %}false{% else %}true{% endif %} {{ buildgraph_args }} && \
	rm -R -f /home/ue4/UnrealEngine/LocalBuilds/InstalledDDC

# Split out components (DDC, debug symbols, template projects) so they can be copied into the final container image as separate filesystem layers
COPY split-components.py /tmp/split-components.py
RUN python3 /tmp/split-components.py /home/ue4/UnrealEngine/LocalBuilds/Engine/Linux /home/ue4/UnrealEngine/Components

{% if (not disable_all_patches) and (not disable_target_patches) %}
# Ensure Client and Server targets have their `PlatformType` field set correctly in BaseEngine.ini
COPY fix-targets.py /tmp/fix-targets.py
RUN python3 /tmp/fix-targets.py /home/ue4/UnrealEngine/LocalBuilds/Engine/Linux/Engine/Config/BaseEngine.ini
{% endif %}

{% if (not disable_all_patches) and (not disable_unrealpak_copy) %}
# Some versions of the Engine fail to include UnrealPak in the Installed Build, so copy it manually
RUN cp ./Engine/Binaries/Linux/UnrealPak ./LocalBuilds/Engine/Linux/Engine/Binaries/Linux/UnrealPak
{% endif %}

{% if (not disable_all_patches) and (not disable_toolchain_copy) %}
# Ensure the bundled toolchain included in 4.20.0 and newer is copied to the Installed Build
COPY --chown=ue4:ue4 copy-toolchain.py /tmp/copy-toolchain.py
RUN python3 /tmp/copy-toolchain.py /home/ue4/UnrealEngine
{% endif %}

# Copy the Installed Build into a clean image, discarding the source build
{% if combine %}
FROM prerequisites as minimal
{% else %}
ARG NAMESPACE
FROM ${NAMESPACE}/ue4-build-prerequisites:${PREREQS_TAG}
{% endif %}

# Copy the Installed Build files from the builder image
COPY --from=builder --chown=ue4:ue4 /home/ue4/UnrealEngine/LocalBuilds/Engine/Linux /home/ue4/UnrealEngine
{% if excluded_components.ddc == false %}
COPY --from=builder --chown=ue4:ue4 /home/ue4/UnrealEngine/Components/DDC /home/ue4/UnrealEngine
{% endif %}
{% if excluded_components.debug == false %}
COPY --from=builder --chown=ue4:ue4 /home/ue4/UnrealEngine/Components/DebugSymbols /home/ue4/UnrealEngine
{% endif %}
{% if excluded_components.templates == false %}
COPY --from=builder --chown=ue4:ue4 /home/ue4/UnrealEngine/Components/TemplatesAndSamples /home/ue4/UnrealEngine
{% endif %}
WORKDIR /home/ue4/UnrealEngine

{% if not disable_labels %}
# Add labels to the built image to identify which components (if any) were excluded from the build that it contains
LABEL com.adamrehn.ue4-docker.excluded.ddc={% if excluded_components.ddc == true %}1{% else %}0{% endif %} 
LABEL com.adamrehn.ue4-docker.excluded.debug={% if excluded_components.debug == true %}1{% else %}0{% endif %} 
LABEL com.adamrehn.ue4-docker.excluded.templates={% if excluded_components.templates == true %}1{% else %}0{% endif %} 
{% endif %}

# Perform first-run setup for Mono, UnrealBuildTool and AutomationTool, which makes it possible to build Unreal projects and plugins as users other than `ue4`
# (Note that this will only work with 4.26.0 and newer, older Engine versions will always require write access to `/home/ue4/UnrealEngine`)
# See the comments on this issue for details, including the need to ensure $HOME is set correctly: <https://github.com/adamrehn/ue4-docker/issues/141>
RUN ./Engine/Build/BatchFiles/Linux/Build.sh UnrealHeaderTool Linux Development -SkipBuild && \
	mkdir -p ./Engine/Programs/AutomationTool/Saved && \
	chmod a+rw ./Engine/Programs/AutomationTool/Saved

# Enable Vulkan support for NVIDIA GPUs
USER root
RUN apt-get update && apt-get install -y --no-install-recommends libvulkan1 && \
	rm -rf /var/lib/apt/lists/* && \
	VULKAN_API_VERSION=`dpkg -s libvulkan1 | grep -oP 'Version: [0-9|\.]+' | grep -oP '[0-9|\.]+'` && \
	mkdir -p /etc/vulkan/icd.d/ && \
	echo \
	"{\
		\"file_format_version\" : \"1.0.0\",\
		\"ICD\": {\
			\"library_path\": \"libGLX_nvidia.so.0\",\
			\"api_version\" : \"${VULKAN_API_VERSION}\"\
		}\
	}" > /etc/vulkan/icd.d/nvidia_icd.json
USER ue4
