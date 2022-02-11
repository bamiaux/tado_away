# Tado Away

Tado thermostat home/away automation.

A simple script to automatize stopping zones when:
- some opened windows are detected
- geofencing have found all devices to be away

## How to use
```sh
# install python environment
poetry install --no-dev

# run script with a default period of 60 seconds
# it will prompt for your password
poetry run python3 tado_away.py --username john.doe@gmail.com
```

This script uses python-tado to access public API from Tado thermostat. You need to use your username/password to connect to it. This script is meant to be run inside a tmux/screen whatever session.
