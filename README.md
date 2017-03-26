# UnifiSynoCam
Unifi based Geofence camera controlling in Synology Surveillance Station

This Python3 script uses the active client results of the Unifi Controller to enable and disable a camera in Synology Surveillance Station.

# Configuration
This script uses the default site in the Unifi controller so it may need a change for your specific set-up. Also it's set to camera id 1 in the Synology Surveillance Station.

To-Do:
- Secure connection to DSM
- Controlling multiple camera's at once
- Make everything less dirty :)

Push messaging:
It uses pushover.net to create push messages and inform on activity. The function message() can be easily adjusted to print(),empty or any other tool.