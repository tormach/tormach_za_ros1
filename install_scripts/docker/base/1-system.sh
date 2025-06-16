#!/bin/bash -xe
WANT_ENV="docker-build docker-run"
. $(dirname $0)/../env.sh
BASE_SCRIPTS_DIR=${DOCKER_SCRIPTS_DIR}/base

###########################
# Update system & install general dependencies
###########################

# Prevent accidental installations of packages
PACKAGE_BLACKLIST=(
    python3-pint # Installed from pip; see pp-rosdep.yaml
)

>/etc/apt/preferences.d/10blacklist
for pkg in ${PACKAGE_BLACKLIST[@]}; do
    tee -a /etc/apt/preferences.d/10blacklist <<EOF

Package: $pkg
Pin: release *
Pin-Priority: -1
EOF
done

apt-get update
apt-get upgrade -y

# Install basic utilities
apt-get install -y \
    ssh-client \
    wget \
    lsb-release \
    gnupg2 \
    build-essential \
    gdb \
    doxygen \
    git \
    cgroup-tools

# Install python
apt-get install -y \
    python3-dbg \
    python3-pip \
    python3-setuptools
# - Make python3 and pip3 the default when running `python` or `pip`
update-alternatives --install /usr/bin/python python /usr/bin/python3 1
update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# upgrade pip to latest version, required by PySide6
pip install --upgrade pip

# setup locale
apt-get install -y \
    locales
sed 's/.*#\s*\(en_US.UTF-8 UTF-8\).*/\1/' /etc/locale.gen -i
locale-gen
update-locale

# ccache
apt-get install -y \
    ccache
# - add a couple of missing symlinks if needed
test -f /usr/lib/ccache/c++ || ln -s ../../bin/ccache /usr/lib/ccache/c++
test -f /usr/lib/ccache/cc || ln -s ../../bin/ccache /usr/lib/ccache/cc

# APT repo tools
apt-get install -y \
    apt-transport-https \
    curl
if test $OS_VENDOR = debian; then
    apt-get install -y debian-keyring
    apt-get install -y debian-archive-keyring
fi

###########################
# Docker CE
###########################

# Add official Docker GPG key
curl -fsSL https://download.docker.com/linux/${OS_VENDOR}/gpg |
    apt-key add -

echo "deb [arch=amd64] https://download.docker.com/linux/${OS_VENDOR} \
     $(lsb_release -cs) stable" |
    tee /etc/apt/sources.list.d/docker.list
apt-get update

# Install or update docker-ce package
apt-get install -y docker-ce

###########################
# Update apt cache
###########################

apt-get update

###########################
# Machinekit, EtherLab Master, hal_ros_control
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

# Replaced with @zultron's fork
# install_cloudsmith_repo machinekit machinekit-hal D35981AB4276AC36
install_cloudsmith_repo zultron machinekit EB6FA9FCFA405632
install_cloudsmith_repo machinekit machinekit A9B6D8B4BD8321F3
install_cloudsmith_repo zultron etherlabmaster 4505856D2FCE892D
install_cloudsmith_repo zultron hal_ros_control 8125ECEB39CC37B9

apt-get update

# # Pin Machinekit-HAL version to the latest rolling release before
# # the CMake switch and the big change in package structure (denoted
# # by change in version number to 0.5)

# machinekit_suite_version="0.4.21040-1.git21e4211e4~${DEBIAN_SUITE}"

# tee /etc/apt/preferences.d/20machinekit-version <<EOF

# Package: machinekit-hal
# Pin: version ${machinekit_suite_version}
# Pin-Priority: 999

# Package: machinekit-hal-dev
# Pin: version ${machinekit_suite_version}
# Pin-Priority: 999
# EOF
# check_package_in_repo() {
#     local package=$1
#     local version=$2

#     local packages="$(apt-cache policy $package)"
#     local retval="$?"
#     if ((retval != 0)); then
#         echo "Command 'apt-cache policy $package' returned error code $retval!"
#         exit 123
#     fi

#     if ! [[ "$packages" =~ $version ]]; then
#         echo "Package version $version of package $package was not found!"
#         exit 123
#     fi
# }

# check_package_in_repo "machinekit-hal" "$machinekit_suite_version"
# check_package_in_repo "machinekit-hal-dev" "$machinekit_suite_version"
