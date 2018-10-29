# escape=`
ARG TAG
FROM adamrehn/ue4-engine:${TAG} AS engine
FROM adamrehn/ue4-minimal:${TAG} AS builder

# Copy the full set of third-party libraries from the source build of the Engine
COPY --from=engine C:\UnrealEngine\Engine\Source\ThirdParty C:\UnrealEngine\Engine\Source\ThirdParty

# Install ue4cli and extract the third-party library details from UBT
RUN pip install ue4cli
ENV UE4CLI_SENTINEL_RENAME=1
RUN ue4 libs

# Isolate the final image from the modifications performed during UBT interrogation
FROM adamrehn/ue4-minimal:${TAG}

# Copy the full set of third-party libraries from the source build of the Engine
COPY --from=engine C:\UnrealEngine\Engine\Source\ThirdParty C:\UnrealEngine\Engine\Source\ThirdParty

# Install ue4cli and the prerequisites for conan-ue4cli
RUN git clone "https://github.com/adamrehn/conan-ue4cli.git" C:\conan-ue4cli
RUN pip install -r C:\conan-ue4cli\requirements.txt

# Copy the ue4cli configuration and cached third-party library details from the builder image
COPY --from=builder C:\Users\Administrator\AppData\Roaming\ue4cli C:\Users\Administrator\AppData\Roaming\ue4cli

# Install conan-ue4cli (4.19.0 and newer only, this call is a no-op for older Engine versions)
RUN python C:\conan-ue4cli\generate.py
