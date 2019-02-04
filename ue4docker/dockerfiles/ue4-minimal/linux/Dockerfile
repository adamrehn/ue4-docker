ARG TAG
ARG PREREQS_TAG
FROM adamrehn/ue4-source:${TAG}-${PREREQS_TAG} AS builder

# Increase the output verbosity of the DDC generation step
COPY verbose-ddc.py /tmp/verbose-ddc.py
RUN python3 /tmp/verbose-ddc.py /home/ue4/UnrealEngine/Engine/Build/InstalledEngineBuild.xml

# Ensure UBT is built before we create the Installed Build, since Build.sh explicitly sets the
# target .NET framework version, whereas InstalledEngineBuild.xml just uses the system default,
# which can result in errors when running the built UBT due to the wrong version being targeted
RUN ./Engine/Build/BatchFiles/Linux/Build.sh UE4Editor Linux Development -Clean

# Create an Installed Build of the Engine
WORKDIR /home/ue4/UnrealEngine
RUN ./Engine/Build/BatchFiles/RunUAT.sh BuildGraph -target="Make Installed Build Linux" -script=Engine/Build/InstalledEngineBuild.xml -set:HostPlatformOnly=true

# Some versions of the Engine fail to include UnrealPak in the Installed Build, so copy it manually
RUN cp ./Engine/Binaries/Linux/UnrealPak ./LocalBuilds/Engine/Linux/Engine/Binaries/Linux/UnrealPak

# Ensure the bundled toolchain included in 4.20.0 and newer is copied to the Installed Build
COPY --chown=ue4:ue4 copy-toolchain.py /tmp/copy-toolchain.py
RUN python3 /tmp/copy-toolchain.py /home/ue4/UnrealEngine

# Copy the Installed Build into a clean image, discarding the source build
FROM adamrehn/ue4-build-prerequisites:${PREREQS_TAG}

# Copy the Installed Build files from the builder image
COPY --from=builder --chown=ue4:ue4 /home/ue4/UnrealEngine/LocalBuilds/Engine/Linux /home/ue4/UnrealEngine
COPY --from=builder --chown=ue4:ue4 /home/ue4/UnrealEngine/root_commands.sh /tmp/root_commands.sh
WORKDIR /home/ue4/UnrealEngine

# Run the post-setup commands that were previously extracted from `Setup.sh`
USER root
RUN /tmp/root_commands.sh
USER ue4
