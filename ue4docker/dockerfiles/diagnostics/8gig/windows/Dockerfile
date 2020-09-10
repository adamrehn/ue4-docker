# escape=`
ARG BASETAG
FROM mcr.microsoft.com/windows/servercore:${BASETAG}
SHELL ["cmd", "/S", "/C"]

# Add a sentinel label so we can easily identify intermediate images
LABEL com.adamrehn.ue4-docker.sentinel="1"

# Write an 8GiB sparse file
RUN powershell "fsutil.exe file createnew file 8589934592"
