ARG TAG
FROM adamrehn/ue4-package:${TAG}

# Clone the UE4Capture Git repository
WORKDIR /home/ue4
RUN git clone "https://github.com/adamrehn/UE4Capture.git"

# Patch the problematic UE4 header files
WORKDIR /home/ue4/UE4Capture/scripts
RUN python3 ./patch-headers.py

# Build the Conan packages for the UE4Capture dependencies
WORKDIR /home/ue4/UE4Capture/recipes/MediaIPC
RUN python3 ./build.py

# Reset our working directory
WORKDIR /home/ue4/UnrealEngine
