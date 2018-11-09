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
WORKDIR /home/ue4
RUN git clone --progress --depth=1 -b $GIT_BRANCH $GIT_REPO /home/ue4/UnrealEngine
