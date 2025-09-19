#!/bin/bash
# script to start the Schlüsselkasten GUI

# kill any remaining app components
pkill flet
pkill python
pkill python

pinctrl 19 a5 # enable PWM (alternate 5) on pin 19 (display backlight)

source ~/SKV2-env/bin/activate # enable venv

cd ~/Schluesselkasten-V2-software/

flet run &

