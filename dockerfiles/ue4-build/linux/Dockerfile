ARG TAG

# Since the prebuilt SDL2 library included with UE4.20.0 onwards is not built with ALSA support,
# we rebuild it to include ALSA support (since PulseAudio doesn't play nicely with our containers)
FROM adamrehn/ue4-source:${TAG} AS sdl-builder
USER root
RUN apt-get install -y --no-install-recommends libxcursor-dev libxinerama-dev libxi-dev libxrandr-dev x11proto-scrnsaver-dev libwayland-dev libgles2-mesa-dev libpulse-dev libasound2-dev
USER ue4

# Retrieve the dependency files for SDL and Vulkan
WORKDIR /home/ue4/UnrealEngine
RUN ./Engine/Build/BatchFiles/Linux/GitDependencies.sh --prompt \
	--exclude=AMD \
	--exclude=AndroidPermission \
	--exclude=ANGLE \
	--exclude=Binaries \
	--exclude=Breakpad \
	--exclude=Build \
	--exclude=CEF3 \
	--exclude=Content \
	--exclude=coremod \
	--exclude=CryptoPP \
	--exclude=Documentation \
	--exclude=DotNetZip \
	--exclude=elftoolchain \
	--exclude=Expat \
	--exclude=Extras \
	--exclude=FakeIt \
	--exclude=FBX \
	--exclude=FeaturePacks \
	--exclude=ForsythTriOO \
	--exclude=FreeType2 \
	--exclude=glslang \
	--exclude=GoogleARCore \
	--exclude=GoogleInstantPreview \
	--exclude=GoogleTest \
	--exclude=GoogleVR \
	--exclude=HarfBuzz \
	--exclude=hlslcc \
	--exclude=ICU \
	--exclude=IntelEmbree \
	--exclude=IntelISPCTexComp \
	--exclude=IntelTBB \
	--exclude=IOS \
	--exclude=jemalloc \
	--exclude=Kiss_FFT \
	--exclude=Leap \
	--exclude=libcurl \
	--exclude=libOpus \
	--exclude=libPhonon \
	--exclude=libPNG \
	--exclude=libSampleRate \
	--exclude=libstrophe \
	--exclude=libWebSockets \
	--exclude=Licenses \
	--exclude=llvm \
	--exclude=MCPP \
	--exclude=MikkTSpace \
	--exclude=mtlpp \
	--exclude=NVIDIA \
	--exclude=nvtesslib \
	--exclude=nvTextureTools \
	--exclude=nvTriStrip \
	--exclude=Oculus \
	--exclude=Ogg \
	--exclude=OneSky \
	--exclude=OpenAL \
	--exclude=openexr \
	--exclude=OpenSSL \
	--exclude=OpenSubdiv \
	--exclude=OpenVR \
	--exclude=Perforce \
	--exclude=PLCrashReporter \
	--exclude=Plugins \
	--exclude=Programs \
	--exclude=PhysX \
	--exclude=PhysX3 \
	--exclude=Qualcomm \
	--exclude=rd_route \
	--exclude=ResonanceAudioApi \
	--exclude=Runtime \
	--exclude=Samples \
	--exclude=SpeedTree \
	--exclude=Steamworks \
	--exclude=Templates \
	--exclude=TVOS \
	--exclude=VHACD \
	--exclude=Vorbis \
	--exclude=WebRTC \
	--exclude=Windows \
	--exclude=zlib

# Copy the Vulkan headers into the location that the SDL2 build script looks for them
RUN mkdir /home/ue4/UnrealEngine/Engine/Source/ThirdParty/Vulkan/Linux
RUN cp -R /home/ue4/UnrealEngine/Engine/Source/ThirdParty/Vulkan/Include /home/ue4/UnrealEngine/Engine/Source/ThirdParty/Vulkan/Linux/include

# Rebuild SDL2
RUN ./Engine/Source/ThirdParty/SDL2/build.sh

# -------

# Isolate the SDL build dependencies in a separate stage to avoid polluting our main image
FROM adamrehn/ue4-source:${TAG}

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

# Copy our ALSA-enabled SDL library files
ARG SDL_LIBDIR="/home/ue4/UnrealEngine/Engine/Source/ThirdParty/SDL2/SDL-gui-backend/lib/Linux/x86_64-unknown-linux-gnu"
COPY --from=sdl-builder ${SDL_LIBDIR} ${SDL_LIBDIR}

# Build UBT and build the Engine
RUN ./Engine/Build/BatchFiles/Linux/Build.sh UE4Editor Linux Development -WaitMutex
