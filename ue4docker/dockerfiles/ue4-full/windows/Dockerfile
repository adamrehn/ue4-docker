# escape=`
ARG NAMESPACE
ARG TAG
ARG PREREQS_TAG
FROM ${NAMESPACE}/ue4-source:${TAG}-${PREREQS_TAG} AS builder

# Install ue4cli and conan-ue4cli
RUN pip install setuptools wheel --no-warn-script-location
RUN pip install "ue4cli>=0.0.41" "conan-ue4cli>=0.0.21" --no-warn-script-location

# Build UBT, and extract the third-party library details from UBT
# (Remove the profile base packages to avoid a bug where Windows locks the files and breaks subsequent profile generation)
RUN GenerateProjectFiles.bat
RUN ue4 setroot C:\UnrealEngine
RUN ue4 conan generate && ue4 conan generate --remove-only

# Copy the generated Conan packages into a new image with our Installed Build
FROM ${NAMESPACE}/ue4-minimal:${TAG}-${PREREQS_TAG}

# Install ue4cli conan-ue4cli, and ue4-ci-helpers
RUN pip install setuptools wheel --no-warn-script-location
RUN pip install "ue4cli>=0.0.41" "conan-ue4cli>=0.0.21" ue4-ci-helpers --no-warn-script-location

# Explicitly set the configuration directory for ue4cli
# (This prevents things from breaking when using CI/CD systems that override the $HOME environment variable)
ENV UE4CLI_CONFIG_DIR C:\Users\ContainerAdministrator\AppData\Roaming\ue4cli

# Copy the Conan configuration settings and package cache from the builder image
COPY --from=builder C:\Users\ContainerAdministrator\.conan C:\Users\ContainerAdministrator\.conan

# Install conan-ue4cli (just generate the profile, since we've already copied the generated packages)
RUN ue4 setroot C:\UnrealEngine
RUN ue4 conan generate --profile-only

# Install CMake and add it to the system PATH
RUN choco install -y cmake --installargs "ADD_CMAKE_TO_PATH=System"
