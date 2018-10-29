# escape=`
ARG TAG
ARG PREREQS_TAG
FROM adamrehn/ue4-package:${TAG} AS builder
FROM adamrehn/ue4-build-prerequisites:${PREREQS_TAG}

# Copy the Installed Build of the Engine from the builder image
COPY --from=builder C:\UnrealEngine\LocalBuilds\Engine\Windows C:\UnrealEngine
COPY --from=builder C:\UnrealEngine\Engine\Source\ThirdParty C:\UnrealEngine\Engine\Source\ThirdParty

# Install ue4cli and the prerequisites for conan-ue4cli
RUN git clone "https://github.com/adamrehn/conan-ue4cli.git" C:\conan-ue4cli
RUN pip install -r C:\conan-ue4cli\requirements.txt

# Point ue4cli to the root of the Installed Build
RUN ue4 setroot C:\UnrealEngine

# Install conan-ue4cli (4.19.0 and newer only, this call is a no-op for older Engine versions)
ENV UE4CLI_SENTINEL_RENAME=1
RUN python C:\conan-ue4cli\generate.py
