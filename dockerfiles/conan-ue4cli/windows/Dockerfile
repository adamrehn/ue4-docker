# escape=`
ARG TAG
FROM adamrehn/ue4-build:${TAG}

WORKDIR C:\
RUN git clone "https://github.com/adamrehn/conan-ue4cli.git"
WORKDIR C:\conan-ue4cli
RUN pip install -r .\requirements.txt
RUN ue4 setroot C:\UnrealEngine
RUN python .\generate.py
