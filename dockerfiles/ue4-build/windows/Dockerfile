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

# Install ue4cli and the prerequisites for conan-ue4cli
RUN git clone "https://github.com/adamrehn/conan-ue4cli.git" C:\conan-ue4cli
RUN pip install -r C:\conan-ue4cli\requirements.txt

# Point ue4cli to the root of the built Engine
RUN ue4 setroot C:\UnrealEngine

# Install conan-ue4cli (4.19.0 and newer only, this call is a no-op for older Engine versions)
RUN python C:\conan-ue4cli\generate.py
