# escape=`
ARG BASETAG
FROM mcr.microsoft.com/windows/servercore:${BASETAG}
SHELL ["cmd", "/S", "/C"]

# Add a sentinel label so we can easily identify intermediate images
LABEL com.adamrehn.ue4-docker.sentinel="1"

# Attempt to download the Chocolatey installation script
RUN wget 'https://chocolatey.org/install.ps1'
