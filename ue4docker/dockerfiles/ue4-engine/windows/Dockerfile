# escape=`
ARG NAMESPACE
ARG TAG
ARG PREREQS_TAG
FROM ${NAMESPACE}/ue4-source:${TAG}-${PREREQS_TAG}

# Build UBT and build the Engine
RUN GenerateProjectFiles.bat
RUN .\Engine\Build\BatchFiles\Build.bat UE4Editor Win64 Development -WaitMutex
RUN .\Engine\Build\BatchFiles\Build.bat ShaderCompileWorker Win64 Development -WaitMutex
RUN .\Engine\Build\BatchFiles\Build.bat UnrealPak Win64 Development -WaitMutex
