FROM alpine:latest

# Add a sentinel label so we can easily identify intermediate images
LABEL com.adamrehn.ue4-docker.sentinel="1"

# Test that we can ping the IPv6 loopback address
RUN ping6 -c 5 '::1'
