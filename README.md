# plex-tvtime-agent - Syncing both ways
Script for loading Plex into TvTime and TvTime into Plex.

# Installation
Any Operating system is supported:

Requirements:
- Python
- Conda 
    - Clint     (```conda install -c conda-forge clint```)
    - requests  (```conda install -c conda-forge clint```)

Modify config.py to add your plex.auth details (server and token)
Plex token guide: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

# Running
- Step 1: Run the script  ```python main.py``` 
- Step 2: Follow the instructions to bind your TvTime account to your script and get the access token
- Step 3: Wait while it runs (it can take a while because of the TvTime limit)

# Automatic sync
Run this script in a cronjob once a day as running it all the time will use up the API rates for everyone else.

# Credits
Idea from: https://github.com/imrabti/tvshowtime-plex
