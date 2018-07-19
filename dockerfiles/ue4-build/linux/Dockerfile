ARG TAG
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

# Build UBT and build the Engine
USER ue4
RUN ./Engine/Build/BatchFiles/Linux/Build.sh UE4Editor Linux Development -WaitMutex
