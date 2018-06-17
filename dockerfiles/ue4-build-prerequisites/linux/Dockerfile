FROM ubuntu:18.04

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
	python3 \
	python3-pip \
	tzdata \
	unzip \
	wget \
	zip
