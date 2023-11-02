import time
import json
import requests
import os
import glob
from os.path import exists
import re
import configparser
import math

# variables
logPath = "\\logs\\"
configp = configparser.ConfigParser(strict=False)

# functions
# checks if shmoovin is present in config
def shmoovincheck():
    hasshmoovin = False
    if exists(f"{serverspath}\\{file}\\cfg\\csp_extra_options.ini"):
        with open(f"{serverspath}\\{file}\\cfg\\csp_extra_options.ini") as cspconf:
            cspconflines = cspconf.readlines()
            for line in cspconflines:
                for url in shmoovinurl:
                    if url in line and not ";" in line:
                        hasshmoovin = True
                        print(f"shmoovin script was found in server {file}")
    return(hasshmoovin)

# reads log and extracts scores
def scorefind():
    if not exists(f"{serverspath}\\{file}\\leaderboard.txt"):
        with open(f"{serverspath}\\{file}\\leaderboard.txt", 'w') as leaderboard:
            leaderboard.write("")
            print(f"leaderboard was not found so it was created for server {file}")
    pathToLogs = f"{serverspath}\\{file}{logPath}*"
    list_of_files = glob.glob(pathToLogs)
    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"Log file that is being read is: {latest_file} for server {file}")
    # opens and loops trough last logfile to find score entries and writes them to leaderboard.txt
    with open(latest_file, encoding='utf-8', errors='ignore' "r") as f:
        loglines = f.readlines()
        for logline in loglines:
            hasscore = False
            name = ""
            score = ""
            x = re.search(".* \[INF\] CHAT:.* just scored a.*", logline)
            xx = re.search(".* \[INF\] CHAT:.* Drift.", logline)
            if str(xx) != "None":
                hasscore = True 
                print(f"found score on: {logline.strip()} for server {file}")
                x = logline.split(" Drift:")
                nameArray = x[0].split("CHAT: ")
                nameNoID = nameArray[1].split(" (")
                x[0] = nameNoID[0]
                name = x[0]
                score = float(x[1])
            elif str(x) != "None":  
                hasscore = True 
                print(f"found score on: {logline.strip()} for server {file}")
                x = logline.split("): just scored a ")
                nameArray = x[0].split("CHAT: ")
                x[0] = nameArray[1].split(" (")[0]
                name = x[0]
                score = float(x[1])
            if hasscore: 
                with open(f"{serverspath}\\{file}\\leaderboard.txt", encoding='utf-8', errors='ignore', mode="r+") as leaderboard:
                    leaderboardlinesnew = []
                    wasfound = False
                    leaderboardlines = leaderboard.readlines()
                    for leaderboardline in leaderboardlines:
                        if str(leaderboardline) == "\n":
                            leaderboardlines[leaderboardlines.index(leaderboardline)] = ""
                        if "\n" not in str(leaderboardline):
                            leaderboardlines[leaderboardlines.index(leaderboardline)] = leaderboardline+"\n"
                        if name in leaderboardline:
                            wasfound = True
                            leaderboardlineArray = leaderboardline.split(',')
                            oldscore = leaderboardlineArray[1]
                            if float(score) > float(oldscore):
                                entry = f"{name},{score}\n"
                                leaderboardlines[leaderboardlines.index(leaderboardline)] = ""
                                leaderboardlinesnew.append(entry)
                                print(f"new record for {name} with score {score} for server {file}")
                    if wasfound == False:
                        entry = f"{name},{score}\n"
                        leaderboardlinesnew.append(entry)
                        print(f"new record for {name} with score {score} on server {file}")
                    leaderboardlinescomb = leaderboardlines + leaderboardlinesnew
                    print(f"list to write: {leaderboardlinescomb}")
                    leaderboardwrite = ''.join(leaderboardlinescomb)
                    leaderboard.seek(0)
                    leaderboard.truncate()
                    leaderboard.write(leaderboardwrite)

def timefind():
    if not exists(f"{serverspath}\\{file}\\laptimes.txt"):
        with open(f"{serverspath}\\{file}\\laptimes.txt", 'w') as leaderboard:
            leaderboard.write("")
            print(f"laptimes was not found so it was created for server {file}")
    pathToLogs = f"{serverspath}\\{file}{logPath}*"
    list_of_files = glob.glob(pathToLogs)
    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"Log file that is being read is: {latest_file} for server {file}")
    # opens and loops trough last logfile to find score entries and writes them to laptimes.txt
    with open(latest_file, encoding='utf-8', errors='ignore' "r") as f:
        loglines = f.readlines()
        for logline in loglines:
            hasscore = False
            name = ""
            score = ""
            x = re.search(".* \[INF\] Lap completed by.* 0 cuts.*", logline)
            if str(x) != "None":
                hasscore = True 
                print(f"found laptime on: {logline.strip()} for server {file}")
                x = logline.split(" cuts, laptime ")
                print(x)
                nameArray = x[0].split("Lap completed by ")
                x[0] = nameArray[1].split(",")[0]
                name = x[0]
                score = float(x[1])
                for carline in reversed(loglines):
                    xxx = re.search(".* \[INF\] .* has connected", carline)
                    if str(xxx) != "None" and str(name) in carline:
                        print(f"found car on: {carline.strip()} for server {file}")
                        x = carline.split(" (")
                        carArray = x[2].split(")) has connected")
                        car = carArray[0]
                        print(f"car is {car}")
                        break
                with open(f"{serverspath}\\{file}\\laptimes.txt", encoding='utf-8', errors='ignore', mode="r+") as leaderboard:
                    leaderboardlinesnew = []
                    wasfound = False
                    leaderboardlines = leaderboard.readlines()
                    for leaderboardline in leaderboardlines:
                        if str(leaderboardline) == "\n":
                            leaderboardlines[leaderboardlines.index(leaderboardline)] = ""
                        if "\n" not in str(leaderboardline):
                            leaderboardlines[leaderboardlines.index(leaderboardline)] = leaderboardline+"\n"
                        if name in leaderboardline and car in leaderboardline:
                                wasfound = True
                                leaderboardlineArray = leaderboardline.split(',')
                                oldscore = leaderboardlineArray[2]
                                if score < float(oldscore):
                                    entry = f"{car},{name},{score}\n"
                                    leaderboardlines[leaderboardlines.index(leaderboardline)] = ""
                                    leaderboardlinesnew.append(entry)
                                    print(f"new laptime for {name} in {car} with time {score} for server {file}")
                    if wasfound == False:
                        entry = f"{car},{name},{score}\n"
                        leaderboardlinesnew.append(entry)
                        print(f"new laptime for {name} in {car} with time {score} for server {file}")
                    leaderboardlinescomb = leaderboardlines + leaderboardlinesnew
                    leaderboardwrite = ''.join(leaderboardlinescomb)
                    leaderboard.seek(0)
                    leaderboard.truncate()
                    leaderboard.write(leaderboardwrite)

# sorts leaderboard in a list
def sortleaderboard():
    scores = []
    with open(f"{serverspath}\\{file}\\leaderboard.txt", 'r', encoding='utf-8', errors='ignore') as leaderboardfile:
        for line in leaderboardfile:
            name, score = line.split(',')
            score = score.strip()
            scores.append([name, score])
    scores.sort(key=lambda s: float(s[1]), reverse = True)
    return(scores)

# sort laptimes in a list
def sorttimes():
    scores = []
    with open(f"{serverspath}\\{file}\\laptimes.txt", 'r', encoding='utf-8', errors='ignore') as leaderboardfile:
        for line in leaderboardfile:
            car, name, score = line.split(',')
            score = score.strip()
            scores.append([car, name, score])
    scores.sort(key=lambda s: float(s[2]), reverse = False)
    return(scores)

#sorts times if class configuration is present
def sorttimesclass(scores,classcfg):
    filteredtimes = []
    for classselected in classcfg:
        filtered = []
        for cars in classcfg[classselected]:
            for score in scores:
                if str(cars) in str(score[0]):
                    filtered.append(score)
        filteredtimes.append(filtered)
    return(filteredtimes)

# formats scores to str to use in webhook
def formatleaderboard(scores):
    finallist = []
    scorecounter = 0
    scorelength = len(scores)
    finalstr = "currently empty"
    if scorelength >= leaderboardlimit:
        scorelength = leaderboardlimit
    for score in scores:
        scorecounter = scorecounter + 1
        if scorecounter <= scorelength:
            score_format = ' '.join(score)
            score_format = score_format.strip()
            finallist.append(f"{scorecounter}. {score_format}\n")
            finalstr = "".join(finallist)
        else:
            break
    return(finalstr)

#formats laptimes to str to use in webhook
def formattimes(scores):
    finallist = []
    scorecounter = 0
    scorelength = len(scores)
    finalstr = "currently empty"
    if scorelength >= leaderboardlimit:
        scorelength = leaderboardlimit
    for score in scores:
        scorecounter = scorecounter + 1
        if scorecounter <= scorelength:
            laptime = float(score[2])
            minutes= math.floor(laptime/(1000*60)%60)
            laptime = (laptime-(minutes*(1000*60)))
            seconds = (laptime/1000)
            score_format = f"{score[1]} {minutes}:{seconds}"
            finallist.append(f"{scorecounter}. {score_format}\n")
            finalstr = "".join(finallist)
        else:
            break
    return(finalstr)

# formats laptimes if class configuration is present
def formattimesclass(scores,classcfg):
    finallist = []
    classlist = []
    for classname in classcfg:
        classlist.append(classname)
    for i,score in enumerate(scores):
        scorelength = len(score)
        scorecounter = 0
        if scorelength > 0:
            finallist.append(f"{str(classlist[i])}:\n")
        if scorelength >= leaderboardlimit:
            scorelength = leaderboardlimit
        for classcore in scores[i]:
            scorecounter = scorecounter + 1
            if scorecounter <= scorelength:
                laptime = float(classcore[2])
                minutes= math.floor(laptime/(1000*60)%60)
                laptime = (laptime-(minutes*(1000*60)))
                seconds = (laptime/1000)
                score_format = f"{classcore[1]} {minutes}:{seconds}"
                finallist.append(f"{scorecounter}. {score_format}\n")
    finalstr = "".join(finallist)
    if finalstr == "":
        finalstr = "currently empty"
    print(finalstr)
    return(finalstr)

# checks if class config is present and returns it
def hasclasscfg():
    classcfg = False
    if exists(f"{serverspath}\\{file}\\\\discordbotcfg.json"):
        with open(f"{serverspath}\\{file}\\\\discordbotcfg.json") as config:
            configJson = json.load(config)
        try:
            classcfg = configJson["classes"]
        except:
            pass
    return(classcfg)
            

# send leaderboard to discord
def sendtowebhook(finalstr,finaltimes,hasshmoovin):
    configp.read(f"{serverspath}\\{file}\\cfg\\server_cfg.ini")
    name = str(configp['SERVER']['NAME'])
    configp.read(f"{serverspath}\\{file}\\cfg\\csp_extra_options.ini")
    scripttype = str(configp['SCRIPT_...']['SCRIPT'])
    scripttype = scripttype.replace("'","")
    if scripttype  in overtakescript:
        description = "Shmoovin overtake leaderboard"
    elif scripttype in driftscript:
        description = "Shmoovin drift leaderboard"
    if exists(f"{serverspath}\\{file}\\\\discordbotcfg.json"):
        with open(f"{serverspath}\\{file}\\\\discordbotcfg.json") as config:
            configJson = json.load(config)
        try:
            showtimes = configJson["showlaptimes"]
            if showtimes.lower() == "false":
                finaltimes = "NA"
            else:
                finaltimes = finaltimes
        except:
            pass
    else:
        finaltimes = finaltimes
    if onlyleaderboards.lower() == "false":
        configp.read(f"{serverspath}\\{file}\\cfg\\server_cfg.ini")
        httpport = str(configp['SERVER']['HTTP_PORT'])
        serverhttp = f"{serveradress}:{httpport}"
        try:
            rl = requests.get(f"http://{serverhttp}/INFO")
            print(f"server info response is: {rl} for server {file}")
            if "200" in str(rl):
                rljson = rl.json()
                clients = rljson["clients"]
                maxplayers = rljson["maxclients"]
                status = ":green_circle: Online"
                trackstr = rljson["track"]
                tracklst = trackstr.split("/")
                track = str(tracklst[-1])
            else:
                status = ":red_circle: Offline"
                maxplayers = "NA"
                clients = "NA"
                track = "NA"
        except Exception as e:
            status = ":red_circle: Offline"
            maxplayers = "NA"
            clients = "NA"
            track = "NA"
            print(f"an exception occured for server {file} {e}")
    if onlyleaderboards.lower() == "false" and hasshmoovin == True:
        data = {"embeds": [
                {
                    "title": name,
                    "description":"",
                    "fields": [
                        {
                            "name": f":race_car:",
                            "value": f"[***Click here to connect***](https://acstuff.ru/s/q:race/online/join?ip={serveradressdisplay}&httpPort={httpport})",
                        },
                        {
                            "name": "Status",
                            "value": status,
                            "inline": "true" 
                        },
                        {
                            "name": "Players",
                            "value": f":busts_in_silhouette: {clients}/{maxplayers}",
                            "inline": "true" 
                        },
                        {
                            "name": "Track",
                            "value": track,
                            "inline": "true" 
                        },
                        {
                            "name": "Laptimes",
                            "value": finaltimes
                        },
                        {
                            "name": description,
                            "value": finalstr
                        }
                    ]
                }
            ]}
    elif onlyleaderboards.lower() == "false" and hasshmoovin == False:
        data = {"embeds": [
                {
                    "title": name,
                    "description":"",
                    "fields": [
                        {
                            "name": f":race_car:",
                            "value": f"[***Click here to connect***](https://acstuff.ru/s/q:race/online/join?ip={serveradressdisplay}&httpPort={httpport})",
                        },
                        {
                            "name": "Status",
                            "value": status,
                            "inline": "true" 
                        },
                        {
                            "name": "Players",
                            "value": f":busts_in_silhouette: {clients}/{maxplayers}",
                            "inline": "true" 
                        },
                        {
                            "name": "Track",
                            "value": track,
                            "inline": "true" 
                        },
                        {
                            "name": "Laptimes",
                            "value": finaltimes
                        },
                    ]
                }
            ]}
    elif onlyleaderboards.lower() == "true" and hasshmoovin == True:
        data = {"embeds": [
                {
                    "title": name,
                    "description":"",
                    "fields": [
                        {
                            "name": "Laptimes",
                            "value": finaltimes
                        },
                        {
                            "name": description,
                            "value": finalstr
                        }
                    ]
                }
            ]}
    elif onlyleaderboards.lower() == "true" and hasshmoovin == False:
        data = {"embeds": [
                {
                    "title": name,
                    "description":"",
                    "fields": [
                        {
                            "name": "Laptimes",
                            "value": finaltimes
                        }
                    ]
                }
            ]}
    # checks if leaderboard message was allready created and updates it
    if exists(f"config/{file}.txt"):
        with open(f"config/{file}.txt") as File:
            messageid = str(File.readline())
        print(f"{messageid} read from {file}.txt")
        rl = requests.patch(f"{webhookurl}/messages/{messageid}", json=data, params={'wait': 'true'})
        print(f"discord webhook response for method patch is {rl} ({messageid} updated)")
    # creates leaderboard message if not allready created
    else:
        rl = requests.post(webhookurl, json=data, params={'wait': 'true'})
        rljson = rl.json()
        messageid = rljson["id"]
        print(f"discord webhook response for method post is {rl} ({messageid} posted)")
        with open(f"config/{file}.txt", 'w') as File:
            File.write(messageid)
            print(f"{messageid} saved in file {file}.txt")
    time.sleep(2)


# load config
with open("config/config.json") as config:
    configJson = json.load(config)
    interval = configJson["interval"]
    serverspath = configJson["serverspath"]
    webhookurl = configJson["webhookurl"]
    folderidentifier = configJson["folderindentifier"]
    leaderboardlimit = configJson["leaderboardlimit"]
    driftscript = configJson["shmoovindrifturl"]
    overtakescript = configJson["shmoovinovertakeurl"]
    onlyleaderboards = configJson["onlyleaderboards"]
    serveradress = configJson["serveradress"]
    serveradressdisplay = configJson["serveradressdisplay"]
    shmoovinurl = driftscript + overtakescript

# main loop
while True:
    filenames= os.listdir(serverspath)
    print(f"list of folders to check: {filenames}")
    # loop trough folders in server folder
    for file in filenames:
        # checks if folder is actually a server folder
        if folderidentifier in file.lower():
            hasshmoovin = shmoovincheck()
            if hasshmoovin == True:
                scorefind()
                scores = sortleaderboard()
                finalstr = formatleaderboard(scores)
            else:
                finalstr="NA"
            timefind()
            classcfg = hasclasscfg()
            if classcfg != False:
                times = sorttimes()
                timesperclass = sorttimesclass(times,classcfg)
                finaltimes = formattimesclass(timesperclass,classcfg)
            else:
                times = sorttimes()
                finaltimes = formattimes(times)        
            sendtowebhook(finalstr,finaltimes,hasshmoovin)
    print(f"waiting for {interval} minutes")
    time.sleep(interval*60)
