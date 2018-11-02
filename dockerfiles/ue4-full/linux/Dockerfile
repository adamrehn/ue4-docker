ARG TAG
FROM adamrehn/ue4-engine:${TAG} AS engine
FROM adamrehn/ue4-minimal:${TAG} AS builder

# Copy the full set of third-party libraries from the source build of the Engine
COPY --from=engine --chown=ue4:ue4 /home/ue4/UnrealEngine/Engine/Source/ThirdParty /home/ue4/UnrealEngine/Engine/Source/ThirdParty

# Install ue4cli and the prerequisites for conan-ue4cli
RUN git clone "https://github.com/adamrehn/conan-ue4cli.git" /home/ue4/conan-ue4cli
USER root
RUN pip3 install -r /home/ue4/conan-ue4cli/requirements.txt
USER ue4

# Install conan-ue4cli and extract the third-party library details from UBT
ENV UE4CLI_SENTINEL_RENAME=1
RUN ue4 setroot /home/ue4/UnrealEngine
RUN python3 /home/ue4/conan-ue4cli/generate.py

# Isolate the final image from the modifications performed during UBT interrogation
FROM adamrehn/ue4-minimal:${TAG}

# Clone the conan-ue4cli, UE4Capture, and ue4-conan-recipes repositories
RUN git clone "https://github.com/adamrehn/conan-ue4cli.git" /home/ue4/conan-ue4cli
RUN git clone "https://github.com/adamrehn/UE4Capture.git" /home/ue4/UE4Capture
RUN git clone "https://github.com/adamrehn/ue4-conan-recipes.git" /home/ue4/ue4-conan-recipes

# Install the Python requirements for conan-ue4cli and ue4-conan-recipes
USER root
RUN pip3 install -r /home/ue4/conan-ue4cli/requirements.txt
RUN pip3 install -r /home/ue4/ue4-conan-recipes/requirements.txt
USER ue4

# Copy the Conan configuration settings and package cache from the builder image
COPY --from=builder --chown=ue4:ue4 /home/ue4/.conan /home/ue4/.conan

# Install conan-ue4cli (just generate the profile, since we've already copied the generated packages)
RUN ue4 setroot /home/ue4/UnrealEngine
RUN python3 /home/ue4/conan-ue4cli/generate.py --profile-only

# Build the Conan packages for the UE4Capture dependencies
RUN python3 /home/ue4/ue4-conan-recipes/build.py MediaIPC-ue4

# Patch the problematic UE4 header files under 4.19.x (this call is a no-op under newer Engine versions)
RUN python3 /home/ue4/UE4Capture/scripts/patch-headers.py
