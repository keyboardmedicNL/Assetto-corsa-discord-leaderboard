import time
import json
import requests
import os
import glob
from os.path import exists
import re
import configparser

# variables
logPath = "\\logs\\"
configp = configparser.ConfigParser(strict=False)

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
    shmoovinurl = driftscript + overtakescript

# main loop
while True:
    filenames= os.listdir(serverspath)
    print(f"list of folders to check: {filenames}")
    # loop trough folders in server folder
    for file in filenames:
        # checks if folder is actually a server folder
        if folderidentifier in file.lower():
            hasshmoovin = False
            if exists(f"{serverspath}\\{file}\\cfg\\csp_extra_options.ini"):
             with open(f"{serverspath}\\{file}\\cfg\\csp_extra_options.ini") as cspconf:
                cspconflines = cspconf.readlines()
                for line in cspconflines:
                    for url in shmoovinurl:
                        if url in line and not ";" in line:
                            hasshmoovin = True
            if hasshmoovin == True:
                if not exists(f"{serverspath}\\{file}\\leaderboard.txt"):
                    with open(f"{serverspath}\\{file}\\leaderboard.txt", 'w') as leaderboard:
                        leaderboard.write("")
                print(f"folder is a server with name: {file}")
                pathToLogs = f"{serverspath}\\{file}{logPath}*"
                list_of_files = glob.glob(pathToLogs)
                latest_file = max(list_of_files, key=os.path.getctime)
                print(f"Log file that is being read is: {latest_file}")
                # opens and loops trough last logfile to find score entries
                with open(latest_file, encoding='utf-8', errors='ignore' "r") as f:
                    loglines = f.readlines()
                for logline in loglines:
                    x = re.search(".* \[INF\] CHAT:.* just scored a.*", logline)
                    xx = re.search(".* \[INF\] CHAT:.* Drift.", logline)
                    if str(x) != "None" or str(xx) != "None":   
                        print(f"found score on: {logline.strip()}")
                        loglineArray = logline.split()
                        name = loglineArray[5]
                        score = float(loglineArray[-1])
                        print(f"score is: {name} {score}")
                        # opens and reads leaderboard file, then writes scores to the file
                        with open(f"{serverspath}\\{file}\\leaderboard.txt", encoding='utf-8', errors='ignore', mode="r+") as leaderboard:
                            leaderboardlinesnew = []
                            wasfound = False
                            leaderboardlines = leaderboard.readlines()
                            print(f"file content before loop: {leaderboardlines}")
                            for leaderboardline in leaderboardlines:
                                if name in leaderboardline:
                                    wasfound = True
                                    print (f"{name} was found in leaderboard file")
                                    leaderboardlineArray = leaderboardline.split(',')
                                    oldscore = leaderboardlineArray[1]
                                    if score > float(oldscore):
                                        entry = f"{name},{score}\n"
                                        leaderboardlines.remove(leaderboardline)
                                        leaderboardlinesnew.append(entry)
                                        print(f"new record for {name} with score {score}")
                            if wasfound == False:
                                entry = f"{name},{score}\n"
                                leaderboardlinesnew.append(entry)
                            leaderboardlinescomb = leaderboardlines + leaderboardlinesnew
                            print(f"list to write: {leaderboardlinescomb}")
                            leaderboardwrite = ''.join(leaderboardlinescomb)
                            leaderboard.seek(0)
                            leaderboard.truncate()
                            leaderboard.write(leaderboardwrite)
                # sorts and sends top 10 leaderboard to discord webhook
                scores = []
                with open(f"{serverspath}\\{file}\\leaderboard.txt", 'r', encoding='utf-8', errors='ignore') as leaderboardfile:
                    for line in leaderboardfile:
                        name, score = line.split(',')
                        score = score.strip()
                        scores.append([name, score])
                scores.sort(key=lambda s: float(s[1]), reverse = True)
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
                # json format to send to the webhook
                time.sleep(2)
                configp.read(f"{serverspath}\\{file}\\cfg\\server_cfg.ini")
                name = str(configp['SERVER']['NAME'])
                configp.read(f"{serverspath}\\{file}\\cfg\\csp_extra_options.ini")
                scripttype = str(configp['SCRIPT_...']['SCRIPT'])
                scripttype = scripttype.replace("'","")
                if scripttype  in overtakescript:
                    description = "Shmoovin overtake leaderboard"
                elif scripttype in driftscript:
                    description = "Shmoovin drift leaderboard"
                data = {"embeds": [
                        {
                            "title": name,
                            "description":"",
                            "fields": [
                                {
                                    "name": description,
                                    "value": finalstr
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
    print(f"waiting for {interval} minutes")
    time.sleep(interval*60)
