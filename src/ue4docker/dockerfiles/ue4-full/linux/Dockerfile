ARG UE4CLI_VERSION="ue4cli>=0.0.45"
ARG CONAN_UE4CLI_VERSION="git+https://github.com/Greenroom-Robotics/conan-ue4cli@feature/fix-libcxx"
ARG CONAN_VERSION="conan>=1.59.0,<2"
{% if combine %}
FROM source as conan
{% else %}
ARG NAMESPACE="{{ namespace }}""
ARG TAG="{{ tag }}"
ARG PREREQS_TAG="{{ prereqs_tag }}"
FROM ${NAMESPACE}/ue4-source:${TAG}-${PREREQS_TAG} AS conan
{% endif %}
ARG UE4CLI_VERSION
ARG CONAN_UE4CLI_VERSION
ARG CONAN_VERSION

# Install ue4cli and conan-ue4cli
USER root
RUN rm -f /usr/lib/python3.*/EXTERNALLY-MANAGED
RUN pip3 install --ignore-installed  "$CONAN_VERSION" "$UE4CLI_VERSION" "$CONAN_UE4CLI_VERSION"
USER ue4

# Copy in UBT from minimal image, if present (required for `ue4 conan generate` to work on UE5)
ARG UBT_DIR="/home/ue4/UnrealEngine/Engine/Binaries/DotNET"
{% if combine %}
COPY --from=minimal --chown=ue4:ue4 $UBT_DIR/UnrealBuildTool $UBT_DIR/UnrealBuildTool
{% else %}
COPY --from={{ namespace }}/ue4-minimal:{{ tag }}-{{ prereqs_tag }} --chown=ue4:ue4 $UBT_DIR/UnrealBuildTool $UBT_DIR/UnrealBuildTool
{% endif %}

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
ARG CONAN_VERSION

# Install CMake, ue4cli, conan-ue4cli, and ue4-ci-helpers
USER root
RUN rm -f /usr/lib/python3.*/EXTERNALLY-MANAGED

RUN apt-get update && apt-get install -y --no-install-recommends cmake
RUN pip3 install --ignore-installed "$CONAN_VERSION" "$UE4CLI_VERSION" "$CONAN_UE4CLI_VERSION" ue4-ci-helpers
USER ue4

# Explicitly set the configuration directory for ue4cli
# (This prevents things from breaking when using CI/CD systems that override the $HOME environment variable)
ENV UE4CLI_CONFIG_DIR=/home/ue4/.config/ue4cli

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
