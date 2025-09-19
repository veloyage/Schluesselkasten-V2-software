#!/bin/bash
# checks if desktop environment is running, starts it if not; also shuts down python program
if ! pgrep -x "wf-panel-pi" > /dev/null
then
    /usr/bin/lwrespawn /usr/bin/pcmanfm --desktop --profile LXDE-pi &
    /usr/bin/lwrespawn /usr/bin/wf-panel-pi &
    #/usr/bin/kanshi &
    /usr/bin/lxsession-xdg-autostart &
    squeekboard &
    pkill flet
    pkill python
    pkill python
else
    pkill flet
    pkill python
    pkill python
fi


