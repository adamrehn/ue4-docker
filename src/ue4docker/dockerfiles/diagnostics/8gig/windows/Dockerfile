# escape=`
ARG BASETAG
FROM mcr.microsoft.com/windows/servercore:${BASETAG}
SHELL ["cmd", "/S", "/C"]

# Add a sentinel label so we can easily identify intermediate images
LABEL com.adamrehn.ue4-docker.sentinel="1"

# Atttempt to create an 8GiB filesystem layer
ARG CREATE_RANDOM
COPY test.ps1 C:\test.ps1
RUN powershell -ExecutionPolicy Bypass -File C:\test.ps1
