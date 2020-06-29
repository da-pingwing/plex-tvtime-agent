tvtime = {
    "urls": {
        "device":           "https://api.tvtime.com/v1/oauth/device/code",
        "access_token":     "https://api.tvtime.com/v1/oauth/access_token",
        "check_in":         "https://api.tvtime.com/v1/checkin",
        "user":             "https://api.tvtime.com/v1/user",
        "library":          "https://api.tvtime.com/v1/library",
        "follow":           "https://api.tvtime.com/v1/follow",
        "progress":         "https://api.tvtime.com/v1/show_progress",
        "show":             "https://api.tvtime.com/v1/show"
    },
    "auth": {
        "id": "UOWED7wBGRQv17skSZJO",
        "secret": "ZHYcO8n8h6WbYuMDWVgXr7T571ZF_s1r1Rzu1-3B",
        "user-agent": "plex-tvtime-agent",
        "timeout": 300,
        "interval": 30,
        "rate_time": 6
    }
}
plex = {
    "urls":{
        "library": "/library/sections/2/all",
        "details": "/library/metadata/{plex_id}/children",
        "watched": "/:/scrobble?key={item_id}&identifier=com.plexapp.plugins.library"
    },
    "auth":{
        "token": "qPG2zGyqMATsB638MEyi",
        "server": "http://192.168.1.234:32400"
    }
}
