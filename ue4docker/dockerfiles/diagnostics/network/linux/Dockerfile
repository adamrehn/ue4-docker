FROM alpine:latest

# Add a sentinel label so we can easily identify intermediate images
LABEL com.adamrehn.ue4-docker.sentinel="1"

# Attempt to download the Chocolatey installation script (not actually useful under Linux of course, but useful as a network test)
RUN wget 'https://chocolatey.org/install.ps1'
