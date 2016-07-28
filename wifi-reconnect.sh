#!/bin/bash

INTERFACE=wlan0
wlan=`/sbin/ifconfig $INTERFACE | grep inet\ addr | wc -l` 
if [ $wlan -eq 0 ]; then
    sudo ifdown --force $INTERFACE
    sudo ifup $INTERFACE
else
    echo "wifi ok"
fi
