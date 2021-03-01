ARG UE4CLI_VERSION="ue4cli>=0.0.45"
ARG CONAN_UE4CLI_VERSION="conan-ue4cli>=0.0.27"
{% if combine %}
FROM source as conan
{% else %}
ARG NAMESPACE
ARG TAG
ARG PREREQS_TAG
FROM ${NAMESPACE}/ue4-source:${TAG}-${PREREQS_TAG} AS conan
{% endif %}
ARG UE4CLI_VERSION
ARG CONAN_UE4CLI_VERSION

# Install ue4cli and conan-ue4cli
USER root
RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install "$UE4CLI_VERSION" "$CONAN_UE4CLI_VERSION"
USER ue4

# Extract the third-party library details from UBT
RUN ue4 setroot /home/ue4/UnrealEngine
RUN ue4 conan generate

# Copy the generated Conan packages into a new image with our Installed Build
{% if combine %}
FROM minimal as full
{% else %}
FROM ${NAMESPACE}/ue4-minimal:${TAG}-${PREREQS_TAG}
{% endif %}
ARG UE4CLI_VERSION
ARG CONAN_UE4CLI_VERSION

# Clone the UE4Capture repository
RUN git clone "https://github.com/adamrehn/UE4Capture.git" /home/ue4/UE4Capture

# Install CMake, ue4cli, conan-ue4cli, and ue4-ci-helpers
USER root
RUN apt-get update && apt-get install -y --no-install-recommends cmake
RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install "$UE4CLI_VERSION" "$CONAN_UE4CLI_VERSION" ue4-ci-helpers
USER ue4

# Explicitly set the configuration directory for ue4cli
# (This prevents things from breaking when using CI/CD systems that override the $HOME environment variable)
ENV UE4CLI_CONFIG_DIR /home/ue4/.config/ue4cli

# Copy the Conan configuration settings and package cache from the previous build stage
COPY --from=conan --chown=ue4:ue4 /home/ue4/.conan /home/ue4/.conan

# Install conan-ue4cli (just generate the profile, since we've already copied the generated packages)
RUN ue4 setroot /home/ue4/UnrealEngine
RUN ue4 conan generate --profile-only

# Build the Conan packages for the UE4Capture dependencies
RUN ue4 conan build MediaIPC-ue4

# Enable PulseAudio support
USER root
RUN apt-get install -y --no-install-recommends pulseaudio-utils
COPY pulseaudio-client.conf /etc/pulse/client.conf

# Enable Vulkan support
RUN apt-get install -y --no-install-recommends libvulkan1 && \
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

# Enable X11 support (including the libraries required by CEF) and xvfb so we can create a dummy display if needed
RUN apt-get install -y --no-install-recommends \
	libasound2 \
	libatk1.0-0 \
	libcairo2 \
	libfontconfig1 \
	libfreetype6 \
	libglu1 \
	libnss3 \
	libnspr4 \
	libpango-1.0-0 \
	libpangocairo-1.0-0 \
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
	xkb-data \
	xvfb
USER ue4
