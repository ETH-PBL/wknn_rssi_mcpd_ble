#!/bin/bash

while [ true ]
do
    cat /dev/ttyACM0 >> $1 2>/dev/null
    sleep 0.1
done
