ARG BASEIMAGE
FROM ${BASEIMAGE} as prerequisites

{% if not disable_labels %}
# Add a sentinel label so we can easily identify all derived images, including intermediate images
LABEL com.adamrehn.ue4-docker.sentinel="1"
{% endif %}

# Disable interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Add the "display" driver capability for NVIDIA GPUs
# (This also allows us to run the Editor from an interactive container by bind-mounting the host system's X11 socket)
ENV NVIDIA_DRIVER_CAPABILITIES ${NVIDIA_DRIVER_CAPABILITIES},display

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
		software-properties-common \
		sudo \
		tzdata \
		unzip \
		xdg-user-dirs \
		zip && \
	rm -rf /var/lib/apt/lists/*

# Install the X11 runtime libraries required by CEF so we can cook Unreal Engine projects that use the WebBrowserWidget plugin
# (Starting in Unreal Engine 5.0, we need these installed before creating an Installed Build to prevent cooking failures related to loading the Quixel Bridge plugin)
RUN apt-get update && apt-get install -y --no-install-recommends \
			libasound2 \
			libatk1.0-0 \
			libatk-bridge2.0-0 \
			libcairo2 \
			libfontconfig1 \
			libfreetype6 \
			libglu1 \
			libnss3 \
			libnspr4 \
			libpango-1.0-0 \
			libpangocairo-1.0-0 \
			libsm6 \
			libxcomposite1 \
			libxcursor1 \
			libxi6 \
			libxrandr2 \
			libxrender1 \
			libxss1 \
			libxtst6 \
			libxv1 \
			x11-xkb-utils \
			xauth \
			xfonts-base \
			xkb-data && \
	rm -rf /var/lib/apt/lists/*

{% if enable_dso_patch %}
# Install the glibc DSO patch to improve Editor startup times
RUN add-apt-repository -y ppa:slonopotamus/glibc-dso && \
	apt-get update && \
	apt upgrade -y libc6 && \
	rm -rf /var/lib/apt/lists/*

# Enable the glibc DSO patch
ENV GLIBC_TUNABLES=glibc.rtld.dynamic_sort=2
{% endif %}

# Disable the default "lecture" message the first time a user runs a command using sudo
RUN echo 'Defaults lecture="never"' >> /etc/sudoers

# Unreal refuses to run as the root user, so create a non-root user with no password and allow them to run commands using sudo
RUN useradd --create-home --home /home/ue4 --shell /bin/bash --uid 1000 ue4 && \
	passwd -d ue4 && \
	usermod -a -G audio,video,sudo ue4
USER ue4

# Enable Git Large File Storage (LFS) support
RUN git lfs install
