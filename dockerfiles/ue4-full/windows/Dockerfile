# escape=`
ARG TAG
FROM adamrehn/ue4-engine:${TAG} AS builder

# Install ue4cli and the prerequisites for conan-ue4cli
RUN git clone "https://github.com/adamrehn/conan-ue4cli.git" C:\conan-ue4cli
RUN pip install -r C:\conan-ue4cli\requirements.txt --no-warn-script-location

# Install conan-ue4cli and extract the third-party library details from UBT
RUN ue4 setroot C:\UnrealEngine
RUN python C:\conan-ue4cli\generate.py

# Copy the generated Conan packages into a new image with our Installed Build
FROM adamrehn/ue4-minimal:${TAG}

# Install ue4cli and the prerequisites for conan-ue4cli
RUN git clone "https://github.com/adamrehn/conan-ue4cli.git" C:\conan-ue4cli
RUN pip install -r C:\conan-ue4cli\requirements.txt --no-warn-script-location

# Copy the Conan configuration settings and package cache from the builder image
COPY --from=builder C:\Users\ContainerAdministrator\.conan C:\Users\ContainerAdministrator\.conan

# Install conan-ue4cli (just generate the profile, since we've already copied the generated packages)
RUN ue4 setroot C:\UnrealEngine
RUN python C:\conan-ue4cli\generate.py --profile-only
