{% if combine %}
FROM source as engine
{% else %}
ARG NAMESPACE
ARG TAG
ARG PREREQS_TAG
FROM ${NAMESPACE}/ue4-source:${TAG}-${PREREQS_TAG}
{% endif %}

# Build UBT and build the Engine
RUN ./Engine/Build/BatchFiles/Linux/Build.sh UE4Editor Linux Development -WaitMutex
RUN ./Engine/Build/BatchFiles/Linux/Build.sh ShaderCompileWorker Linux Development -WaitMutex
RUN ./Engine/Build/BatchFiles/Linux/Build.sh UnrealPak Linux Development -WaitMutex
