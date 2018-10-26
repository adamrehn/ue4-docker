ARG TAG
ARG PREREQS_TAG
FROM adamrehn/ue4-package:${TAG} AS builder
FROM adamrehn/ue4-build-prerequisites:${PREREQS_TAG}

# Re-create the non-root user
RUN useradd --create-home --home /home/ue4 --shell /bin/bash ue4
RUN usermod -a -G audio,video ue4
USER ue4

# Copy the Installed Build of the Engine from the builder image
COPY --from=builder --chown=ue4:ue4 /home/ue4/UnrealEngine/LocalBuilds/Engine/Linux /home/ue4/UnrealEngine
COPY --from=builder --chown=ue4:ue4 /home/ue4/UnrealEngine/Engine/Source/ThirdParty /home/ue4/UnrealEngine/Engine/Source/ThirdParty
COPY --from=builder --chown=ue4:ue4 /home/ue4/UnrealEngine/root_commands.sh /tmp/root_commands.sh

# Run the post-setup commands that were previously extracted from `Setup.sh`
USER root
RUN /tmp/root_commands.sh
USER ue4

# Install ue4cli and the prerequisites for conan-ue4cli
RUN git clone "https://github.com/adamrehn/conan-ue4cli.git" /home/ue4/conan-ue4cli
USER root
RUN pip3 install -r /home/ue4/conan-ue4cli/requirements.txt
USER ue4

# Point ue4cli to the root of the Installed Build
ENV UE4CLI_SENTINEL_RENAME=1
RUN ue4 setroot /home/ue4/UnrealEngine

# Install conan-ue4cli (4.19.0 and newer only, this call is a no-op for older Engine versions)
RUN python3 /home/ue4/conan-ue4cli/generate.py
