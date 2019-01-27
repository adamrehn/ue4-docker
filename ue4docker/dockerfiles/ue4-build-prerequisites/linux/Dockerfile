ARG BASEIMAGE
FROM ${BASEIMAGE}

# Add a sentinel label so we can easily identify all derived images, including intermediate images
LABEL com.adamrehn.ue4-docker.sentinel="1"

# Disable interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install our build prerequisites
RUN \
	apt-get update && apt-get install -y --no-install-recommends \
		build-essential \
		ca-certificates \
		curl \
		git \
		python3 \
		python3-pip \
		shared-mime-info \
		tzdata \
		unzip \
		xdg-user-dirs \
		zip && \
	rm -rf /var/lib/apt/lists/*

# Since UE4 refuses to build or run as the root user under Linux, create a non-root user
RUN \
	useradd --create-home --home /home/ue4 --shell /bin/bash --uid 1000 ue4 && \
	usermod -a -G audio,video ue4
USER ue4
