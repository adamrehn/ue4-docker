# escape=`
ARG BASETAG
FROM mcr.microsoft.com/windows/servercore:${BASETAG} as intermediate

# Add a sentinel label so we can easily identify intermediate images
LABEL com.adamrehn.ue4-docker.sentinel="1"

WORKDIR C:\stuff

# Create three 7GB files
# We do not use a single 21GiB file in order to distinguish this diagnostic from 8GiB diagnostic
RUN fsutil file createnew C:\stuff\bigfile_1.txt 7516192768
RUN fsutil file createnew C:\stuff\bigfile_2.txt 7516192768
RUN fsutil file createnew C:\stuff\bigfile_3.txt 7516192768

FROM mcr.microsoft.com/windows/servercore:${BASETAG}

# Add a sentinel label so we can easily identify intermediate images
LABEL com.adamrehn.ue4-docker.sentinel="1"

# Copy more than 20GiB between docker layers
COPY --from=intermediate C:\stuff C:\stuff
