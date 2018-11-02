# escape=`
ARG TAG
FROM adamrehn/ue4-engine:${TAG} AS engine
FROM adamrehn/ue4-minimal:${TAG} AS builder

# Copy the full set of third-party libraries from the source build of the Engine
COPY --from=engine C:\UnrealEngine\Engine\Source\ThirdParty C:\UnrealEngine\Engine\Source\ThirdParty

# Install ue4cli and the prerequisites for conan-ue4cli
RUN git clone "https://github.com/adamrehn/conan-ue4cli.git" C:\conan-ue4cli
RUN pip install -r C:\conan-ue4cli\requirements.txt

# Install conan-ue4cli and extract the third-party library details from UBT
ENV UE4CLI_SENTINEL_RENAME=1
RUN ue4 setroot C:\UnrealEngine
RUN python C:\conan-ue4cli\generate.py

# Isolate the final image from the modifications performed during UBT interrogation
FROM adamrehn/ue4-minimal:${TAG}

# Install ue4cli and the prerequisites for conan-ue4cli
RUN git clone "https://github.com/adamrehn/conan-ue4cli.git" C:\conan-ue4cli
RUN pip install -r C:\conan-ue4cli\requirements.txt

# Copy the Conan configuration settings and package cache from the builder image
COPY --from=builder C:\Users\ContainerAdministrator\.conan C:\Users\ContainerAdministrator\.conan

# Install conan-ue4cli (just generate the profile, since we've already copied the generated packages)
RUN ue4 setroot C:\UnrealEngine
RUN python C:\conan-ue4cli\generate.py --profile-only
