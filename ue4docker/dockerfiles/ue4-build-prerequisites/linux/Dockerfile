ARG BASEIMAGE
FROM ${BASEIMAGE} as prerequisites

{% if not disable_labels %}
# Add a sentinel label so we can easily identify all derived images, including intermediate images
LABEL com.adamrehn.ue4-docker.sentinel="1"
{% endif %}

# Disable interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install our build prerequisites
RUN apt-get update && apt-get install -y --no-install-recommends \
		build-essential \
		ca-certificates \
		curl \
		git \
		git-lfs \
		python3 \
		python3-dev \
		python3-pip \
		shared-mime-info \
		sudo \
		tzdata \
		unzip \
		xdg-user-dirs \
		zip && \
	rm -rf /var/lib/apt/lists/*

# Disable the default "lecture" message the first time a user runs a command using sudo
RUN echo 'Defaults lecture="never"' >> /etc/sudoers

# Unreal refuses to run as the root user, so create a non-root user with no password and allow them to run commands using sudo
RUN useradd --create-home --home /home/ue4 --shell /bin/bash --uid 1000 ue4 && \
	passwd -d ue4 && \
	usermod -a -G audio,video,sudo ue4
USER ue4

# Enable Git Large File Storage (LFS) support
RUN git lfs install
