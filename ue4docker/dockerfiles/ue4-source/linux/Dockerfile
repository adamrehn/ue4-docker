ARG PREREQS_TAG
FROM adamrehn/ue4-build-prerequisites:${PREREQS_TAG}

# The git repository that we will clone
ARG GIT_REPO=""

# The git branch/tag that we will checkout
ARG GIT_BRANCH=""

# Retrieve the address for the host that will supply git credentials
ARG HOST_ADDRESS_ARG=""
ENV HOST_ADDRESS=${HOST_ADDRESS_ARG}

# Retrieve the security token for communicating with the credential supplier
ARG HOST_TOKEN_ARG=""
ENV HOST_TOKEN=${HOST_TOKEN_ARG}

# Install our git credential helper that forwards requests to the host
COPY --chown=ue4:ue4 git-credential-helper.sh /tmp/git-credential-helper.sh
ENV GIT_ASKPASS=/tmp/git-credential-helper.sh
RUN chmod +x /tmp/git-credential-helper.sh

# Clone the UE4 git repository using the host-supplied credentials
RUN git clone --progress --depth=1 -b $GIT_BRANCH $GIT_REPO /home/ue4/UnrealEngine

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
