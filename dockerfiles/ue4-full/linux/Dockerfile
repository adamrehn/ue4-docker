ARG TAG
FROM adamrehn/ue4-engine:${TAG} AS engine
FROM adamrehn/ue4-minimal:${TAG} AS builder

# Copy the full set of third-party libraries from the source build of the Engine
COPY --from=engine --chown=ue4:ue4 /home/ue4/UnrealEngine/Engine/Source/ThirdParty /home/ue4/UnrealEngine/Engine/Source/ThirdParty

# Install ue4cli and extract the third-party library details from UBT
USER root
RUN pip3 install ue4cli
USER ue4
ENV UE4CLI_SENTINEL_RENAME=1
RUN ue4 setroot /home/ue4/UnrealEngine
RUN ue4 libs

# Isolate the final image from the modifications performed during UBT interrogation
FROM adamrehn/ue4-minimal:${TAG}

# Copy the full set of third-party libraries from the source build of the Engine
COPY --from=engine --chown=ue4:ue4 /home/ue4/UnrealEngine/Engine/Source/ThirdParty /home/ue4/UnrealEngine/Engine/Source/ThirdParty

# Install ue4cli and the prerequisites for conan-ue4cli
RUN git clone "https://github.com/adamrehn/conan-ue4cli.git" /home/ue4/conan-ue4cli
USER root
RUN pip3 install -r /home/ue4/conan-ue4cli/requirements.txt
USER ue4

# Copy the ue4cli configuration and cached third-party library details from the builder image
# (Create the parent ~/.config directory first to ensure the ue4 user owns it)
RUN mkdir /home/ue4/.config
COPY --from=builder --chown=ue4:ue4 /home/ue4/.config/ue4cli /home/ue4/.config/ue4cli

# Install conan-ue4cli (4.19.0 and newer only, this call is a no-op for older Engine versions)
RUN python3 /home/ue4/conan-ue4cli/generate.py

# Clone the UE4Capture Git repository
WORKDIR /home/ue4
RUN git clone "https://github.com/adamrehn/UE4Capture.git"

# Patch the problematic UE4 header files under 4.19.x (this call is a no-op under other versions)
WORKDIR /home/ue4/UE4Capture/scripts
RUN python3 ./patch-headers.py

# Build the Conan packages for the UE4Capture dependencies
# (This will fail for Engine versions prior to 4.19, since that is the minimum required version)
WORKDIR /home/ue4/UE4Capture/recipes/MediaIPC
RUN python3 ./build.py

# Reset our working directory
WORKDIR /home/ue4/UnrealEngine
