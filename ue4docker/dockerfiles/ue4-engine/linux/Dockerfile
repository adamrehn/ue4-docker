ARG TAG
FROM adamrehn/ue4-source:${TAG}

# The linker bundled with UE4.20.0 onwards chokes on system libraries built with newer compilers,
# so redirect the bundled clang to use the system linker instead
COPY --chown=ue4:ue4 linker-fixup.py /tmp/linker-fixup.py
RUN python3 /tmp/linker-fixup.py /home/ue4/UnrealEngine/Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux/Linux_x64 `which ld`

# Build UBT and build the Engine
RUN ./Engine/Build/BatchFiles/Linux/Build.sh UE4Editor Linux Development -WaitMutex
RUN ./Engine/Build/BatchFiles/Linux/Build.sh ShaderCompileWorker Linux Development -WaitMutex
RUN ./Engine/Build/BatchFiles/Linux/Build.sh UnrealPak Linux Development -WaitMutex
