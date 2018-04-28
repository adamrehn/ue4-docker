ARG TAG
FROM adamrehn/ue4-build:${TAG}

WORKDIR /home/ue4
RUN git clone "https://github.com/adamrehn/conan-ue4cli.git"
WORKDIR /home/ue4/conan-ue4cli
USER root
RUN pip3 install setuptools wheel
RUN pip3 install -r ./requirements.txt
USER ue4
RUN ue4 setroot /home/ue4/UnrealEngine
RUN python3 ./generate.py
