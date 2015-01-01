#!/bin/bash -u

v1=0
v2=1
if [ "$#" == "2" ]
then
    v1="$1"
    v2="$2"
fi

v4l2-ctl -s ntsc-m -d /dev/video"${v1}"
v4l2-ctl -s ntsc-m -d /dev/video"${v2}"
