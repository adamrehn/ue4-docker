ARG BASEIMAGE
FROM ${BASEIMAGE}

# Add a label so we can easily identify derived images
LABEL com.adamrehn.ue4-docker.sentinel="1"

# Disable interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install our build prerequisites
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	ca-certificates \
	clang-5.0 \
	cmake \
	curl \
	git \
	libasound2 \
	lld-5.0 \
	python3 \
	python3-pip \
	shared-mime-info \
	tzdata \
	unzip \
	wget \
	xdg-user-dirs \
	zip

# Install our Python dependencies
RUN pip3 install setuptools wheel

# Since UE4 refuses to build or run as the root user under Linux, create a non-root user
RUN useradd --create-home --home /home/ue4 --shell /bin/bash ue4
RUN usermod -a -G audio,video ue4
USER ue4
