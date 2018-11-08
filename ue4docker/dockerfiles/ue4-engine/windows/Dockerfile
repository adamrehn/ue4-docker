# escape=`
ARG TAG
FROM adamrehn/ue4-source:${TAG}

# Since the UE4 prerequisites installer appears to break when newer versions
# of the VC++ runtime are present, patch out the prereqs call in Setup.bat
COPY patch-setup-win.py C:\patch-setup-win.py
RUN python C:\patch-setup-win.py C:\UnrealEngine\Setup.bat

# Run post-clone setup steps
WORKDIR C:\UnrealEngine
RUN Setup.bat

# Build UBT and build the Engine
RUN GenerateProjectFiles.bat
RUN .\Engine\Build\BatchFiles\Build.bat UE4Editor Win64 Development -WaitMutex
RUN .\Engine\Build\BatchFiles\Build.bat ShaderCompileWorker Win64 Development -WaitMutex
RUN .\Engine\Build\BatchFiles\Build.bat UnrealPak Win64 Development -WaitMutex
