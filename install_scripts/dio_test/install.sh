#!/bin/bash -xe
VER=$1

if cat /proc/mounts | awk '$2 == "/mnt" {exit 1;} ENDFILE {exit 0;}'; then
    sudo mount /dev/sdb1 /mnt
fi
cd ~/dio_test
TARBALL=$(ls -dt /mnt/dio_test*.tgz | head -1)
tar xvf $TARBALL

#sudo umount /mnt
