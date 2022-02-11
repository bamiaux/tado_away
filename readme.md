# Tado Away

Tado thermostat home/away automation.

A simple script to automatize stopping zones when:
- some opened windows are detected
- geofencing have found all devices to be away

This script uses python-tado to access public API from Tado thermostat. You need to use your username/password to connect to it. This script is meant to be run periodically, like once every 5 minutes to adjust heating accordingly.