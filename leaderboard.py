import time
import json
import requests
import os
import glob
from os.path import exists
import re
import configparser
import math

##### variables #####
logPath = "\\logs\\"
configp = configparser.ConfigParser(strict=False)

##### functions #####


### file checks ###

# checks if shmoovin is present in config
def shmoovin_check():
    has_shmoovin = False
    shmoovin_type = ""
    if exists(f"{serverspath}\\{file}\\cfg\\csp_extra_options.ini"):
        try:
            configp.read(f"{serverspath}\\{file}\\cfg\\csp_extra_options.ini")
            scripttype = str(configp['SCRIPT_...']['SCRIPT'])
            scripttype = scripttype.replace("'","")
            if scripttype  in overtakescript:
                shmoovin_type = "Shmoovin overtake leaderboard"
                has_shmoovin = True
            elif scripttype in driftscript:
                shmoovin_type = "Shmoovin drift leaderboard"
                has_shmoovin = True
        except:
            pass
    return(has_shmoovin,shmoovin_type)

# checks if class config is present and returns it
def has_classcfg():
    classcfg = {"none": ["none"]}
    if exists(f"{serverspath}\\{file}\\\\discordbotcfg.json"):
        with open(f"{serverspath}\\{file}\\\\discordbotcfg.json") as config:
            configJson = json.load(config)
        try:
            classcfg = configJson["classes"]
        except:
            pass
    return(classcfg)

# checks if server folder contains assettoserver.exe used to filter results
def server_type_check():
    if exists(f"{serverspath}\\{file}\\\\assettoserver.exe"):
        return("assettoserver")
    elif exists(f"{serverspath}\\{file}\\\\acServer.exe"):
        return("acserver")

# checks if laptimes file exsists and if not creates it
def has_score_file_check(file_name):
    if not exists(f"{serverspath}\\{file}\\{file_name}.txt"):
        with open(f"{serverspath}\\{file}\\{file_name}.txt", 'w') as score_file:
            score_file.write("")
            print(f"{file_name} was not found so it was created for server {file}")




### score and time find ###

# opens and loops trough last logfile to find score entries and writes them to the appropriate files
def score_find():
    for index_log_line,log_line in enumerate(log_lines):
        if str(re.search(".* \[INF\] CHAT:.* Drift.", log_line)) != "None":
            # formats logline to variables to use for drift entry
            print(f"found score on: {log_line.strip()} for server {file}")
            init_split = log_line.split(" Drift:")
            name_array = init_split[0].split("CHAT: ")
            name_no_id = name_array[1].split(" (")[0]
            name = name_no_id
            score = float(init_split[1])
            input_method = input_find(index_log_line,log_lines,name)
            car = find_car(index_log_line,log_lines,name)
            write_score(name,score,car,input_method,"leaderboard")
        elif str(re.search(".* \[INF\] CHAT:.* just scored a.*", log_line)) != "None": 
            # formats logline to variables to use for overtake entry 
            print(f"found score on: {log_line.strip()} for server {file}")
            init_split = log_line.split("): just scored a ")
            name_array = init_split[0].split("CHAT: ") 
            name = name_array[1].split(" (")[0]
            score = float(init_split[1])
            input_method = input_find(index_log_line,log_lines,name)
            car = find_car(index_log_line,log_lines,name)
            write_score(name,score,car,input_method,"leaderboard")
        elif str(re.search(".* \[INF\] Lap completed by.* 0 cuts.*", log_line)) != "None":
            # formats logline to variables to use for laptime entry
            print(f"found laptime on: {log_line.strip()} for server {file}")
            lap_split = log_line.split(" cuts, laptime ")
            name_array = lap_split[0].split("Lap completed by ")
            name = name_array[1].split(",")[0]
            score = float(lap_split[1])
            input_method = input_find(index_log_line,log_lines,name)
            car = find_car(index_log_line,log_lines,name)
            write_score(name,score,car,input_method,"laptimes")

# loop to find input method used by whoever got the score
def input_find(index_log_line,log_lines,name):      
    input_method = "Unknown"
    for index_input,input_line in enumerate(reversed(log_lines)):
        if index_input > len(log_lines)-index_log_line and index_input < len(log_lines):
            if str(re.search(".* \[INF\] CSP handshake received from.*InputMethod=.*", input_line)) != "None" and str(name) in input_line:
                print(f"found input method on: {input_line.strip()} for server {file}")
                input_split = input_line.split("InputMethod=\"")[1]
                input_method = input_split.split("\" Rain")[0]
                return(input_method)
                break
    if input_method == "Unknown":
        try:
            print(f"could not find input method in current log for {str(name)}, trying in second latest log file {str(sorted_files[-2])}")
            with open(str(sorted_files[-2]), encoding='utf-8', errors='ignore' "r") as second_log_file:
                loglines_second_last = second_log_file.readlines()
            for second_input_line in reversed(loglines_second_last):
                if str(re.search(".* \[INF\] CSP handshake received from.*InputMethod=.*", second_input_line)) != "None" and str(name) in input_line:
                    print(f"found input method on: {second_input_line.strip()} for server {file}")
                    input_split = second_input_line.split("InputMethod=\"")[1]
                    input_method = input_split.split("\" Rain")[0]
                    return(input_method)
                    break
        except:
            print(f"could not find input method for {str(name)}")
            return(input_method)

# loop to find car driven by whoever got the score
def find_car(index_log_line,log_lines,name):
    car = "none"
    for index_car_line,car_line in enumerate(reversed(log_lines)):
        if index_car_line > len(log_lines)-index_log_line and index_car_line < len(log_lines):
            if str(re.search(".* \[INF\] .* has connected", car_line)) != "None" and str(name) in car_line:
                print(f"found car on: {car_line.strip()} for server {file}")
                car_split = car_line.split(" (")
                car_array = car_split[2].split(")) has connected")
                car = car_array[0]
                return(car)
                break
    if car == "none":
        print(f"could not find car entry in current log for {str(name)}, trying in second latest log file {str(sorted_files[-2])}")
        with open(str(sorted_files[-2]), encoding='utf-8', errors='ignore' "r") as f:
            loglines_second_last = f.readlines()
        for car_line in reversed(loglines_second_last):
            if str(re.search(".* \[INF\] .* has connected", car_line)) != "None" and str(name) in car_line:
                print(f"found car on: {car_line.strip()} for server {file}")
                car_split = car_line.split(" (")
                car_array = car_split[2].split(")) has connected")
                car = car_array[0]
                return(car)
                break

# # writes obtained scores to appropriate file
def write_score(name,score,car,input_method,file_name):
    with open(f"{serverspath}\\{file}\\{file_name}.txt", encoding='utf-8', errors='ignore', mode="r+") as score_file:
        score_file_lines_new = []
        was_found = False
        score_file_lines = score_file.readlines()
        for score_file_line in score_file_lines:
            # extra logic to avoid issues when manually editing laptimes.txt
            if str(score_file_line) == "\n":
                score_file_lines[score_file_lines.index(score_file_line)] = ""
            if "\n" not in str(score_file_line):
                score_file_lines[score_file_lines.index(score_file_line)] = score_file_line+"\n"
            # actual logic to save laptime to laptimes.txt
            if name in score_file_line and car in score_file_line:
                    was_found = True
                    old_score = score_file_line.split(',')[2]
                    if score < float(old_score):
                        entry = f"{car},{name},{score},{input_method}\n"
                        score_file_lines[score_file_lines.index(score_file_line)] = ""
                        score_file_lines_new.append(entry)
                        print(f"new record for {name} in {car} with {score} and input method {input_method} for file {file_name} for server {file}")
        if was_found == False:
            entry = f"{car},{name},{score},{input_method}\n"
            score_file_lines_new.append(entry)
            print(f"new record for {name} in {car} with {score} and input method {input_method} for file {file_name} for server {file}")
        score_file.seek(0)
        score_file.truncate()
        score_file.write(''.join(score_file_lines + score_file_lines_new))

# find laptimes for acServer sessions
def findtimevanilla():
    latest_file = max(glob.glob(f"{serverspath}\\{file}\\results\\*"), key=os.path.getctime)
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

# sort scores in list per entry within 1 master list
def sort_score(score_type,classcfg):
    scores = []
    filtered_times = []
    with open(f"{serverspath}\\{file}\\{score_type}.txt", 'r', encoding='utf-8', errors='ignore') as score_file:
        for line in score_file:
            if score_type == "laptimes":
                try:
                    car, name, score, input_method = line.split(',')
                except:
                    car, name, score= line.split(',')
                    input_method = "Unknown"
            elif score_type == "leaderboard":
                try:
                    car, name, score, input_method = line.split(',')
                except:
                    try:
                        name, score, input_method = line.split(',')
                        car = "Unknown"
                    except:
                        name, score,= line.split(',')
                        input_method = "Unknown"
                        car = "Unknown"
            score = score.strip()
            scores.append([car, name, score, input_method])
    if score_type == "laptimes":
        scores.sort(key=lambda s: float(s[2]), reverse = False)
    elif score_type == "leaderboard":
        scores.sort(key=lambda s: float(s[2]), reverse = True)
    for class_selected in classcfg:
        filtered = []
        for score in scores:
            carname_split = score[0].split("-")
            # checks if carname that is recorded exsists in the classcfg list that it is currently itterating over
            if str(carname_split[0]) in str(classcfg[class_selected]) or class_selected == "none":
                allready_in = False
                for index_entry,entry in enumerate(filtered):
                    if str(score[1]) in str(entry):
                        allready_in = True
                        if score_type == "laptimes":
                            if float(score[2]) < float(entry[2]):
                                del filtered[index_entry]
                                filtered.append(score)
                        elif score_type == "leaderboard":
                            if float(score[2]) > float(entry[2]):
                                del filtered[index_entry]
                                filtered.append(score)
                if not allready_in:
                    filtered.append(score)
        filtered_times.append(filtered)
    print(f"sorted scores for server {file}")
    return(filtered_times)

# formats laptimes if class configuration is present to str for use in webhook
def format_scores(scores,classcfg,doc_type,score_type):
    finallist = []
    classlist = []
    finallist_html = []
    for classname in classcfg:
        classlist.append(classname)
    for i,score in enumerate(scores):
        scorelength = len(score)
        scorecounter = 0
        if scorelength > 0:
            if doc_type == "discord" and str(classlist[i]) != "none":
                finallist.append(f"\n***class: {str(classlist[i])}***:\n")
            elif doc_type == "html" and str(classlist[i]) != "none":
                finallist_html.append(f"\n<div class=\"classbox\">\n<h3>class: {str(classlist[i])}</h3>\n</div>\n")
        if scorelength >= leaderboardlimit:
            scorelength = leaderboardlimit
        for classcore in scores[i]:
            scorecounter = scorecounter + 1
            if scorecounter <= scorelength:
                if score_type == "laptimes":
                    laptime = float(classcore[2])
                    minutes= math.floor(laptime/(1000*60)%60)
                    laptime = (laptime-(minutes*(1000*60)))
                    seconds = (laptime/1000)
                    score_format = f"{minutes}:{seconds}"
                elif score_type == "leaderboard":
                    score_format = float(classcore[2])
                score_input = classcore[3].strip()
                if doc_type == "discord":
                    if show_input == "true":
                        finallist.append(f"{scorecounter}. {classcore[1]} - {score_input} - {score_format}\n")
                    else:
                        finallist.append(f"{scorecounter}. {classcore[1]} - {score_format}\n")
                elif doc_type == "html":
                    if show_input == "true":
                        finallist.append(f"{scorecounter}. {classcore[1]} - {score_input} - {score_format}\n")
                        short_name = str(classcore[1])[0:8]
                        html_score_format = f"<b>{short_name}</b> - {score_input} - {score_format}"
                        finallist_html.append(f"<div class=\"namebox\">\n<p>{scorecounter}. {html_score_format}</p>\n</div>\n")
                    else:
                        finallist.append(f"{scorecounter}. {classcore[1]} - {score_format}\n")
                        short_name = str(classcore[1])[0:8]
                        html_score_format = f"<b>{short_name}</b> {score_format}"
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
def sendtohtml(finalstr,finaltimes,hasshmoovin,shmoovin_type):
    configp.read(f"{serverspath}\\{file}\\cfg\\server_cfg.ini")
    name = str(configp['SERVER']['NAME'])
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
    if not exists("html"):
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
        shmoovin_html = f"{pre_html}<h1>{str(name)}</h1>\n</div>\n<div class=\"classbox\">\n<h3>{shmoovin_type}</h3>\n</div>\n{finalstr}\n{refresh_script}"
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
def sendtowebhook(finalstr,finaltimes,hasshmoovin,shmoovin_type):
    configp.read(f"{serverspath}\\{file}\\cfg\\server_cfg.ini")
    name = str(configp['SERVER']['NAME'])
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
                            "name": shmoovin_type,
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
                            "name": shmoovin_type,
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
                            "name": shmoovin_type,
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
                            "name": shmoovin_type,
                            "value": finalstr
                        }
                    ]
                }
            ]}
    # checks if leaderboard message was allready created and updates it
    if exists(f"config/messages/{main_loop_counter}.txt"):
        with open(f"config/messages/{main_loop_counter}.txt") as File:
            messageid = str(File.readline())
        print(f"{messageid} read from {main_loop_counter}.txt")
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
        with open(f"config/messages/{main_loop_counter}.txt", 'w') as File:
            File.write(f"{messageid}")
            print(f"{messageid} saved in file {main_loop_counter}.txt")
    time.sleep(1)

# deletes unused discord messages
def deletemessage():
    message_lst= os.listdir("config/messages")
    for index,message in enumerate(message_lst):
        if index > main_loop_counter:
            with open(f"config/messages/{message}") as File:
                message_id = str(File.readline())
            rl = requests.delete(f"{webhookurl}/messages/{message_id}",params={'wait': 'true'})
            if "204" in str(rl):
                print(f"discord message {message_id} is unused and is now deleted")
            else:
                print(f"discord message {message_id} could not be deleted")
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
    main_loop_counter = -1
    for serverspath in serverspathlst:
        filenames= os.listdir(str(serverspath))
        print(f"list of folders to check: {filenames}")
        for file in filenames:
            # checks if folder is actually a server folder
            if folderidentifier in file.lower():
                finalstr = "NA"
                finalstr_html = "NA"
                has_shmoovin = False
                shmoovin_type = "none"
                main_loop_counter = main_loop_counter+1
                server_type = server_type_check()
                classcfg = has_classcfg()
                if server_type == "assettoserver":
                    sorted_files = sorted(glob.glob(f"{serverspath}\\{file}{logPath}*"), key=os.path.getctime)
                    print(f"Log file that is being read is: {str(sorted_files[-1])} for server {file}")
                    with open(str(sorted_files[-1]), encoding='utf-8', errors='ignore' "r") as log_file:
                        log_lines = log_file.readlines()
                    has_score_file_check("laptimes")
                    score_find()
                    has_shmoovin, shmoovin_type = shmoovin_check()
                    if has_shmoovin == True:
                        has_score_file_check("leaderboard")
                        scores = sort_score("leaderboard",classcfg)
                        finalstr = format_scores(scores,classcfg,"discord","leaderboard")
                        finalstr_html = format_scores(scores,classcfg,"html","leaderboard")
                elif server_type == "acserver":
                    findtimevanilla()
                times = sort_score("laptimes",classcfg)
                finaltimes = format_scores(times,classcfg,"discord","laptimes")
                finaltimes_html = format_scores(times,classcfg,"html","laptimes")     
                sendtowebhook(finalstr,finaltimes,has_shmoovin,shmoovin_type)
                sendtohtml(finalstr_html,finaltimes_html,has_shmoovin,shmoovin_type)
        deletemessage()
        delete_html()
    print(f"waiting for {interval} minutes")
    time.sleep(interval*60)
