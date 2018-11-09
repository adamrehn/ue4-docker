ARG TAG

# Since the prebuilt SDL2 library included with UE4.20.0 onwards is not built with ALSA support,
# we rebuild it to include ALSA support (since PulseAudio doesn't play nicely with our containers)
FROM adamrehn/ue4-source:${TAG} AS sdl-builder
USER root
RUN apt-get install -y --no-install-recommends libxcursor-dev libxinerama-dev libxi-dev libxrandr-dev x11proto-scrnsaver-dev libwayland-dev libgles2-mesa-dev libpulse-dev libasound2-dev
RUN pip3 install ue4cli
USER ue4

# Perform the build (4.20.0 and newer only, this call is a no-op for older Engine versions)
RUN ue4 setroot /home/ue4/UnrealEngine
COPY --chown=ue4:ue4 build-sdl.py /tmp/build-sdl.py
RUN python3 /tmp/build-sdl.py

# -------

# Isolate the SDL build dependencies in a separate stage to avoid polluting our main image
FROM adamrehn/ue4-source:${TAG}

# Patch out all instances of `sudo` in Setup.sh, plus any commands that refuse to run as root
COPY --chown=ue4:ue4 patch-setup-linux.py /tmp/patch-setup-linux.py
RUN python3 /tmp/patch-setup-linux.py /home/ue4/UnrealEngine/Setup.sh
RUN python3 /tmp/patch-setup-linux.py /home/ue4/UnrealEngine/Engine/Build/BatchFiles/Linux/Setup.sh

# Extract the list of post-clone setup commands that require root and run them as root,
# running everything else as the non-root user to avoid creating files owned by root
WORKDIR /home/ue4/UnrealEngine
RUN echo "#!/usr/bin/env bash" >> ./root_commands.sh
RUN echo "set -x" >> ./root_commands.sh
RUN chmod a+x ./root_commands.sh
RUN ./Setup.sh
USER root
RUN ./root_commands.sh
USER ue4

# The linker bundled with UE4.20.0 onwards chokes on system libraries built with newer compilers,
# so redirect the bundled clang to use the system linker instead
COPY --chown=ue4:ue4 linker-fixup.py /tmp/linker-fixup.py
RUN python3 /tmp/linker-fixup.py /home/ue4/UnrealEngine/Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux/Linux_x64 `which ld`

# Copy our ALSA-enabled SDL library files (4.20.0 and newer only, the Python call is a no-op for older Engine versions)
ARG SDL_LIBDIR="/home/ue4/UnrealEngine/Engine/Source/ThirdParty/SDL2/SDL-gui-backend/lib/Linux/x86_64-unknown-linux-gnu"
COPY --from=sdl-builder --chown=ue4:ue4 /tmp/sdl /tmp/sdl
COPY --chown=ue4:ue4 copy-sdl.py /tmp/copy-sdl.py
RUN python3 /tmp/copy-sdl.py /tmp/sdl ${SDL_LIBDIR}

# Build UBT and build the Engine
RUN ./Engine/Build/BatchFiles/Linux/Build.sh UE4Editor Linux Development -WaitMutex
RUN ./Engine/Build/BatchFiles/Linux/Build.sh ShaderCompileWorker Linux Development -WaitMutex
RUN ./Engine/Build/BatchFiles/Linux/Build.sh UnrealPak Linux Development -WaitMutex
