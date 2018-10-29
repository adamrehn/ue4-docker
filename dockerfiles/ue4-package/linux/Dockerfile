ARG TAG
FROM adamrehn/ue4-build:${TAG} AS builder

# Create an Installed Build of the Engine
WORKDIR /home/ue4/UnrealEngine
RUN ./Engine/Build/BatchFiles/RunUAT.sh BuildGraph -target="Make Installed Build Linux" -script=Engine/Build/InstalledEngineBuild.xml -set:HostPlatformOnly=true

# Some versions of the Engine fail to include UnrealPak in the Installed Build, so copy it manually
RUN cp ./Engine/Binaries/Linux/UnrealPak ./LocalBuilds/Engine/Linux/Engine/Binaries/Linux/UnrealPak

# Copy the Installed Build into a clean image, discarding the source build
FROM adamrehn/ue4-build-prerequisites:${PREREQS_TAG}

# Re-create the non-root user
RUN useradd --create-home --home /home/ue4 --shell /bin/bash ue4
RUN usermod -a -G audio,video ue4
USER ue4

# Copy the Installed Build files from the builder image
COPY --from=builder --chown=ue4:ue4 /home/ue4/UnrealEngine/LocalBuilds/Engine/Linux /home/ue4/UnrealEngine
COPY --from=builder --chown=ue4:ue4 /home/ue4/UnrealEngine/root_commands.sh /tmp/root_commands.sh
WORKDIR /home/ue4/UnrealEngine

# Run the post-setup commands that were previously extracted from `Setup.sh`
USER root
RUN /tmp/root_commands.sh
USER ue4
