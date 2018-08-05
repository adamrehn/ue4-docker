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
COPY build-sdl.py /tmp/build-sdl.py
RUN python3 /tmp/build-sdl.py

# -------

# Isolate the SDL build dependencies in a separate stage to avoid polluting our main image
FROM adamrehn/ue4-source:${TAG}

# Install ue4cli and the prerequisites for conan-ue4cli
RUN git clone "https://github.com/adamrehn/conan-ue4cli.git" /home/ue4/conan-ue4cli
USER root
RUN pip3 install -r /home/ue4/conan-ue4cli/requirements.txt
USER ue4

# Point ue4cli to the root of the Engine source tree
RUN ue4 setroot /home/ue4/UnrealEngine

# Patch out all instances of `sudo` in Setup.sh, plus any commands that refuse to run as root
COPY patch-setup-linux.py /tmp/patch-setup-linux.py
RUN python3 /tmp/patch-setup-linux.py /home/ue4/UnrealEngine/Setup.sh
RUN python3 /tmp/patch-setup-linux.py /home/ue4/UnrealEngine/Engine/Build/BatchFiles/Linux/Setup.sh

# Run post-clone setup as root (so any apt-get commands will work) and then set the
# non-root user as the owner of all generated files to prevent any permission issues
WORKDIR /home/ue4/UnrealEngine
USER root
RUN ./Setup.sh
RUN chown -hR ue4 /home/ue4/UnrealEngine
USER ue4

# The linker bundled with UE4.20.0 onwards chokes on system libraries built with newer compilers,
# so redirect the bundled clang to use the system linker instead
ENV BUNDLED_LINKER /home/ue4/UnrealEngine/Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux/Linux_x64/v11_clang-5.0.0-centos7/x86_64-unknown-linux-gnu/bin/x86_64-unknown-linux-gnu-ld
RUN test -e "$BUNDLED_LINKER" && rm "$BUNDLED_LINKER" && ln -s `which ld` "$BUNDLED_LINKER"; exit 0

# Copy our ALSA-enabled SDL library files (4.20.0 and newer only, the Python call is a no-op for older Engine versions)
ARG SDL_LIBDIR="/home/ue4/UnrealEngine/Engine/Source/ThirdParty/SDL2/SDL-gui-backend/lib/Linux/x86_64-unknown-linux-gnu"
COPY --from=sdl-builder /tmp/sdl /tmp/sdl
COPY copy-sdl.py /tmp/copy-sdl.py
RUN python3 /tmp/copy-sdl.py /tmp/sdl ${SDL_LIBDIR}

# Build UBT and build the Engine
RUN ./Engine/Build/BatchFiles/Linux/Build.sh UE4Editor Linux Development -WaitMutex

# Install conan-ue4cli (4.19.0 and newer only, this call is a no-op for older Engine versions)
RUN python3 /home/ue4/conan-ue4cli/generate.py
