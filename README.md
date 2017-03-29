# UnifiSynoCam
Unifi Controller based camera controlling in Synology Surveillance Station.

# Why this project?
Home security cameras are becoming a more important addition to any household, but they carry the risk of unauthorized access and privacy issues with them. With this in mind, I wanted to switch off my camera's in Synology Surveillance Station when I’m at home and enable them automatically again when I leave. As I didn't find anything useful online and didn't want to install an app (geofencing) on my phone due power usage, I had to find another way.

I decided to develop my own script and use my Ubiquiti Unifi Controller as a source for the @home indication. This Python3 script uses this indication (polling the active client results) to enable and disable camera(s) in Synology Surveillance Station automatically.

# Configuration
See the config file. You can specifiy a list of clients and multiple camera id's.

To-Do:
- Secure connection to DSM
- Make everything less dirty :)

Push messaging:
It uses pushover.net to create push messages and inform on activity. The function "message()" can be easily adjusted to print(),empty or any other tool.