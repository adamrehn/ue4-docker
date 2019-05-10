ARG NAMESPACE
ARG TAG
ARG PREREQS_TAG
FROM ${NAMESPACE}/ue4-source:${TAG}-${PREREQS_TAG} AS builder

# Set the changelist number in Build.version to ensure our Build ID is generated correctly
COPY set-changelist.py /tmp/set-changelist.py
RUN python3 /tmp/set-changelist.py /home/ue4/UnrealEngine/Engine/Build/Build.version

# Increase the output verbosity of the DDC generation step
COPY verbose-ddc.py /tmp/verbose-ddc.py
RUN python3 /tmp/verbose-ddc.py /home/ue4/UnrealEngine/Engine/Build/InstalledEngineBuild.xml

# Ensure UBT is built before we create the Installed Build, since Build.sh explicitly sets the
# target .NET framework version, whereas InstalledEngineBuild.xml just uses the system default,
# which can result in errors when running the built UBT due to the wrong version being targeted
RUN ./Engine/Build/BatchFiles/Linux/Build.sh UE4Editor Linux Development -Clean

# Create an Installed Build of the Engine
# (We can optionally remove debug symbols and/or template projects in order to reduce the final container image size)
ARG EXCLUDE_DEBUG
ARG EXCLUDE_TEMPLATES
WORKDIR /home/ue4/UnrealEngine
COPY exclude-components.py /tmp/exclude-components.py
RUN ./Engine/Build/BatchFiles/RunUAT.sh BuildGraph -target="Make Installed Build Linux" -script=Engine/Build/InstalledEngineBuild.xml -set:HostPlatformOnly=true && \
	python3 /tmp/exclude-components.py /home/ue4/UnrealEngine/LocalBuilds/Engine/Linux $EXCLUDE_DEBUG $EXCLUDE_TEMPLATES

# Some versions of the Engine fail to include UnrealPak in the Installed Build, so copy it manually
RUN cp ./Engine/Binaries/Linux/UnrealPak ./LocalBuilds/Engine/Linux/Engine/Binaries/Linux/UnrealPak

# Ensure the bundled toolchain included in 4.20.0 and newer is copied to the Installed Build
COPY --chown=ue4:ue4 copy-toolchain.py /tmp/copy-toolchain.py
RUN python3 /tmp/copy-toolchain.py /home/ue4/UnrealEngine

# Copy the Installed Build into a clean image, discarding the source build
FROM adamrehn/ue4-build-prerequisites:${PREREQS_TAG}

# Copy the Installed Build files from the builder image
COPY --from=builder --chown=ue4:ue4 /home/ue4/UnrealEngine/LocalBuilds/Engine/Linux /home/ue4/UnrealEngine
COPY --from=builder --chown=ue4:ue4 /home/ue4/UnrealEngine/root_commands.sh /tmp/root_commands.sh
WORKDIR /home/ue4/UnrealEngine

# Run the post-setup commands that were previously extracted from `Setup.sh`
USER root
RUN /tmp/root_commands.sh
USER ue4

# Add labels to the built image to identify which components (if any) were excluded from the build that it contains
# (Note that we need to redeclare the relevant ARG directives here because they are scoped to each individual stage in a multi-stage build)
ARG EXCLUDE_DEBUG
ARG EXCLUDE_TEMPLATES
LABEL com.adamrehn.ue4-docker.excluded.debug=${EXCLUDE_DEBUG}
LABEL com.adamrehn.ue4-docker.excluded.templates=${EXCLUDE_TEMPLATES}
