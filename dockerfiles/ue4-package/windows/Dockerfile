# escape=`
ARG TAG
FROM adamrehn/conan-ue4cli:${TAG}

# Create an Installed Build of the Engine and direct ue4cli to use it
RUN .\Engine\Build\BatchFiles\RunUAT.bat BuildGraph -target="Make Installed Build Win64" -script=Engine/Build/InstalledEngineBuild.xml -set:HostPlatformOnly=true
RUN ue4 setroot C:\UnrealEngine\LocalBuilds\Engine\Windows
