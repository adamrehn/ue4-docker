FROM alpine:latest

# Add a sentinel label so we can easily identify intermediate images
LABEL com.adamrehn.ue4-docker.sentinel="1"

# The BusyBox version of `head` doesn't support the syntax "8G", so we specify 8GiB in bytes
RUN head -c 8589934592 </dev/urandom >file
