# escape=`
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
COPY git-credential-helper.bat C:\git-credential-helper.bat
ENV GIT_ASKPASS=C:\git-credential-helper.bat

# Clone the UE4 git repository using the host-supplied credentials
WORKDIR C:\
RUN git clone --progress --depth=1 -b %GIT_BRANCH% %GIT_REPO% C:\UnrealEngine

# Install legacy toolchain components if we're building UE4.19
# (This call is a no-op under newer Engine versions)
COPY legacy-toolchain-fix.py C:\legacy-toolchain-fix.py
RUN python C:\legacy-toolchain-fix.py

# Since the UE4 prerequisites installer appears to break when newer versions
# of the VC++ runtime are present, patch out the prereqs call in Setup.bat
COPY patch-setup-win.py C:\patch-setup-win.py
RUN python C:\patch-setup-win.py C:\UnrealEngine\Setup.bat

# Run post-clone setup steps
WORKDIR C:\UnrealEngine
RUN Setup.bat
