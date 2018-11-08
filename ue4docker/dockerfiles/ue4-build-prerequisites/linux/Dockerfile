ARG BASEIMAGE
FROM ${BASEIMAGE}

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
