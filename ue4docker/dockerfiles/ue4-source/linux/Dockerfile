{% if combine %}
FROM prerequisites as source
{% else %}
ARG PREREQS_TAG
FROM adamrehn/ue4-build-prerequisites:${PREREQS_TAG}
{% endif %}

{% if not disable_all_patches %}
# Enable verbose output for steps that patch files?
ARG VERBOSE_OUTPUT=0
{% endif %}

{% if source_mode == "copy" %}

# Copy the Unreal Engine source code from the host system
ARG SOURCE_LOCATION
COPY ${SOURCE_LOCATION} /home/ue4/UnrealEngine

{% else %}

# The git repository that we will clone
ARG GIT_REPO=""

# The git branch/tag that we will checkout
ARG GIT_BRANCH=""

{% if credential_mode == "secrets" %}

# Install our git credential helper that retrieves credentials from build secrets
COPY --chown=ue4:ue4 git-credential-helper-secrets.sh /tmp/git-credential-helper-secrets.sh
ENV GIT_ASKPASS=/tmp/git-credential-helper-secrets.sh
RUN chmod +x /tmp/git-credential-helper-secrets.sh

# Clone the UE4 git repository using the build secret credentials
RUN --mount=type=secret,id=username,uid=1000,required \
	--mount=type=secret,id=password,uid=1000,required \
	git clone --progress --depth=1 -b $GIT_BRANCH $GIT_REPO /home/ue4/UnrealEngine

{% else %}

# Retrieve the address for the host that will supply git credentials
ARG HOST_ADDRESS_ARG=""
ENV HOST_ADDRESS=${HOST_ADDRESS_ARG}

# Retrieve the security token for communicating with the credential supplier
ARG HOST_TOKEN_ARG=""
ENV HOST_TOKEN=${HOST_TOKEN_ARG}

# Install our git credential helper that forwards requests to the credential HTTP endpoint on the host
COPY --chown=ue4:ue4 git-credential-helper-endpoint.sh /tmp/git-credential-helper-endpoint.sh
ENV GIT_ASKPASS=/tmp/git-credential-helper-endpoint.sh
RUN chmod +x /tmp/git-credential-helper-endpoint.sh

# Clone the UE4 git repository using the endpoint-supplied credentials
RUN git clone --progress --depth=1 -b $GIT_BRANCH $GIT_REPO /home/ue4/UnrealEngine

{% endif %}

{% endif %}

{% if (not disable_all_patches) and (not disable_release_patches) %}
# Apply our bugfix patches to broken Engine releases such as 4.25.4
# (Make sure we do this before the post-clone setup steps are run)
COPY --chown=ue4:ue4 patch-broken-releases.py /tmp/patch-broken-releases.py
RUN python3 /tmp/patch-broken-releases.py /home/ue4/UnrealEngine $VERBOSE_OUTPUT
{% endif %}

# Run post-clone setup steps, ensuring our package lists are up to date since Setup.sh doesn't call `apt-get update`
# (Note that the `-no-cache` flag disables caching of dependency data in `.git/ue4-gitdeps`, saving disk space)
WORKDIR /home/ue4/UnrealEngine
RUN sudo apt-get update && \
	./Setup.sh -no-cache && \
	sudo rm -rf /var/lib/apt/lists/*

{% if (not disable_all_patches) and (not disable_linker_fixup) %}
# The linker bundled with UE4.20.0 onwards chokes on system libraries built with newer compilers,
# so redirect the bundled clang to use the system linker instead
COPY --chown=ue4:ue4 linker-fixup.py /tmp/linker-fixup.py
RUN python3 /tmp/linker-fixup.py /home/ue4/UnrealEngine/Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux/Linux_x64 `which ld`
{% endif %}

{% if (not disable_all_patches) and (not disable_example_platform_cleanup) %}
# Remove the sample `XXX` example platform code, since this breaks builds from 4.24.0 onwards
# (For details of what this is, see: <https://forums.unrealengine.com/unreal-engine/announcements-and-releases/1617783-attention-platform-changes-ahead>)
RUN rm -r -f /home/ue4/UnrealEngine/Engine/Platforms/XXX
{% endif %}

{% if (not disable_all_patches) and (not disable_ubt_patches) %}
# Apply our bugfix patches to UnrealBuildTool (UBT)
COPY --chown=ue4:ue4 patch-ubt.py /tmp/patch-ubt.py
RUN python3 /tmp/patch-ubt.py /home/ue4/UnrealEngine/Engine/Source/Programs/UnrealBuildTool
{% endif %}
