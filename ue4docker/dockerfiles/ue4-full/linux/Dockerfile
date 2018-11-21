ARG TAG
FROM adamrehn/ue4-source:${TAG} AS builder

# Install ue4cli and conan-ue4cli
USER root
RUN pip3 install ue4cli conan-ue4cli
USER ue4

# Extract the third-party library details from UBT
RUN ue4 setroot /home/ue4/UnrealEngine
RUN ue4 conan generate

# Copy the generated Conan packages into a new image with our Installed Build
FROM adamrehn/ue4-minimal:${TAG}

# Clone the UE4Capture, and ue4-conan-recipes repositories
RUN git clone "https://github.com/adamrehn/UE4Capture.git" /home/ue4/UE4Capture
RUN git clone "https://github.com/adamrehn/ue4-conan-recipes.git" /home/ue4/ue4-conan-recipes

# Install ue4cli, conan-ue4cli, and the Python requirements for ue4-conan-recipes
USER root
RUN pip3 install ue4cli conan-ue4cli
RUN pip3 install -r /home/ue4/ue4-conan-recipes/requirements.txt
USER ue4

# Copy the Conan configuration settings and package cache from the builder image
COPY --from=builder --chown=ue4:ue4 /home/ue4/.conan /home/ue4/.conan

# Install conan-ue4cli (just generate the profile, since we've already copied the generated packages)
RUN ue4 setroot /home/ue4/UnrealEngine
RUN ue4 conan generate --profile-only

# Build the Conan packages for the UE4Capture dependencies
RUN python3 /home/ue4/ue4-conan-recipes/build.py MediaIPC-ue4

# Patch the problematic UE4 header files under 4.19.x (this call is a no-op under newer Engine versions)
RUN python3 /home/ue4/UE4Capture/scripts/patch-headers.py

# Enable PulseAudio support
USER root
RUN apt-get install -y --no-install-recommends pulseaudio-utils
USER ue4
COPY pulseaudio-client.conf /etc/pulse/client.conf
