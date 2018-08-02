ARG PREREQS_TAG
FROM adamrehn/ue4-build-prerequisites:${PREREQS_TAG}

# The git tag that we will checkout
ARG GIT_TAG=""

# Retrieve the address for the host that will supply git credentials
ARG HOST_ADDRESS_ARG=""
ENV HOST_ADDRESS=${HOST_ADDRESS_ARG}

# Retrieve the security token for communicating with the credential supplier
ARG HOST_TOKEN_ARG=""
ENV HOST_TOKEN=${HOST_TOKEN_ARG}

# Install our git credential helper that forwards requests to the host
COPY git-credential-helper.sh /tmp/git-credential-helper.sh
ENV GIT_ASKPASS=/tmp/git-credential-helper.sh
RUN chmod +x /tmp/git-credential-helper.sh

# Since UE4 refuses to build as the root user under Linux, create a non-root user
RUN useradd --create-home --home /home/ue4 --shell /bin/bash ue4
RUN usermod -a -G audio,video ue4
USER ue4

# Clone the UE4 git repository using the host-supplied credentials
ARG GIT_REPOSITORY="https://github.com/EpicGames/UnrealEngine.git"
WORKDIR /home/ue4
RUN git clone --progress --depth=1 -b $GIT_TAG $GIT_REPOSITORY
