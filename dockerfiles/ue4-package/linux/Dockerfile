ARG TAG
FROM adamrehn/conan-ue4cli:${TAG}

# Create an Installed Build of the Engine and direct ue4cli to use it
WORKDIR /home/ue4/UnrealEngine
RUN ./Engine/Build/BatchFiles/RunUAT.sh BuildGraph -target="Make Installed Build Linux" -script=Engine/Build/InstalledEngineBuild.xml -set:HostPlatformOnly=true
RUN ue4 setroot /home/ue4/UnrealEngine/LocalBuilds/Engine/Linux
