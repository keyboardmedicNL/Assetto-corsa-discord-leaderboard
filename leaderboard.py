import time
import json
import requests
import os
import glob
from os.path import exists
import re
import configparser
import math
import threading
from subprocess import call

##### variables #####
logPath = "\\logs\\"
configp = configparser.ConfigParser(strict=False)

##### functions #####


### file checks ###

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

# checks if server folder contains assettoserver.exe used to filter results
def hasassettoserver():
    if exists(f"{serverspath}\\{file}\\\\assettoserver.exe"):
        return("assettoserver")
    elif exists(f"{serverspath}\\{file}\\\\acServer.exe"):
        return("acserver")
    else:
        return("none")



### score and time find ###

# reads log and extracts shmoovin scores for assettoserver
def scorefind():
    if not exists(f"{serverspath}\\{file}\\leaderboard.txt"):
        with open(f"{serverspath}\\{file}\\leaderboard.txt", 'w') as leaderboard:
            leaderboard.write("")
            print(f"leaderboard was not found so it was created for server {file}")
    pathToLogs = f"{serverspath}\\{file}{logPath}*"
    list_of_files = glob.glob(pathToLogs)
    sorted_files = sorted(list_of_files, key=os.path.getctime)
    latest_file = str(sorted_files[-1])
    print(f"Log file that is being read is: {latest_file} for server {file}")
    # opens and loops trough last logfile to find score entries and writes them to leaderboard.txt
    with open(latest_file, encoding='utf-8', errors='ignore' "r") as f:
        loglines = f.readlines()
        for il,logline in enumerate(loglines):
            hasscore = False
            name = ""
            score = ""
            x = re.search(".* \[INF\] CHAT:.* just scored a.*", logline)
            xx = re.search(".* \[INF\] CHAT:.* Drift.", logline)
            if str(xx) != "None":
                # formats logline to variables to use for leaderboard entry
                hasscore = True 
                print(f"found score on: {logline.strip()} for server {file}")
                x = logline.split(" Drift:")
                nameArray = x[0].split("CHAT: ")
                nameNoID = nameArray[1].split(" (")
                x[0] = nameNoID[0]
                name = x[0]
                score = float(x[1])
            elif str(x) != "None": 
                # formats logline to variables to use for leaderboard entry 
                hasscore = True 
                print(f"found score on: {logline.strip()} for server {file}")
                x = logline.split("): just scored a ")
                nameArray = x[0].split("CHAT: ")
                x[0] = nameArray[1].split(" (")[0]
                name = x[0]
                score = float(x[1])
            # loops in reverse to find input device used by whoever got the laptime, then formats the entry
            if hasscore:
                input_method = "Unknown"
                for ii,input_line in enumerate(reversed(loglines)):
                    if ii > len(loglines)-il and ii < len(loglines):
                        has_input_rgx = re.search(".* \[INF\] CSP handshake received from.*InputMethod=.*", input_line)
                        if str(has_input_rgx) != "None" and str(name) in input_line:
                            print(f"found input method on: {input_line.strip()} for server {file}")
                            input_split = input_line.split("InputMethod=\"")[1]
                            input_method = input_split.split("\" Rain")[0]
                            break
                if input_method == "Unknown":
                    try:
                        print(f"could not find input method in current log for {str(name)}, trying in second latest log file {str(sorted_files[-2])}")
                        with open(str(sorted_files[-2]), encoding='utf-8', errors='ignore' "r") as f:
                            loglines_second_last = f.readlines()
                        for input_line in reversed(loglines_second_last):
                            has_input_secondary_rgx = re.search(".* \[INF\] CSP handshake received from.*InputMethod=.*", input_line)
                            if str(has_input_secondary_rgx) != "None" and str(name) in input_line:
                                print(f"found input method on: {input_line.strip()} for server {file}")
                                input_split = input_line.split("InputMethod=\"")[1]
                                input_method = input_split.split("\" Rain")[0]
                                break
                    except:
                        print(f"could not find input method in current log for {str(name)}")
                # writes obtained scores to leaderboard.txt if score < recorded score for user with same name and car
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
                                entry = f"{name},{score},{input_method}\n"
                                leaderboardlines[leaderboardlines.index(leaderboardline)] = ""
                                leaderboardlinesnew.append(entry)
                                print(f"new record for {name} with score {score} with input method {input_method} for server {file}")
                    if wasfound == False:
                        entry = f"{name},{score},{input_method}\n"
                        leaderboardlinesnew.append(entry)
                        print(f"new record for {name} with score {score} with input method {input_method} on server {file}")
                    leaderboardlinescomb = leaderboardlines + leaderboardlinesnew
                    leaderboardwrite = ''.join(leaderboardlinescomb)
                    leaderboard.seek(0)
                    leaderboard.truncate()
                    leaderboard.write(leaderboardwrite)

# reads log and extracts laptimes for assettoserver
def timefind():
    if not exists(f"{serverspath}\\{file}\\laptimes.txt"):
        with open(f"{serverspath}\\{file}\\laptimes.txt", 'w') as leaderboard:
            leaderboard.write("")
            print(f"laptimes was not found so it was created for server {file}")
    pathToLogs = f"{serverspath}\\{file}{logPath}*"
    list_of_files = glob.glob(pathToLogs)
    sorted_files = sorted(list_of_files, key=os.path.getctime)
    latest_file = str(sorted_files[-1])
    print(f"Log file that is being read is: {latest_file} for server {file}")
    # opens and loops trough last logfile to find score entries and writes them to laptimes.txt
    with open(latest_file, encoding='utf-8', errors='ignore' "r") as f:
        loglines = f.readlines()
    for il,logline in enumerate(loglines):
        hasscore = False
        name = ""
        score = ""
        has_lap = re.search(".* \[INF\] Lap completed by.* 0 cuts.*", logline)
        if str(has_lap) != "None":
            # formats logline to variables to use for laptime entry
            hasscore = True 
            print(f"found laptime on: {logline.strip()} for server {file}")
            lap_split = logline.split(" cuts, laptime ")
            nameArray = lap_split[0].split("Lap completed by ")
            lap_split[0] = nameArray[1].split(",")[0]
            name = lap_split[0]
            score = float(lap_split[1])
            # loops in reverse to find car driven by whoever got the laptime, then formats the entry
            car = "none"
            for ic,carline in enumerate(reversed(loglines)):
                if ic > len(loglines)-il and ic < len(loglines):
                    has_car_rgx = re.search(".* \[INF\] .* has connected", carline)
                    if str(has_car_rgx) != "None" and str(name) in carline:
                        print(f"found car on: {carline.strip()} for server {file}")
                        car_split = carline.split(" (")
                        carArray = car_split[2].split(")) has connected")
                        car = carArray[0]
                        break
            if car == "none":
                print(f"could not find car entry in current log for {str(name)}, trying in second latest log file {str(sorted_files[-2])}")
                with open(str(sorted_files[-2]), encoding='utf-8', errors='ignore' "r") as f:
                    loglines_second_last = f.readlines()
                for carline in reversed(loglines_second_last):
                    has_car_secondary_rgx = re.search(".* \[INF\] .* has connected", carline)
                    if str(has_car_secondary_rgx) != "None" and str(name) in carline:
                        print(f"found car on: {carline.strip()} for server {file}")
                        car_split = carline.split(" (")
                        carArray = car_split[2].split(")) has connected")
                        car = carArray[0]
                        break
            # loops in reverse to find input device used by whoever got the laptime, then formats the entry
            input_method = "Unknown"
            for ii,input_line in enumerate(reversed(loglines)):
                if ii > len(loglines)-il and ii < len(loglines):
                    has_input_rgx = re.search(".* \[INF\] CSP handshake received from.*InputMethod=.*", input_line)
                    if str(has_input_rgx) != "None" and str(name) in input_line:
                        print(f"found input method on: {input_line.strip()} for server {file}")
                        input_split = input_line.split("InputMethod=\"")[1]
                        input_method = input_split.split("\" Rain")[0]
                        break
            if input_method == "Unknown":
                try:
                    print(f"could not find input method in current log for {str(name)}, trying in second latest log file {str(sorted_files[-2])}")
                    with open(str(sorted_files[-2]), encoding='utf-8', errors='ignore' "r") as f:
                        loglines_second_last = f.readlines()
                    for input_line in reversed(loglines_second_last):
                        has_input_secondary_rgx = re.search(".* \[INF\] CSP handshake received from.*InputMethod=.*", input_line)
                        if str(has_input_secondary_rgx) != "None" and str(name) in input_line:
                            print(f"found input method on: {input_line.strip()} for server {file}")
                            input_split = input_line.split("InputMethod=\"")[1]
                            input_method = input_split.split("\" Rain")[0]
                            break
                except:
                    print(f"could not find input method in current log for {str(name)}")
                # writes obtained laptime to laptimes.txt if laptime < recorded laptime for user with same name and car
            with open(f"{serverspath}\\{file}\\laptimes.txt", encoding='utf-8', errors='ignore', mode="r+") as leaderboard:
                leaderboardlinesnew = []
                wasfound = False
                leaderboardlines = leaderboard.readlines()
                for leaderboardline in leaderboardlines:
                    # extra logic to avoid issues when manually editing laptimes.txt
                    if str(leaderboardline) == "\n":
                        leaderboardlines[leaderboardlines.index(leaderboardline)] = ""
                    if "\n" not in str(leaderboardline):
                        leaderboardlines[leaderboardlines.index(leaderboardline)] = leaderboardline+"\n"
                    # actual logic to save laptime to laptimes.txt
                    if name in leaderboardline and car in leaderboardline:
                            wasfound = True
                            leaderboardlineArray = leaderboardline.split(',')
                            oldscore = leaderboardlineArray[2]
                            if score < float(oldscore):
                                entry = f"{car},{name},{score},{input_method}\n"
                                leaderboardlines[leaderboardlines.index(leaderboardline)] = ""
                                leaderboardlinesnew.append(entry)
                                print(f"new laptime for {name} in {car} with time {score} input method {input_method} for server {file}")
                if wasfound == False:
                    entry = f"{car},{name},{score},{input_method}\n"
                    leaderboardlinesnew.append(entry)
                    print(f"new laptime for {name} in {car} with time {score} and input method {input_method} for server {file}")
                leaderboardlinescomb = leaderboardlines + leaderboardlinesnew
                leaderboardwrite = ''.join(leaderboardlinescomb)
                leaderboard.seek(0)
                leaderboard.truncate()
                leaderboard.write(leaderboardwrite)

# find laptimes for acServer sessions
def findtimevanilla():
    if not exists(f"{serverspath}\\{file}\\laptimes.txt"):
        with open(f"{serverspath}\\{file}\\laptimes.txt", 'w') as leaderboard:
            leaderboard.write("")
            print(f"laptimes was not found so it was created for server {file}")
    pathToResults = f"{serverspath}\\{file}\\results\\*"
    list_of_files = glob.glob(pathToResults)
    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"results file that is being read is: {latest_file} for server {file}")
    with open(latest_file, encoding='utf-8', errors='ignore' "r") as f:
        resultsJson = json.load(f)
    for result in resultsJson["Result"]:
        name = result["DriverName"]
        car = result["CarModel"]
        score = result["BestLap"]
        if name != "" and score != 999999999:
             with open(f"{serverspath}\\{file}\\laptimes.txt", encoding='utf-8', errors='ignore', mode="r+") as leaderboard:
                    leaderboardlinesnew = []
                    wasfound = False
                    leaderboardlines = leaderboard.readlines()
                    for leaderboardline in leaderboardlines:
                        # extra logic to avoid issues when manually editing laptimes.txt
                        if str(leaderboardline) == "\n":
                            leaderboardlines[leaderboardlines.index(leaderboardline)] = ""
                        if "\n" not in str(leaderboardline):
                            leaderboardlines[leaderboardlines.index(leaderboardline)] = leaderboardline+"\n"
                        # actual logic to save laptime to laptimes.txt
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




### sorting and formatting ####

# sorts leaderboard in list per entry within 1 master list, highest score on top
def sortleaderboard():
    scores = []
    with open(f"{serverspath}\\{file}\\leaderboard.txt", 'r', encoding='utf-8', errors='ignore') as leaderboardfile:
        for line in leaderboardfile:
            try:
                name, score, input_method = line.split(',')
            except:
                name, score= line.split(',')
                input_method = "Unknown"
            score = score.strip()
            scores.append([name, score, input_method])
    scores.sort(key=lambda s: float(s[1]), reverse = True)
    print(f"sorted leaderboardfile for server {file}")
    return(scores)

# sort laptimes in list per entry within 1 master list, fastest lap on top
def sorttimes():
    scores = []
    with open(f"{serverspath}\\{file}\\laptimes.txt", 'r', encoding='utf-8', errors='ignore') as leaderboardfile:
        for line in leaderboardfile:
            try:
                car, name, score, input_method = line.split(',')
            except:
                car, name, score= line.split(',')
                input_method = "Unknown"
            score = score.strip()
            scores.append([car, name, score, input_method])
    scores.sort(key=lambda s: float(s[2]), reverse = False)
    print(f"sorted laptimes for server {file}")
    return(scores)

#sorts times if class configuration is present, outputs lists per class within 1 master list
def sorttimesclass(scores,classcfg):
    filteredtimes = []
    for classselected in classcfg:
        filtered = []
        for score in scores:
            carnamesplit = score[0].split("-")
            # checks if carname that is recorded exsists in the classcfg list that it is currently itterating over
            if str(carnamesplit[0]) in str(classcfg[classselected]):
                allreadyin = False
                for entry in filtered:
                    if str(score[1]) in str(entry):
                        allreadyin = True
                        if str(score[2]) < str(entry[2]):
                            filtered.append(score)
                if not allreadyin:
                    filtered.append(score)
        filteredtimes.append(filtered)
    print(f"sorted laptimes for server with multiclass {file}")
    return(filteredtimes)

# formats scores to str to use in webhook
def formatleaderboard(scores,doc_type):
    finallist = []
    finallist_html = []
    scorecounter = 0
    scorelength = len(scores)
    finalstr = "currently empty"
    finalstr_html = "<div class=\"namebox\">\n<p>currently empty</p>\n</div>\n"
    if scorelength >= leaderboardlimit:
        scorelength = leaderboardlimit
    for score in scores:
        scorecounter = scorecounter + 1
        if scorecounter <= scorelength:
            score_input = score[2].strip()
            if doc_type == "discord":
                if show_input == "true":
                    finallist.append(f"{scorecounter}. {score[0]} - {score_input} - {score[1]}\n")
                else:
                    finallist.append(f"{scorecounter}. {name} {score_from_file}\n")
            if doc_type == "html":
                if "gamepad" in str(score[2].lower()):
                    score_input = score[2].replace("Gamepad", "Control")
                elif "Keyboard" in str(score[2].lower()):
                    score_input = score[2].replace("Keyboard", "Keyboard")
                if show_input == "true":
                    finallist.append(f"{scorecounter}. {score[0]} - {score_input} -  {score[1]}\n")
                    short_name = str(score[0])[0:8]
                    html_score_format = f"<b>{short_name}</b> {score_input} {str(score[1])}"
                    finallist_html.append(f"<div class=\"namebox\">\n<p> {scorecounter}. {html_score_format}</p>\n</div>\n")
                else:
                    finallist.append(f"{scorecounter}. {name} {score_from_file}\n")
                    short_name = str(score[0])[0:8]
                    html_score_format = f"<b>{short_name}</b> {str(score[1])}"
                    finallist_html.append(f"<div class=\"namebox\">\n<p>{scorecounter}. {html_score_format}</p>\n</div>\n")
            finalstr = "".join(finallist)
            finalstr_html = "".join(finallist_html)
        else:
            break
    print(f"formatted leaderboard for server {file}")
    if doc_type == "discord":
        return(finalstr)
    elif doc_type == "html":
        return(finalstr_html)

#formats laptimes to str to use in webhook
def formattimes(scores,doc_type):
    finallist = []
    finallist_html = []
    scorecounter = 0
    scorelength = len(scores)
    finalstr = "currently empty"
    finalstr_html = "<div class=\"namebox\">\n<p>currently empty</p>\n</div>\n"
    if scorelength >= leaderboardlimit:
        scorelength = leaderboardlimit
    for score in scores:
        allreadyin = False
        name = score[1]  
        for entry in finallist:
            if str(name) in str(entry):
                allreadyin = True
        if scorecounter <= scorelength-1 and allreadyin != True:
            scorecounter = scorecounter + 1
            # math to convert from ms to minutes:seconds.miliseconds
            laptime = float(score[2])
            minutes= math.floor(laptime/(1000*60)%60)
            laptime = (laptime-(minutes*(1000*60)))
            seconds = (laptime/1000)
            score_input = score[3].strip()
            if doc_type == "discord":
                if show_input == "true":
                    finallist.append(f"{scorecounter}. {score[1]} - {score_input} - {minutes}:{seconds}\n")
                else:
                    finallist.append(f"{scorecounter}. {score[1]} - {minutes}:{seconds}\n")
            elif doc_type == "html":
                if "gamepad" in str(score[3].lower()):
                    score_input = score[3].replace("Gamepad", "Control")
                elif "Keyboard" in str(score[3].lower()):
                    score_input = score[3].replace("Keyboard", "Keyboard")
                if show_input == "true":
                    finallist.append(f"{scorecounter}. {score[1]} - {score_input} - {minutes}:{seconds}\n")
                    short_name = str(score[1])[0:8]
                    html_score_format = f"<b>{short_name}</b> - {score_input} - {minutes}:{seconds}"
                    finallist_html.append(f"<div class=\"namebox\">\n<p>{scorecounter}. {html_score_format}</p>\n</div>\n")
                else:
                    finallist.append(f"{scorecounter}. {score[1]} - {minutes}:{seconds}\n")
                    short_name = str(score[1])[0:8]
                    html_score_format = f"<b>{short_name}</b> {minutes}:{seconds}"
                    finallist_html.append(f"<div class=\"namebox\">\n<p>{scorecounter}. {html_score_format}</p>\n</div>\n")
            finalstr = "".join(finallist)
            finalstr_html = "".join(finallist_html)
    print(f"formatted laptimes for server {file}")
    if doc_type == "discord":
        return(finalstr)
    elif doc_type == "html":
        return(finalstr_html)

# formats laptimes if class configuration is present to str for use in webhook
def formattimesclass(scores,classcfg,doc_type):
    finallist = []
    classlist = []
    finallist_html = []
    for classname in classcfg:
        classlist.append(classname)
    for i,score in enumerate(scores):
        scorelength = len(score)
        scorecounter = 0
        if scorelength > 0:
            if doc_type == "discord":
                finallist.append(f"\n***class: {str(classlist[i])}***:\n")
            elif doc_type == "html":
                finallist_html.append(f"\n<div class=\"classbox\">\n<h3>class: {str(classlist[i])}</h3>\n</div>\n")
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
                score_input = classcore[3].strip()
                if doc_type == "discord":
                    if show_input == "true":
                        finallist.append(f"{scorecounter}. {classcore[1]} - {score_input} - {minutes}:{seconds}\n")
                    else:
                        finallist.append(f"{scorecounter}. {classcore[1]} - {minutes}:{seconds}\n")
                elif doc_type == "html":
                    if "gamepad" in str(classcore[3].lower()):
                        score_input = classcore[3].replace("Gamepad", "Control")
                    elif "Keyboard" in str(classcore[3].lower()):
                        score_input = classcore[3].replace("Keyboard", "Keyboard")
                    if show_input == "true":
                        finallist.append(f"{scorecounter}. {classcore[1]} - {score_input} - {minutes}:{seconds}\n")
                        short_name = str(classcore[1])[0:8]
                        html_score_format = f"<b>{short_name}</b> - {score_input} - {minutes}:{seconds}"
                        finallist_html.append(f"<div class=\"namebox\">\n<p>{scorecounter}. {html_score_format}</p>\n</div>\n")
                    else:
                        finallist.append(f"{scorecounter}. {classcore[1]} - {minutes}:{seconds}\n")
                        short_name = str(classcore[1])[0:8]
                        html_score_format = f"<b>{short_name}</b> {minutes}:{seconds}"
                        finallist_html.append(f"<div class=\"namebox\">\n<p>{scorecounter}. {html_score_format}</p>\n</div>\n")
    finalstr = "".join(finallist)
    finalstr_html = "".join(finallist_html)
    if finalstr == "":
        finalstr = "currently empty"
        finalstr_html = "<div class=\"namebox\">\n<p>currently empty</p>\n</div>\n"
    print(f"formatted leaderboard for server with multiclass {file}")
    if doc_type == "discord":
        return(finalstr)
    elif doc_type == "html":
        return(finalstr_html)
           
# formats and sends to html files for webserver
def sendtohtml(finalstr,finaltimes,hasshmoovin):
    configp.read(f"{serverspath}\\{file}\\cfg\\server_cfg.ini")
    name = str(configp['SERVER']['NAME'])
    try:
        configp.read(f"{serverspath}\\{file}\\cfg\\csp_extra_options.ini")
        scripttype = str(configp['SCRIPT_...']['SCRIPT'])
        scripttype = scripttype.replace("'","")
        if scripttype  in overtakescript:
            description = "Shmoovin overtake leaderboard"
        elif scripttype in driftscript:
            description = "Shmoovin drift leaderboard"
    except:
        pass
    showtimes = True
    if exists(f"{serverspath}\\{file}\\\\discordbotcfg.json"):
        with open(f"{serverspath}\\{file}\\\\discordbotcfg.json") as config:
            configJson = json.load(config)
        try:
            showtimes = configJson["showlaptimes"]
            if showtimes.lower() == "false":
                showtimes = False
        except:
            pass
    if not exists(f"html"):
        os.mkdir("html")
    pre_html = ("""<html>
                        <head>
                        <style>
                        body {
                            font-family: verdana; 
                            }
                        .namebox {
                            width: 320px;
                            line-height:1%;
                            padding: 1px;
                            padding-right: 10px;
                            margin: 2px;
                            background-color: #000000;
                            color: white;
                            border-right-style: solid;
                            border-color: orange;
                            text-align: right;
                            }
                        .classbox {
                            width: 320px;
                            line-height:100%;
                            padding: 1px;
                            padding-right: 10px;
                            margin: 2px;
                            background-color: orange;
                            color: white;
                            border-right-style: solid;
                            border-color: orange;
                            text-align: right;
                            }
                        .titlebox {
                            width: 320px;
                            line-height:200%;
                            padding: 1px;
                            padding-right: 10px;
                            margin: 2px;
                            background-color: black;
                            color: white;
                            border-right-style: solid;
                            border-color: orange;
                            word-wrap: break-word;
                            text-align: right;
                            }
                        </style>
                        </head>
                        <body>
                        <div class="titlebox">""")
    refresh_script = "<script>setTimeout(function(){location.reload()},10000);</script>"
    if showtimes:
        times_html = f"{pre_html}<h1>{str(name)}</h1>\n</div>{finaltimes}\n{refresh_script}"
        if exists (f"html/{file}-times.html"):
            with open(f"html/{file}-times.html", encoding='utf-8', errors='ignore', mode="r+") as html_lap_times:
                html_lap_times.seek(0)
                html_lap_times.truncate()
                html_lap_times.write(times_html)
                print(f"wrote laptimes to {file}-times.html for server {file}")
        else:
            with open(f"html/{file}-times.html", encoding='utf-8', errors='ignore', mode="w") as html_lap_times:
                html_lap_times.write(times_html)
                print(f"{file}-times.html was created with laptimes for server {file}")
    if hasshmoovin:
        shmoovin_html = f"{pre_html}<h1>{str(name)}</h1>\n</div>\n<div class=\"classbox\">\n<h3>{description}</h3>\n</div>\n{finalstr}\n{refresh_script}"
        if exists (f"html/{file}-shmoovin.html"):
            with open(f"html/{file}-shmoovin.html", encoding='utf-8', errors='ignore', mode="r+") as html_lap_times:
                html_lap_times.seek(0)
                html_lap_times.truncate()
                html_lap_times.write(shmoovin_html)
                print(f"wrote shmoovin scores to {file}-shmoovin.html for server {file}")
        else:
            with open(f"html/{file}-shmoovin.html", encoding='utf-8', errors='ignore', mode="w") as html_lap_times:
                html_lap_times.write(shmoovin_html)
                print(f"{file}-shmoovin.html was created with shmoovin scores for server {file}")

# formats message to send to discord, will send a message if it does not exsist yet for the server or update otherwise
def sendtowebhook(finalstr,finaltimes,hasshmoovin):
    configp.read(f"{serverspath}\\{file}\\cfg\\server_cfg.ini")
    name = str(configp['SERVER']['NAME'])
    # gets shmoovin script type from config
    try:
        configp.read(f"{serverspath}\\{file}\\cfg\\csp_extra_options.ini")
        scripttype = str(configp['SCRIPT_...']['SCRIPT'])
        scripttype = scripttype.replace("'","")
        if scripttype  in overtakescript:
            description = "Shmoovin overtake leaderboard"
        elif scripttype in driftscript:
            description = "Shmoovin drift leaderboard"
    except:
        pass
    # checks if laptimes should be shown
    showtimes = True
    if exists(f"{serverspath}\\{file}\\\\discordbotcfg.json"):
        with open(f"{serverspath}\\{file}\\\\discordbotcfg.json") as config:
            configJson = json.load(config)
        try:
            showtimes = configJson["showlaptimes"]
            if showtimes.lower() == "false":
                showtimes = False
        except:
            pass
    # checks if full server status should be shown and formats data for it
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
    # returns correct format based on selected parameters
    if onlyleaderboards.lower() == "false" and hasshmoovin and showtimes:
        print(f"posting/updating message with full server info, shmoovin and laptimes for server {file}")
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
    elif onlyleaderboards.lower() == "false" and not hasshmoovin and showtimes:
        print(f"posting/updating message with full server info and laptimes for server {file}")
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
                        }
                    ]
                }
            ]}
    elif onlyleaderboards.lower() == "false" and not hasshmoovin and not showtimes:
        print(f"posting/updating message with full server info for server {file}")
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
                        }
                    ]
                }
            ]}
    elif onlyleaderboards.lower() == "false" and hasshmoovin and not showtimes:
        print(f"posting/updating message with full server info and shmoovin for server {file}")
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
                            "name": description,
                            "value": finalstr
                        }
                    ]
                }
            ]}
    elif onlyleaderboards.lower() == "true" and hasshmoovin and showtimes:
        print(f"posting/updating message with shmoovin and laptimes for server {file}")
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
    elif onlyleaderboards.lower() == "true" and not hasshmoovin and showtimes:
        print(f"posting/updating message with laptimes for server {file}")
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
    elif onlyleaderboards.lower() == "true" and hasshmoovin and not showtimes:
        print(f"posting/updating message with shmoovin for server {file}")
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
    if exists(f"config/messages/{messagecounter}.txt"):
        with open(f"config/messages/{messagecounter}.txt") as File:
            messageid = str(File.readline())
        print(f"{messageid} read from {messagecounter}.txt")
        rl = requests.patch(f"{webhookurl}/messages/{messageid}", json=data, params={'wait': 'true'})
        if "200" in str(rl):
            print(f"discord message {messageid} updated")
        else:
            print(f"discord message {messageid} could not be updated")

    # creates leaderboard message if not allready created
    else:
        rl = requests.post(webhookurl, json=data, params={'wait': 'true'})
        rljson = rl.json()
        messageid = rljson["id"]
        print(f"discord webhook response for method post is {rl} ({messageid} posted)")
        if "200" in str(rl):
            print(f"discord message {messageid} posted")
        else:
            print(f"discord message {messageid} could not be posted")
        if not exists("config/messages"):
            os.mkdir("config/messages")
        with open(f"config/messages/{messagecounter}.txt", 'w') as File:
            File.write(f"{messageid}")
            print(f"{messageid} saved in file {messagecounter}.txt")
    time.sleep(1)

# deletes unused discord messages
def deletemessage():
    messagelst= os.listdir("config/messages")
    for index,message in enumerate(messagelst):
        if index > messagecounter:
            with open(f"config/messages/{message}") as File:
                messageid = str(File.readline())
            rl = requests.delete(f"{webhookurl}/messages/{messageid}",params={'wait': 'true'})
            if "204" in str(rl):
                print(f"discord message {messageid} is unused and is now deleted")
            else:
                print(f"discord message {messageid} could not be deleted")
            os.remove(f"config/messages/{message}")
            print(f"removing unused message file {message}")

# deletes unused html files
def delete_html():
    html_files = os.listdir("html")
    for html_file in html_files:
        html_matches_servername = False
        for file in filenames:
            if str(file) in str(html_file):
                html_matches_servername = True
        if not html_matches_servername:
            os.remove(f"html/{html_file}")
            print(f"remove {html_file} because it is no longer used")



##### main code ####

# load config
with open("config/config.json") as config:
    configJson = json.load(config)
    interval = configJson["interval"]
    serverspathlst = configJson["serverspath"]
    webhookurl = configJson["webhookurl"]
    folderidentifier = configJson["folderindentifier"]
    leaderboardlimit = configJson["leaderboardlimit"]
    driftscript = configJson["shmoovindrifturl"]
    overtakescript = configJson["shmoovinovertakeurl"]
    onlyleaderboards = configJson["onlyleaderboards"]
    serveradress = configJson["serveradress"]
    serveradressdisplay = configJson["serveradressdisplay"]
    show_input = configJson["show_input"]
    shmoovinurl = driftscript + overtakescript
    print("succesfully loaded config")

# main loop 
print("starting main loop")
while True:
    # loop trough folders in server folder
    messagecounter = -1
    for serverspath in serverspathlst:
        filenames= os.listdir(str(serverspath))
        print(f"list of folders to check: {filenames}")
        for file in filenames:
            # checks if folder is actually a server folder
            if folderidentifier in file.lower():
                messagecounter = messagecounter+1
                hasserver = hasassettoserver()
                if hasserver != "none":
                    # checks if shmoovin script exsists
                    hasshmoovin = shmoovincheck()
                    if hasshmoovin == True:
                        scorefind()
                        scores = sortleaderboard()
                        finalstr = formatleaderboard(scores,"discord")
                        finalstr_html = formatleaderboard(scores,"html")
                    else:
                        finalstr = "NA"
                        finalstr_html = "NA"
                    # gets laptimes and checks if classcfg exsists
                    if hasserver == "assettoserver":
                        timefind()
                    elif hasserver == "acserver":
                        findtimevanilla()
                    classcfg = hasclasscfg()
                    # logic if classcfg does exsist
                    if classcfg != False:
                        times = sorttimes()
                        timesperclass = sorttimesclass(times,classcfg)
                        finaltimes = formattimesclass(timesperclass,classcfg,"discord")
                        finaltimes_html = formattimesclass(timesperclass,classcfg,"html")
                    # logic if classcfg does not exsist
                    else:
                        times = sorttimes()
                        finaltimes = formattimes(times,"discord")
                        finaltimes_html = formattimes(times,"html")         
                    sendtowebhook(finalstr,finaltimes,hasshmoovin)
                    sendtohtml(finalstr_html,finaltimes_html,hasshmoovin)
        deletemessage()
        delete_html()
    print(f"waiting for {interval} minutes")
    time.sleep(interval*60)
