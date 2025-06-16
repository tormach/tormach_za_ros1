#!/bin/bash -xe

# These should run in minimal environment, so avoid populating
# PathPilot Robot set of environment variables

####################################################
# Set up Debian (Ubuntu) packaging tools
####################################################

# Ensure apt cache is up to date
apt-get update

# Install the actual build tools (notice the 'equivs'
# needed for Ubuntu)
apt-get install -y \
    build-essential \
    lsb-release \
    fakeroot \
    devscripts \
    equivs \
    jq \
    curl \
    git

###########################
# The CMake build-system tool
###########################

# Kitware is publishing pre-built binaries only for amd64 and arm64 architectures!
curl -1vLf \
    $(curl -s https://api.github.com/repos/kitware/cmake/releases/latest |
        jq -r --arg FILE "cmake-\d{1,}\.\d{1,}\.\d{1,}(-.{1,})?-linux-$(dpkg-architecture -qDEB_BUILD_GNU_CPU)\.sh" \
            '.assets | .[] | select(.name? | match($FILE)) | .browser_download_url') \
    --output /tmp/cmake.sh &&
    bash /tmp/cmake.sh --skip-license --prefix=/usr/local

###########################
# Machinekit dependencies repository
###########################

# Cloudsmith.io hosting provider specific installation
apt-get install -y debian-keyring \
    debian-archive-keyring \
    apt-transport-https

install_cloudsmith_repo() {
    local base="https://dl.cloudsmith.io/public"
    local org=$1
    local repo=$2
    local key_id=$3
    local keyring_location="/usr/share/keyrings/${org}-${repo}-archive-keyring.gpg"
    local distro="$(lsb_release -is)"
    local codename="$(lsb_release -cs)"
    local cloudsmith_args="distro=${distro,,}&codename=${codename,,}"
    curl -1sLf ${base}/${org}/${repo}/gpg.${key_id}.key |
        gpg --dearmor >${keyring_location}
    curl -1sLf "${base}/${org}/${repo}/config.deb.txt?${cloudsmith_args}" \
        >/etc/apt/sources.list.d/${org}-${repo}.list
}

install_cloudsmith_repo machinekit machinekit A9B6D8B4BD8321F3

apt-get update
