# Imports
import config as config
import json
from clint.textui import puts, colored, indent
import requests
import time
from xml.etree import ElementTree

# Globals
access_token    = ""
username        = ""
shows           = {}

# Main code
def startup():
    puts(colored.yellow('[Plex-TvTime-Agent]')+ " Starting PLEX - TvTime automatic agent by Clovis Warlop");
    puts(colored.yellow('[Plex-TvTime-Agent]')+ " Based off: https://github.com/imrabti/tvshowtime-plex");
    with open('tokens.json') as json_file:
        token_data = json.load(json_file)
        if(token_data['access_token'] != ""):
            global access_token 
            access_token = token_data['access_token']
            puts(colored.yellow('[Plex-TvTime-Agent]') + colored.blue('[Authentication]') + " Token found - Starting with token")
            loadUser()
        else:
            puts(colored.yellow('[Plex-TvTime-Agent]') + colored.blue('[Authentication]') + " Token not found - Starting with token request")
            authenticate()

# Authentication
def authenticate():
    try:
        headers = {'User-Agent': config.tvtime["auth"]['user-agent'] }
        data    = {'client_id': config.tvtime["auth"]['id']}
        request = requests.post(config.tvtime["urls"]['device'], data=data, headers=headers)
        request_json = request.json()

        if(request_json["result"] == "OK"):
            # output for user
            puts(colored.yellow('[Plex-TvTime-Agent]') + colored.blue('[Authentication]') +"###############################################################################")
            puts(colored.yellow('[Plex-TvTime-Agent]') + colored.blue('[Authentication]') +" Instructions: Type this code into your browser in the following URL. ")
            puts(colored.yellow('[Plex-TvTime-Agent]') + colored.blue('[Authentication]') +" Authentication code: "+request_json["user_code"])
            puts(colored.yellow('[Plex-TvTime-Agent]') + colored.blue('[Authentication]') +" Authorization URL: "+request_json["verification_url"])
            puts(colored.yellow('[Plex-TvTime-Agent]') + colored.blue('[Authentication]') +"###############################################################################")

            # wait for authentication token to change
            global access_token 
            access_token= False
            total = 0
            while (access_token == False and total < config.tvtime["auth"]['timeout']):
                access_token = loadAuthCode(request_json["device_code"])
                time.sleep(config.tvtime["auth"]['interval'])
                total += config.tvtime["auth"]['interval']

            if(access_token != False):
                # store access token
                data = {};
                data['access_token'] = access_token
                with open('tokens.json', 'w') as outfile:
                    json.dump(data, outfile)
                puts(colored.yellow('[Plex-TvTime-Agent]') + colored.blue('[Authentication]') + colored.green('[Success]') + " Connected to TVTime!")
                loadUser()
            else:
                puts(colored.yellow('[Plex-TvTime-Agent]') + colored.blue('[Authentication]') + colored.red('[Error]') + " Timeout please try again!")
                authenticate()
        else:
            puts(colored.yellow('[Plex-TvTime-Agent]') + colored.blue('[Authentication]') + colored.red('[Error]') + " Error in request to TVTime.com")
    except Exception as e:
        print(e)
        puts(colored.yellow('[Plex-TvTime-Agent]') + colored.blue('[Authentication]') + colored.red('[Error]') + " Issue in authentication")

# TV Showtime authentication
def loadAuthCode(device_code):
    puts(colored.yellow('[Plex-TvTime-Agent]') + colored.blue('[Authentication]') + " Checking for authentication")
    headers     = {'User-Agent': config.tvtime["auth"]['user-agent'] }
    data        = {'client_id': config.tvtime["auth"]['id'], 'client_secret': config.tvtime["auth"]['secret'], 'code': device_code}
    request     = requests.post(config.tvtime["urls"]['access_token'], data=data, headers=headers)
    request_json = request.json()

    # Return Access Token or failure
    if(request_json['result'] == "OK"):
        return request_json['access_token']
    else:
        puts(colored.yellow('[Plex-TvTime-Agent]') + colored.blue('[Authentication]') + colored.red('[Error]') + " Authentication not yet completed")
        return False

# Load username - (be pretty)
def loadUser():
    headers = {'User-Agent': config.tvtime["auth"]['user-agent'] }
    request = requests.get(config.tvtime["urls"]['user']+"?access_token="+access_token, headers=headers)
    request_json = request.json()
    if(request_json["result"] == "OK"):
        global username 
        username = request_json["user"]["name"]
        puts(colored.yellow('[Plex-TvTime-Agent]') + colored.magenta('[General]') +"###############################################################################")
        puts(colored.yellow('[Plex-TvTime-Agent]') + colored.magenta('[General]') + " Welcome "+username) 
        puts(colored.yellow('[Plex-TvTime-Agent]') + colored.magenta('[General]') +"###############################################################################")
        puts(colored.yellow('[Plex-TvTime-Agent]') + colored.cyan('[Phase 1]') + " Loading Tv Time Data ") 
        loadTvTimeShows();
    else:
        puts(colored.yellow('[Plex-TvTime-Agent]') + colored.cyan('[Phase 1]') + colored.red('[Error]') + " Token Expired, reauthenticate!")
        authenticate()

# (TVTime) Load Shows
def loadTvTimeShows():
    keep_loading = True
    page = 0
    error = False
    global shows
    while keep_loading:
        headers = {'User-Agent': config.tvtime["auth"]['user-agent'] }
        url_params = "?access_token="+access_token+"&page="+str(page)+"&limit=100"
        request = requests.get(config.tvtime["urls"]['library']+url_params, headers=headers)
        request_json = request.json()
        if(request_json["result"] == "OK"):
            if(len(request_json['shows'])>0):
                for show in request_json['shows']:
                    shows[str(show['id'])]= { "tvtime": int(show['seen_episodes']) }
                page += 1
            else:
                puts(colored.yellow('[Plex-TvTime-Agent]') + colored.cyan('[Phase 1]') + colored.green('[Success]') + " Finished Loading TvTime (total: "+str(len(shows))+")")
                keep_loading = False
        else:
            puts(colored.yellow('[Plex-TvTime-Agent]') + colored.cyan('[Phase 1]') + colored.red('[Error]') + " Failed to load shows from TvTime")
            keep_loading = False
            error = True

    if not error:
        loadPlexShows()

# (Plex) Load Shows
def loadPlexShows():
    global shows
    headers = {'User-Agent': config.tvtime["auth"]['user-agent'] }
    url_params = "?X-Plex-Token="+config.plex["auth"]['token']
    request = requests.get(config.plex["auth"]['server']+config.plex["urls"]['library']+url_params, headers=headers)
    tree = ElementTree.fromstring(request.content)

    for show in tree.findall('Directory'):
        showId = str(show.get("guid").split('//')[1].split('?')[0])
        if(showId in shows):
            shows[showId]["plex"] = int(show.get("viewedLeafCount"))
            shows[showId]["plex_id"] = int(show.get("ratingKey"))
        else:
            shows[showId] = {"plex": int(show.get("viewedLeafCount")), "plex_id": int(show.get("ratingKey"))}
    puts(colored.yellow('[Plex-TvTime-Agent]') + colored.cyan('[Phase 1]') + colored.green('[Success]') + " Finished Loading Plex  (total: "+str(len(shows))+")")
    if(len(shows)>0):
        processShows()
    else:
        puts(colored.yellow('[Plex-TvTime-Agent]') + colored.cyan('[Phase 1]') + colored.red('[Error]') + " No shows found, stopping")

# Process Shows (Plex and TvTime)
def processShows():
    global shows
    time.sleep(60)
    for tvId, show in shows.items():
        if 'tvtime' in show:
            if 'plex' in show:
                # Compare watch count
                if(show['tvtime']>show['plex']):
                    addPlexWatched(tvId, show)
                    time.sleep(config.tvtime["auth"]['rate_time']) # Rate limit safety
                elif(show['tvtime']<show['plex']):
                    addTvTimeWatched(tvId, show)
                    time.sleep(config.tvtime["auth"]['rate_time']) # Rate limit safety
                else:
                    pass
                    # Same amount on both --> do nothing
            else:
                pass
                # Not on plex --> do nothing
        else:
            addToTvTime(tvId, show)
            time.sleep(config.tvtime["auth"]['rate_time']) # Rate limit safety
            # Add to tv time

# Add show to Tv Time
def addToTvTime(tvId, showData):
    puts(colored.yellow('[Plex-TvTime-Agent]') + colored.cyan('[Phase 2]') +" Adding show ("+tvId+") to TvTime")
    global shows
    shows[tvId]["tvtime"] = 0;
    showData["tvtime"] = 0;

    # add to TvTime
    headers = {'User-Agent': config.tvtime["auth"]['user-agent'] }
    url_params = "?access_token="+access_token+"&show_id="+tvId
    data = {'show_id': str(tvId)}
    request = requests.post(config.tvtime["urls"]['follow']+url_params,data=data, headers=headers)
    request_json = request.json()
    if(request_json["result"] == "OK"):
        puts(colored.yellow('[Plex-TvTime-Agent]') + colored.cyan('[Phase 2]') + colored.green('[Success]') + " Added show ("+tvId+")")
        #add episodes
        time.sleep(config.tvtime["auth"]['rate_time']) # Rate limit safety
        addTvTimeWatched(tvId, showData)
    else:
        puts(colored.yellow('[Plex-TvTime-Agent]') + colored.cyan('[Phase 2]') + colored.red('[Error]') + " Failed to add show ("+tvId+")")
        
# Add watched to Tv Time
def addTvTimeWatched(tvId, showData):
    puts(colored.yellow('[Plex-TvTime-Agent]') + colored.cyan('[Phase 2]') +" Adding Episode Watched from show ("+str(tvId)+") to TvTime")
    # get seasons from Plex
    headers = {'User-Agent': config.tvtime["auth"]['user-agent'], 'Accept': 'application/json' }
    url_params = "?X-Plex-Token="+config.plex["auth"]['token']
    url = config.plex["auth"]['server']+config.plex["urls"]['details'].replace("{plex_id}",str(showData['plex_id']))+url_params
    request = requests.get(url, headers=headers)
    request_json = request.json();

    season_id = ""
    season_index = ""
    viewed = ""
    run = False
    for season in request_json['MediaContainer']['Metadata']:
        if(season["viewedLeafCount"] == 0):
            pass
        else:
            if(season["leafCount"]>season["viewedLeafCount"] and not run):
                season_id = season["ratingKey"]
                season_index = season["index"]
                sub_headers = {'User-Agent': config.tvtime["auth"]['user-agent'], 'Accept': 'application/json' }
                sub_url_params = "?X-Plex-Token="+config.plex["auth"]['token']
                sub_url = config.plex["auth"]['server']+config.plex["urls"]['details'].replace("{plex_id}",str(season_id))+sub_url_params
                sub_request = requests.get(sub_url, headers=sub_headers)
                sub_request_json = sub_request.json();
                for episode in sub_request_json['MediaContainer']['Metadata']:
                    if( "viewCount" in episode):
                        viewed = episode["index"]
                    else:
                        if(not run):
                            run = True
                            time.sleep(config.tvtime["auth"]['rate_time']) # Rate limit safety
                            tt_headers = {'User-Agent': config.tvtime["auth"]['user-agent'] }
                            tt_url_params = "?access_token="+access_token+"&show_id="+str(tvId)+"&season="+str(season_index)+"&episode="+str(viewed)
                            tt_data = {'show_id': str(tvId)}
                            tt_request = requests.post(config.tvtime["urls"]['progress']+tt_url_params,data=tt_data, headers=tt_headers)
                            tt_request_json = tt_request.json()
                            try:
                                if(tt_request_json["result"] == "OK"):
                                    puts(colored.yellow('[Plex-TvTime-Agent]') + colored.cyan('[Phase 2]') + colored.green('[Success]') + " set show ("+tvId+") to S"+str(season_index)+":E"+str(viewed))
                                else:
                                    puts(colored.yellow('[Plex-TvTime-Agent]') + colored.cyan('[Phase 2]') + colored.red('[Error]') + " Failed to set show ("+tvId+") to S"+str(season_index)+":E"+str(viewed))
                                    print(config.tvtime["urls"]['progress']+url_params)
                            except Exception as e:
                                print(config.tvtime["urls"]['progress']+tt_url_params)
                                print(tt_request,tt_request_json)
                                print(e)
                        
                        
            else:
                season_id = season["ratingKey"]
                season_index = season["index"]
                viewed = season["viewedLeafCount"]
    
# Add watched to Plex
def addPlexWatched(tvId, showData):
    puts(colored.yellow('[Plex-TvTime-Agent]') + colored.cyan('[Phase 2]') +" Adding show watched ("+tvId+") to Plex")
    # Get TvTime data
    tt_data = {}
    headers = {'User-Agent': config.tvtime["auth"]['user-agent'] }
    url_params = "?access_token="+access_token+"&include_episodes=true&show_id="+tvId
    request = requests.get(config.tvtime["urls"]['show']+url_params, headers=headers)
    request_json = request.json()
    for episode in request_json['show']["episodes"]:
        if(episode["season_number"] in tt_data):
            tt_data[episode["season_number"]][episode["number"]] = episode["seen"]
        else:
            tt_data[episode["season_number"]] = {}
            tt_data[episode["season_number"]][episode["number"]] = episode["seen"]
    
    # get plex seasons
    p_headers = {'User-Agent': config.tvtime["auth"]['user-agent'], 'Accept': 'application/json' }
    p_url_params = "?X-Plex-Token="+config.plex["auth"]['token']
    p_url = config.plex["auth"]['server']+config.plex["urls"]['details'].replace("{plex_id}",str(showData["plex_id"]))+p_url_params
    p_request = requests.get(p_url, headers=p_headers)
    p_request_json = p_request.json();

    for season in p_request_json['MediaContainer']['Metadata']:
        if(season["index"] in tt_data):
            p_s_headers = {'User-Agent': config.tvtime["auth"]['user-agent'], 'Accept': 'application/json' }
            p_s_url_params = "?X-Plex-Token="+config.plex["auth"]['token']
            p_s_url = config.plex["auth"]['server']+config.plex["urls"]['details'].replace("{plex_id}",str(season["ratingKey"]))+p_s_url_params
            p_s_request = requests.get(p_s_url, headers=p_s_headers)
            p_s_request_json = p_s_request.json();
            for episode in p_s_request_json['MediaContainer']['Metadata']:
                if episode["index"] in tt_data[season["index"]]:
                    if bool(tt_data[season["index"]][episode["index"]]):
                        view_headers = {'User-Agent': config.tvtime["auth"]['user-agent'], 'Accept': 'application/json' }
                        view_url_params = "&X-Plex-Token="+config.plex["auth"]['token']
                        view_url = config.plex["auth"]['server']+config.plex["urls"]['watched'].replace("{item_id}",str(episode["ratingKey"]))+view_url_params
                        view_request = requests.get(view_url, headers=view_headers)
                        if(view_request.status_code != 200):
                            print("setting scrobble url:",view_url)
        else:
            puts(colored.yellow('[Plex-TvTime-Agent]') + colored.cyan('[Phase 2]') + colored.green('[Success]') + " Added show ("+tvId+")")


# Run code
startup()