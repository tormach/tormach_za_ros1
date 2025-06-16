#!/bin/bash -xe

WANT_ENV="docker-build docker-run"
. $(dirname $0)/../env.sh
BASE_SCRIPTS_DIR=${DOCKER_SCRIPTS_DIR}/base

# Update package lists and install necessary packages
apt-get update
apt-get install -y git cmake build-essential

# Create a temporary directory for the build
BUILD_DIR=$(mktemp -d)
cd "$BUILD_DIR"

# Clone the YDLidar-SDK repository
# FIXME Build broken after upstream changes
# https://github.com/YDLIDAR/YDLidar-SDK/issues/58
# https://github.com/YDLIDAR/YDLidar-SDK/pull/59
# git clone https://github.com/YDLIDAR/YDLidar-SDK.git
git clone https://github.com/hannesduske/YDLidar-SDK.git
cd YDLidar-SDK

# Create build directory
mkdir -p build
cd build

# Run cmake with installation prefix set to /usr/local
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..

# Compile
make

# Install the library
make install

# Clean up
cd /
rm -rf "$BUILD_DIR"

# Clean up apt cache to reduce image size
apt-get clean
rm -rf /var/lib/apt/lists/*

echo "YDLidar-SDK has been successfully compiled and installed!"
