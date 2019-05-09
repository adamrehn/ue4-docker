ARG NAMESPACE
ARG TAG
ARG PREREQS_TAG
FROM ${NAMESPACE}/ue4-source:${TAG}-${PREREQS_TAG} AS builder

# Install ue4cli and conan-ue4cli
USER root
RUN pip3 install setuptools wheel
RUN pip3 install ue4cli conan-ue4cli
USER ue4

# Extract the third-party library details from UBT
RUN ue4 setroot /home/ue4/UnrealEngine
RUN ue4 conan generate

# Copy the generated Conan packages into a new image with our Installed Build
FROM ${NAMESPACE}/ue4-minimal:${TAG}-${PREREQS_TAG}

# Clone the UE4Capture repository
RUN git clone "https://github.com/adamrehn/UE4Capture.git" /home/ue4/UE4Capture

# Install CMake, ue4cli, conan-ue4cli, and ue4-ci-helpers
USER root
RUN apt-get update && apt-get install -y --no-install-recommends cmake
RUN pip3 install setuptools wheel
RUN pip3 install ue4cli conan-ue4cli ue4-ci-helpers
USER ue4

# Copy the Conan configuration settings and package cache from the builder image
COPY --from=builder --chown=ue4:ue4 /home/ue4/.conan /home/ue4/.conan

# Install conan-ue4cli (just generate the profile, since we've already copied the generated packages)
RUN ue4 setroot /home/ue4/UnrealEngine
RUN ue4 conan generate --profile-only

# Build the Conan packages for the UE4Capture dependencies
RUN ue4 conan build MediaIPC-ue4

# Patch the problematic UE4 header files under 4.19.x (this call is a no-op under newer Engine versions)
RUN python3 /home/ue4/UE4Capture/scripts/patch-headers.py

# Enable PulseAudio support
USER root
RUN apt-get install -y --no-install-recommends pulseaudio-utils
COPY pulseaudio-client.conf /etc/pulse/client.conf

# Enable X11 support
USER root
RUN apt-get install -y --no-install-recommends \
	libfontconfig1 \
	libfreetype6 \
	libglu1 \
	libsm6 \
	libxcomposite1 \
	libxcursor1 \
	libxi6 \
	libxrandr2 \
	libxrender1 \
	libxss1 \
	libxv1 \
	x11-xkb-utils \
	xauth \
	xfonts-base \
	xkb-data
USER ue4
