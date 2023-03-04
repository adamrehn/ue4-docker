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

# Enable PulseAudio support
USER root
RUN apt-get install -y --no-install-recommends pulseaudio-utils
COPY pulseaudio-client.conf /etc/pulse/client.conf
USER ue4
