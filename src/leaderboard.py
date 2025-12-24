import housey_logging
housey_logging.configure()

import logging
import time
import json
import requests
import os
import glob
from os.path import exists
import re
import configparser
import math
import datetime
from datetime import timezone
import sys
import yaml
import color_picker
import requests_error_handler
import config_loader

config = config_loader.load_config
configp = configparser.ConfigParser(strict=False)


# variables
logPath = "/logs/"

# checks if shmoovin is present in config
def shmoovin_check(combined_server_path_rel: str) -> tuple[str,str]:
    logging.debug(f"Checking if shmoovin exsists in csp_extra_options.ini for server {combined_server_path_rel}")
    
    has_shmoovin = False
    shmoovin_type = ""
    csp_extra_path = os.path.join(combined_server_path_rel, "cfg", "csp_extra_options.ini")

    if exists(csp_extra_path):
    
        try:
            configp.read(csp_extra_path, encoding='utf-8')
            scripttype = str(configp['SCRIPT_...']['SCRIPT'])
            scripttype = scripttype.replace("'","")

            if scripttype in overtakescript:
                shmoovin_type = "Shmoovin overtake leaderboard"
                has_shmoovin = True
                logging.debug(f"shmoovin was found with the type = overtake")

            elif scripttype in driftscript:
                shmoovin_type = "Shmoovin drift leaderboard"
                has_shmoovin = True
                logging.debug(f"shmoovin was found with the type = drift")
        except:
            logging.debug("unable to find script entry in csp extra options")

    return(has_shmoovin,shmoovin_type)

def get_class_cfg(combined_server_path_rel: str) -> any:
    logging.debug(f"Checking if class_cfg exsists in discordbotcfg.ini for server {combined_server_path_rel}")

    classcfg = {"none": ["none"]}
    config_file_path = os.path.join(combined_server_path_rel,"discordbotcfg.json")

    if exists(config_file_path):
        with open(config_file_path) as config:
            configJson = json.load(config)
        
        try:
            classcfg = configJson["classes"]
        
        except:
            logging.debug(f"discordcfg was found but no classcfg present")

    logging.debug(f"classcfg = {classcfg}")

    return(classcfg)

# checks if server folder contains assettoserver.exe or acserver.exe used to filter results
def server_type_check(combined_server_path_rel: str) -> str:
    logging.debug(f"Checking if AssettoServer.exe or acServer.exe exsists for server {combined_server_path_rel}")
    
    if exists(os.path.join(combined_server_path_rel,"AssettoServer.exe")):
        logging.debug(f"{combined_server_path_rel} is AssettoServer")
        return("AssettoServer")

    elif exists(os.path.join(combined_server_path_rel,"acServer.exe")):
        logging.debug(f"{combined_server_path_rel} is acServer")
        return("acServer")

def has_score_file_check(file_name: str,combined_server_path_rel: str):
    score_file_path_rel = os.path.join(combined_server_path_rel, file_name)
    if not exists(score_file_path_rel):
        with open(score_file_path_rel, 'w') as score_file:
            score_file.write("")
        logging.debug(f"{score_file_path_rel} was not found so it was created")

# opens and loops trough last logfile to find score entries and writes them to the appropriate files
def score_find(selected_log: str, previous_log: str, combined_server_path_rel: str):
    logging.debug(f"Checking log for score entries")

    with open(str(selected_log), encoding='utf-8', errors='ignore' "r") as log_file:
        selected_log_lines = log_file.readlines()

    for index_log_line,log_line in enumerate(selected_log_lines):

        leaderboard_file_name = ""

        if ((shmoovin_match := re.findall(".* \[INF\] CHAT:(.*) \(\d*\): Drift: (\d*.\d*)", log_line)) 
        or (shmoovin_match := re.findall(".* \[INF\] CHAT: (.*) \(\d*\): just scored a (\d*)", log_line))):

            logging.debug(f"found shmoovin score on: {log_line.strip()}")
            leaderboard_file_name = "leaderboard.txt"
            name = str(shmoovin_match[0][0])
            score = str(shmoovin_match[0][1])
            score_find_additional(name, score, leaderboard_file_name, index_log_line, selected_log, previous_log, combined_server_path_rel)
            
        elif lap_match := (re.findall(".* \[INF\] Lap completed by (.*), 0 cuts, laptime (\d*)", log_line)):
            logging.debug(f"found laptime on: {log_line.strip()}")
            leaderboard_file_name = "laptimes.txt"
            name = str(lap_match[0][0])
            score = str(lap_match[0][1])
            score_find_additional(name, score, leaderboard_file_name, index_log_line, selected_log, previous_log, combined_server_path_rel)
            
        elif stage_match := (re.findall(".* \[DBG\] Stage (.*) ended for (.*) \(\d*\), time: (.*)", log_line)):
            logging.debug(f"found sector time on: {log_line.strip()}")
            leaderboard_file_name = str(stage_match[0][0]) + "-sector.txt"
            name = str(stage_match[0][1])
            score = str(stage_match [0][2])
            score_find_additional(name, score, leaderboard_file_name, index_log_line, selected_log, previous_log, combined_server_path_rel)

# finds car used, input method and converts laptimes to complete score finding
def score_find_additional(name: str,score: float, leaderboard_file_name: str,index_log_line: int, selected_log: str, previous_log: str, combined_server_path_rel: str):

    name_allowed = check_name(name)

    if "-sector.txt" in leaderboard_file_name:
        minutes,seconds = score.split(":")
        score = float(float(minutes)*60000)+float(float(seconds)*1000)

    if name_allowed:
        input_method = input_find(index_log_line, name, selected_log, previous_log)
        car = find_car(index_log_line, name, selected_log, previous_log)
        write_score(name, score, car, input_method, leaderboard_file_name, combined_server_path_rel)

# loop to find input method used by whoever got the score
def input_find(index_log_line: int ,name: str, selected_log: str, previous_log: str):
    logging.debug(f"Checking for input method for found score entry")

    with open(str(selected_log), encoding='utf-8', errors='ignore' "r") as log_file:
        selected_log_lines = log_file.readlines()

    input_method = "Unknown"

    for index_input, input_line in enumerate(reversed(selected_log_lines)):

        if index_input > len(selected_log_lines)-index_log_line and index_input < len(selected_log_lines):

            if (input_match := (re.findall(r".* \[INF\] CSP handshake received from.*InputMethod=\"(.*)\" .*", input_line))) and (str(name) in input_line):
                logging.debug(f"found input method on: {input_line.strip()}")
                input_method = input_match[0]

    if input_method == "Unknown":

        try:
            logging.debug(f"could not find input method in current log for {str(name)}, trying in second latest log file {str(previous_log)}")

            with open(str(previous_log), encoding='utf-8', errors='ignore' "r") as second_log_file:
                loglines_second_last = second_log_file.readlines()
            
            for second_input_line in reversed(loglines_second_last):
                if (input_match := (re.findall(r".* \[INF\] CSP handshake received from.*InputMethod=\"(.*)\" .*", second_input_line))) and (str(name) in input_line):
                    logging.debug(f"found input method on: {second_input_line.strip()}")
                    input_method = input_match[0]

        except:
            logging.debug(f"could not find input method for {str(name)}")
            return(input_method)

    logging.debug(f"input_method = {input_method}")
    return(input_method)

# loop to find car driven by whoever got the score
def find_car(index_log_line: int ,name: str, selected_log: str, previous_log: str):
    logging.debug(f"Checking for car for found score entry") 

    car = "unknown"

    with open(str(selected_log), encoding='utf-8', errors='ignore' "r") as log_file:
        selected_log_lines = log_file.readlines()

    for index_car_line,car_line in enumerate(reversed(selected_log_lines)):

        if index_car_line > len(selected_log_lines)-index_log_line and index_car_line < len(selected_log_lines):

            if (car_match := (re.findall(".* \[INF\] .* \(.*\((.*)-.* has connected", car_line))) and (str(name) in car_line):
                logging.debug(f"found car on: {car_line.strip()}")
                car = car_match[0]

    if car == "unknown":

        logging.debug(f"could not find car entry in current log for {str(name)}, trying in second latest log file {str(previous_log)}")

        with open(str(previous_log), encoding='utf-8', errors='ignore' "r") as f:
            loglines_second_last = f.readlines()
        
        for car_line in reversed(loglines_second_last):
            if (car_match := (re.findall(".* \[INF\] .* \(.*\((.*)-.* has connected", car_line))) and (str(name) in car_line):
                logging.debug(f"found car on: {car_line.strip()}")
                car = car_match[0]

    logging.debug(f"car = {car}")
    return(car)

# writes obtained scores to appropriate file
def write_score(name, score, car, input_method, leaderboard_file_name, combined_server_path_rel):

    logging.debug(f"attempting to write found score to {leaderboard_file_name}") 
    
    try:
         with open(f"{os.path.join(combined_server_path_rel,leaderboard_file_name)}", encoding='utf-8', errors='ignore', mode="x"):
            pass
    except Exception as e:
        logging.debug(f"unable to create file {leaderboard_file_name} with exception {e}")

    with open(f"{os.path.join(combined_server_path_rel,leaderboard_file_name)}", encoding='utf-8', errors='ignore', mode="r+") as score_file:
        
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
                    
                    if leaderboard_file_name == "leaderboard.txt" and float(score) > float(old_score):
                        entry = f"{car},{name},{score},{input_method}\n"
                        score_file_lines[score_file_lines.index(score_file_line)] = ""
                        score_file_lines_new.append(entry)
                        
                        logging.debug(f"new record for {name} in {car} with {score} and input method {input_method} for file {leaderboard_file_name}")

                    elif leaderboard_file_name != "leaderboard.txt" and float(score) < float(old_score):
                        entry = f"{car},{name},{score},{input_method}\n"
                        score_file_lines[score_file_lines.index(score_file_line)] = ""
                        score_file_lines_new.append(entry)
                        
                        logging.debug(f"new record for {name} in {car} with {score} and input method {input_method} for file {leaderboard_file_name}")
        
        if was_found == False:
            entry = f"{car},{name},{score},{input_method}\n"
            score_file_lines_new.append(entry)
            
        logging.debug(f"new record for {name} in {car} with {score} and input method {input_method} for file {leaderboard_file_name}")
        
        score_file.seek(0)
        score_file.truncate()
        score_file.write(''.join(score_file_lines + score_file_lines_new))
        
        logging.debug(f"content that was written to {leaderboard_file_name} = \n{''.join(score_file_lines + score_file_lines_new)}")
        
# find laptimes for acServer sessions
def findtimevanilla():
    logging.debug(f"Checking for acServer.exe score entries for server{file}") 
    try:
        latest_file = max(glob.glob(f"{servers_path}/{file}/results/*"), key=os.path.getctime)
        logging.debug(f"results file that is being read is: {latest_file} for server {file}\n")
        
        with open(latest_file, encoding='utf-8', errors='ignore' "r") as f:
            resultsJson = json.load(f)
        
        for result in resultsJson["Result"]:
            name_seperated = result["DriverName"]
            name = name_seperated.replace(',','')
            name_allowed_vanilla = check_name(name)
            
            if name_allowed_vanilla:
                car_seperated = result["CarModel"]
                car = car_seperated.replace(',','')
                score = result["BestLap"]
                
                if name != "" and score != 999999999:
                    logging.debug(f"found laptime for {name} in {car} with time {score}")
                    with open(f"{servers_path}/{file}/laptimes.txt", encoding='utf-8', errors='ignore', mode="r+") as leaderboard:
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
                                            logging.debug(f"new laptime for {name} in {car} with time {score} for server {file}")
                            
                            if wasfound == False:
                                entry = f"{car},{name},{score}\n"
                                leaderboardlinesnew.append(entry)
                                logging.debug(f"new laptime for {name} in {car} with time {score} for server {file}")
                            
                            leaderboardlinescomb = leaderboardlines + leaderboardlinesnew
                            leaderboardwrite = ''.join(leaderboardlinescomb)
                            leaderboard.seek(0)
                            leaderboard.truncate()
                            leaderboard.write(leaderboardwrite)
                            logging.debug(f"content that was written to laptimes.txt = \n{leaderboardwrite}")
    
    except Exception as e:
        logging.debug("An exception occurred attempting to find scores for a ACServer.exe server: ", str(e))

# checks if name is on banned names list
def check_name(name_to_check):
    logging.debug(f"checking {name_to_check} to see if it matches any banned words")
    logging.debug(f"list of banned words to check against:\n{banned_words}")
    allowed = True
    for banned_word in banned_words:
        if banned_word.lower() in name_to_check.lower():
            allowed = False
            logging.debug(f"Found banned word: {banned_word} in the name: {name_to_check}\n")
            
    return(allowed)

# sort scores in list per entry within 1 master list
def sort_score(score_type: str, classcfg: dict, combined_server_path_rel: str) -> list:
    logging.debug(f"attempting to sort scores with type {score_type} for server {combined_server_path_rel}") 
    scores = []
    filtered_times = []

    with open(os.path.join(combined_server_path_rel,score_type), 'r', encoding='utf-8', errors='ignore') as score_file:

        for line in score_file:
            # parses entry from leaderboard.txt into seperate vars for comparison later
            if score_type == "leaderboard.txt":
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

            # parses entry from laptimes or sector times into seperate vars for comparison later
            else:
                try:
                    car, name, score, input_method = line.split(',')
                
                except:
                    car, name, score= line.split(',')
                    input_method = "Unknown"
            
            score = score.strip()

            name_allowed_to_sort = check_name(name)
            
            if name_allowed_to_sort:
                scores.append([car, name, score, input_method])
    
    # sorting for shmoovin scores
    if score_type == "leaderboard.txt":
        scores.sort(key=lambda s: float(s[2]), reverse = True)

    # sorting for laptimes and sector times
    else:
        scores.sort(key=lambda s: float(s[2]), reverse = False)
    
    # sorts scores based on class defined in discordbotcfg
    for class_selected in classcfg:
        filtered = []
        
        for score in scores:
            # old fix to allow for backwards compatibility with old leaderboard.txt wich stored full car name and skin
            try:
                carname_split = score[0].split("-")
            except:
                carname_split = score[0]

            # checks if carname that is recorded exsists in the classcfg list that it is currently itterating over, adds all cars to one big pool if classcfg does not exsist
            if str(carname_split[0]) in str(classcfg[class_selected]) or class_selected == "none":
                allready_in = False
                
                for index_entry,entry in enumerate(filtered):
                    
                    if str(score[1]) in str(entry):
                        allready_in = True
                        
                        # logic for shmoovin scores
                        if score_type == "leaderboard.txt":
                            if float(score[2]) > float(entry[2]):
                                del filtered[index_entry]
                                filtered.append(score)
                        # logic for laptimes and sector times
                        else:
                            if float(score[2]) < float(entry[2]):
                                del filtered[index_entry]
                                filtered.append(score)
                
                if not allready_in:
                    filtered.append(score)

    filtered_times.append(filtered)
    
    logging.debug(f"sorted scores for server {combined_server_path_rel} with type {score_type}")
    logging.debug(f"filtered times = \n{filtered_times}")
    return(filtered_times)

# formats laptimes if class configuration is present to str for use in webhook
def format_scores(scores,classcfg,doc_type,score_type,show_input_discord,use_short_name):

    logging.debug(f"attempting to format scores with type {score_type} for output {doc_type} with classcfg {classcfg} for server {combined_server_path_rel}") 
    
    finallist = []
    classlist = []
    finallist_html = []
    
    for classname in classcfg:
        classlist.append(classname)
    
    for i,score in enumerate(scores):
        scorelength = len(score)
        scorecounter = 0
        
        if scorelength > 0:
            
            if str(classlist[i]) != "none":
                finallist.append(f"***{str(classlist[i])}***:\n")
                finallist_html.append(f"\n<div class=\"classbox\">\n<h3>{str(classlist[i])}</h3>\n</div>\n")
        
        if scorelength >= leaderboardlimit:
            scorelength = leaderboardlimit
        
        for classcore in scores[i]:
            scorecounter = scorecounter + 1
            
            if scorecounter <= scorelength:
                
                if score_type == "leaderboard":
                    score_format = float(classcore[2])
                
                else:
                    laptime = float(classcore[2])
                    minutes= math.floor(laptime/(1000*60)%60)
                    laptime = (laptime-(minutes*(1000*60)))
                    seconds = (laptime/1000)
                    score_format = f"{minutes}:{seconds}"
                
                score_input = classcore[3].strip()
                
                if show_input_discord == "true" and not use_short_name and server_type != "acserver":
                    finallist.append(f"{scorecounter}. {classcore[1]} - {score_input} - {score_format}\n")
                
                elif show_input_discord == "true" and use_short_name and server_type != "acserver":
                    short_name = str(classcore[1])[0:6]
                    finallist.append(f"{scorecounter}.{short_name} {score_input} {score_format}\n")
                
                elif use_short_name:
                    short_name = str(classcore[1])[0:6]
                    finallist.append(f"{scorecounter}.{short_name} {score_format}\n")

                else:
                    finallist.append(f"{scorecounter}. {classcore[1]} - {score_format}\n")
                
                short_name = str(classcore[1])[0:6]
                html_score_format = f"<b>{short_name}</b> {score_format}"
                finallist_html.append(f"<div class=\"namebox\">\n<p>{scorecounter}. {html_score_format}</p>\n</div>\n")
    
    finalstr = "".join(finallist)
    finalstr_html = "".join(finallist_html)
    
    if finalstr == "":
        finalstr = "currently empty"
        finalstr_html = "<div class=\"namebox\">\n<p>currently empty</p>\n</div>\n"
    
    logging.debug(f"formatted scores for discord = \n{finalstr}")
    logging.debug(f"formatted scores for html = \n{finalstr_html}")

    return(finalstr, finalstr_html)

def format_sector(show_input_sector, use_short_name, combined_server_path_rel, classcfg):  
    server_files = os.listdir(combined_server_path_rel)
    combined_sectors = []
    combined_sectors_html = []
    
    for sector_file in server_files:
        if "-sector.txt" in str(sector_file):
            scores = sort_score(sector_file ,classcfg, combined_server_path_rel)
            times, times_html = format_scores(scores, classcfg, "discord", str(sector_file), show_input_sector, use_short_name)
            sector_name = str(sector_file.split("-sector")[0])
            combined_sectors.append(f"\n**{sector_name}**\n")
            combined_sectors.append(times)
            combined_sectors_html.append(f"\n<div class=\"sectorbox\">\n<h3>{sector_name}</h3>\n</div>\n")
            combined_sectors_html.append(times_html)
    
    final_sector_str = "".join(combined_sectors)
    final_sector_str_html = "".join(combined_sectors_html)
    
    return(final_sector_str,final_sector_str_html)

# formats and sends to html files for webserver
def sendtohtml(finalstr,finaltimes,hasshmoovin,shmoovin_type, combined_server_path_rel, server_folder):
    logging.debug(f"attempting to send formatted scores to html for server {combined_server_path_rel}") 
    configp.read(os.path.join(combined_server_path_rel,"server_cfg.ini"))
    name = str(configp['SERVER']['NAME'])
    showtimes = True
    discordbotcfg_file = os.path.join(combined_server_path_rel,"discordbotcfg.json")

    if exists(discordbotcfg_file):
        with open(discordbotcfg_file) as config:
            configJson = json.load(config)
        try:
            showtimes = configJson["showlaptimes"]
            if showtimes.lower() == "false":
                showtimes = False
        except:
            pass
    
    if not exists("html"):
        os.mkdir("html")
    
    pre_html = ("""
    <html>
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
    .sectorbox {
        width: 320px;
        line-height:100%;
        padding: 1px;
        padding-right: 10px;
        margin: 2px;
        background-color: #37474f;
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
    <div class="titlebox">
    """)

    refresh_script = "<script>setTimeout(function(){location.reload()},10000);</script>"
    
    if showtimes:
        times_html = f"{pre_html}<h1>{str(name)}</h1>\n</div>{finaltimes}\n{refresh_script}"
        
        times_html_file = os.path.join("html",f"{server_folder}-times.html")

        if exists (times_html_file):
            with open(times_html_file , encoding='utf-8', errors='ignore', mode="r+") as html_lap_times:
                html_lap_times.seek(0)
                html_lap_times.truncate()
                html_lap_times.write(times_html)
                logging.debug(f"wrote laptimes to {server_folder}-times.html")
                logging.debug(f"html content:\n{times_html}\n")
        else:
            with open(times_html_file , encoding='utf-8', errors='ignore', mode="w") as html_lap_times:
                html_lap_times.write(times_html)
                logging.debug(f"{server_folder}-times.html was created with laptimes")
                logging.debug(f"html content:\n{times_html}\n")
    
    if hasshmoovin:
        shmoovin_html = f"{pre_html}<h1>{str(name)}</h1>\n</div>\n<div class=\"classbox\">\n<h3>{shmoovin_type}</h3>\n</div>\n{finalstr}\n{refresh_script}"
        
        shmoovin_html_file = os.path.join("html",f"{server_folder}-shmoovin.html")
        if exists (shmoovin_html_file):
            with open(shmoovin_html_file, encoding='utf-8', errors='ignore', mode="r+") as html_lap_times:
                html_lap_times.seek(0)
                html_lap_times.truncate()
                html_lap_times.write(shmoovin_html)
                logging.debug(f"wrote shmoovin scores to {server_folder}-shmoovin.html")
                logging.debug(f"html content:\n{shmoovin_html}\n")
        else:
            with open(shmoovin_html_file, encoding='utf-8', errors='ignore', mode="w") as html_lap_times:
                html_lap_times.write(shmoovin_html)

                logging.debug(f"{server_folder}-shmoovin.html was created with shmoovin scores")
                logging.debug(f"html content:\n{shmoovin_html}\n")

# formats message to send to discord, will send a message if it does not exsist yet for the server or update otherwise
def sendtowebhook(finalstr, finaltimes, hasshmoovin, shmoovin_type, combined_server_path_rel):
    logging.debug(f"attempting to send scores to discord for server {combined_server_path_rel}")

    server_cfg_file =  os.path.join(combined_server_path_rel,"cfg","server_cfg.ini")

    configp.read(server_cfg_file)
    name = str(configp['SERVER']['NAME'])

    # checks if laptimes and shmoovin score should be shown
    showtimes = True
    discordbotcfg_file = os.path.join(combined_server_path_rel,"discordbotcfg.json")

    if exists(discordbotcfg_file):
        with open(discordbotcfg_file) as config:
            configJson = json.load(config)
        try:
            showtimes = configJson["showlaptimes"]
            if showtimes.lower() == "false":
                showtimes = False
        except:
            pass
        try:
            hasshmoovin = configJson["showshmoovin"]
            if hasshmoovin.lower() == "false":
                hasshmoovin = False
        except:
            pass
    
    # checks if full server status should be shown and formats data for it
    if onlyleaderboards.lower() == "false":
        configp.read(server_cfg_file)
        httpport = str(configp['SERVER']['HTTP_PORT'])
        serverhttp = f"{serveradress}:{httpport}"
        try:
            rl = requests.get(f"http://{serverhttp}/INFO")
            if verbose:
                logging.debug(f"server info response is: {rl} for server {combined_server_path_rel}")
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
            logging.debug(f"an exception occured for server {combined_server_path_rel} {e}")
    
    # returns correct format based on selected parameters
    if onlyleaderboards.lower() == "false" and hasshmoovin and showtimes :
        logging.debug(f"posting/updating message with full server info, shmoovin and laptimes for server {combined_server_path_rel}")
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
                        },
                        {
                            "name": "",
                            "value": "[***get this bot***](https://github.com/keyboardmedicNL/Assetto-corsa-discord-leaderboard)"
                        }
                    ],
                        "timestamp": datetime.datetime.now(timezone.utc).isoformat()
                }
            ]}

    elif onlyleaderboards.lower() == "false" and not hasshmoovin and showtimes:
        logging.debug(f"posting/updating message with full server info and laptimes for server {combined_server_path_rel}")
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
                            "name": "",
                            "value": "[***get this bot***](https://github.com/keyboardmedicNL/Assetto-corsa-discord-leaderboard)"
                        }
                    ],
                        "timestamp": datetime.datetime.now(timezone.utc).isoformat()
                }
            ]}
    
    elif onlyleaderboards.lower() == "false" and not hasshmoovin and not showtimes:
        logging.debug(f"posting/updating message with full server info for server {combined_server_path_rel}")
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
                            "name": "",
                            "value": "[***get this bot***](https://github.com/keyboardmedicNL/Assetto-corsa-discord-leaderboard)"
                        }
                    ],
                        "timestamp": datetime.datetime.now(timezone.utc).isoformat()
                }
            ]}
    
    elif onlyleaderboards.lower() == "false" and hasshmoovin  and not showtimes:
        logging.debug(f"posting/updating message with full server info and shmoovin for server {combined_server_path_rel}")
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
                        },
                        {
                            "name": "",
                            "value": "[***get this bot***](https://github.com/keyboardmedicNL/Assetto-corsa-discord-leaderboard)"
                        }
                    ],
                        "timestamp": datetime.datetime.now(timezone.utc).isoformat()
                }
            ]}
    
    elif onlyleaderboards.lower() == "true" and hasshmoovin  and showtimes:
        logging.debug(f"posting/updating message with shmoovin and laptimes for server {combined_server_path_rel}")
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
                        },
                        {
                            "name": "",
                            "value": "[***get this bot***](https://github.com/keyboardmedicNL/Assetto-corsa-discord-leaderboard)"
                        }
                    ],
                        "timestamp": datetime.datetime.now(timezone.utc).isoformat()
                }
            ]}
    
    elif onlyleaderboards.lower() == "true" and not hasshmoovin and showtimes:
        logging.debug(f"posting/updating message with laptimes for server {combined_server_path_rel}")
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
                            "name": "",
                            "value": "[***get this bot***](https://github.com/keyboardmedicNL/Assetto-corsa-discord-leaderboard)"
                        }
                    ],
                        "timestamp": datetime.datetime.now(timezone.utc).isoformat()
                }
            ]}
    
    elif onlyleaderboards.lower() == "true" and hasshmoovin  and not showtimes:
        logging.debug(f"posting/updating message with shmoovin for server {combined_server_path_rel}")
        data = {"embeds": [
                {
                    "title": name,
                    "description":"",
                    "fields": [
                        {
                            "name": shmoovin_type,
                            "value": finalstr
                        },
                        {
                            "name": "",
                            "value": "[***get this bot***](https://github.com/keyboardmedicNL/Assetto-corsa-discord-leaderboard)"
                        }
                    ],
                        "timestamp": datetime.datetime.now(timezone.utc).isoformat()
                }
            ]}
    
    # checks if leaderboard message was allready created and updates it
    if exists(f"config/messages/{main_loop_counter}.txt"):
        
        with open(f"config/messages/{main_loop_counter}.txt") as File:
            messageid = str(File.readline())
            logging.debug(f"messageid: {messageid} read from {main_loop_counter}.txt")
            logging.debug(f"json data being send to webhook is: \n{data}\n")
        
        rl = requests.patch(f"{webhookurl}/messages/{messageid}", json=data, params={'wait': 'true'})
        if "200" in str(rl):
            logging.debug(f"discord message {messageid} updated\n")
        
        elif "429" in str(rl):
            for i in range(1,60):
                logging.debug(f"we are being rate limited, waiting for {i} seconds to update discord message with id {messageid}")
                time.sleep(i)
                rl = requests.patch(f"{webhookurl}/messages/{messageid}", json=data, params={'wait': 'true'})
                
                if "200" in str(rl):
                    break
                
                if i == 60 and not "200" in str(rl):
                   logging.debug(f"discord message {messageid} could not be updated with status code {rl}\n") 
        
        else:
            logging.debug(f"discord message {messageid} could not be updated with status code {rl}\n") 
    # creates leaderboard message if not allready created
    
    else:
        logging.debug(f"json data being send to webhook is: \n{data}\n")
        rl = requests.post(webhookurl, json=data, params={'wait': 'true'})
        rljson = rl.json()
        messageid = rljson["id"]
        
        if "200" in str(rl):
            logging.debug(f"discord message {messageid} posted\n")
        
        elif "429" in str(rl):
            for i in range(1,60):
                logging.debug(f"we are being rate limited, waiting for {i} seconds to update discord message with id {messageid}")
                time.sleep(i)
                rl = requests.post(webhookurl, json=data, params={'wait': 'true'})
                
                if "200" in str(rl):
                    break
                
                if i == 60 and not "200" in str(rl):
                   logging.debug(f"discord message {messageid} could not be posted with status code {rl}\n") 
        
        else:
            logging.debug(f"discord message {messageid} could not be posted with status code {rl}\n")
        
        if not exists("config/messages"):
            os.mkdir("config/messages")
        
        with open(f"config/messages/{main_loop_counter}.txt", 'w') as File:
            File.write(f"{messageid}")
            
            if verbose:
                logging.debug(f"{messageid} saved in file {main_loop_counter}.txt")

# deletes unused discord messages
def deletemessage():
    logging.debug(f"checking if messages need to be deleted if unused") 
    message_lst= os.listdir("config/messages")
    
    for index,message in enumerate(message_lst):
        
        if index > main_loop_counter:
            
            with open(f"config/messages/{message}") as File:
                message_id = str(File.readline())
            rl = requests.delete(f"{webhookurl}/messages/{message_id}",params={'wait': 'true'})
            
            if "204" in str(rl):
                logging.debug(f"discord message {message_id} is unused and is now deleted")
            
            elif "429" in str(rl):
                
                for i in range(1,60):
                    logging.debug(f"we are being rate limited, waiting for {i} seconds to update discord message with id {message_id}")
                    time.sleep(i)
                    rl = requests.delete(f"{webhookurl}/messages/{message_id}",params={'wait': 'true'})
                    
                    if "204" in str(rl):
                        break
                    
                    if i == 60 and not "204" in str(rl):
                        logging.debug(f"discord message {message_id} could not be deleted with status code {rl}") 
            
            else:
                logging.debug(f"discord message {message_id} could not be deleted with status code {rl}") 
            os.remove(f"config/messages/{message}")
            
            if verbose:
                logging.debug(f"removing unused message file {message}")

# deletes unused html files
def delete_html(server_folders):
    logging.debug(f"checking if html files need to be deleted if unused")
    html_files = os.listdir("html")
    
    for html_file in html_files:
        html_matches_servername = False
        
        for file in server_folders:
            if str(file) in str(html_file):
                html_matches_servername = True
        
        if not html_matches_servername:
            os.remove(os.path.join("html",html_file))
            logging.debug(f"remove {html_file} because it is no longer used")

##### main code ####

# load config
with open("config/config.json") as config:
    configJson = json.load(config)
    interval = configJson["interval"]
    servers_pathlst = configJson["serverspath"]
    webhookurl = configJson["webhookurl"]
    folder_identifier = configJson["folderindentifier"]
    leaderboardlimit = int(configJson["leaderboardlimit"])
    driftscript = configJson["shmoovindrifturl"]
    overtakescript = configJson["shmoovinovertakeurl"]
    onlyleaderboards = configJson["onlyleaderboards"]
    serveradress = configJson["serveradress"]
    serveradressdisplay = configJson["serveradressdisplay"]
    show_input = configJson["show_input"]
    verbose = configJson["verbose"]
    log_to_file = configJson["log_to_file"]
    use_short_name = configJson["log_to_file"]
    
    if verbose.lower() == "true":
        verbose = True
    
    elif verbose.lower() == "false":
        verbose = False
    
    if use_short_name.lower() == "true":
        use_short_name = True
    
    elif use_short_name.lower() == "false":
        use_short_name = False
    
    shmoovinurl = driftscript + overtakescript
    banned_words = configJson["banned_words"]
    log_lookback = int(configJson["log_lookback"])
    logging.debug("succesfully loaded config\n")

# main loop 
logging.info("Starting assetto discord leaderboards...")
logging.info("Only errors will be displayed here unless otherwise configured.....")

while True:
    # loop trough folders in server folder
    main_loop_counter = -1
       
    for servers_path in servers_pathlst:
        #set default vars for use in instance of loop // replace with defaults in functions later
        has_shmoovin = False
        shmoovin_type = ""

        folders_in_servers_path= os.listdir(str(servers_path))

        logging.debug(f"list of folders to check:{folders_in_servers_path}")
        logging.debug(f"checking {log_lookback} logs back for entries")

        for server_folder in folders_in_servers_path:

            combined_server_path_rel = os.path.join(servers_path,server_folder)
            leaderboardlimit = int(configJson["leaderboardlimit"])
            
            # checks if folder is actually a server folder
            if folder_identifier in server_folder.lower() and os.path.isdir(combined_server_path_rel):
                logging.debug(f"checking server {combined_server_path_rel}")

                has_score_file_check("leaderboard.txt",combined_server_path_rel)
                has_score_file_check("laptimes.txt",combined_server_path_rel)
                server_type = server_type_check(combined_server_path_rel)
                class_cfg = get_class_cfg(combined_server_path_rel)

                finalstr = "NA"
                finalstr_html = "NA"
                main_loop_counter = main_loop_counter+1
                
                final_sector_str = ""
                final_sector_str_html = ""
                
                if server_type == "AssettoServer":

                    # sorts logs in a list by creation date with newest first
                    sorted_log_files = sorted(glob.glob(os.path.join(combined_server_path_rel,"logs","*")), key=os.path.getctime, reverse=True) 
                    
                    for log_index, selected_log in enumerate(sorted_log_files):

                        if log_index < log_lookback or log_index != (len(sorted_log_files)-1) : # checks if current logs are within the set amount of logs to look back at
                            
                            if log_index != (len(sorted_log_files)-1):
                                previous_log = sorted_log_files[int(log_index + 1)]
                            else:
                                previous_log = selected_log

                            logging.debug(f"Log file that is being read is: {str(selected_log)}")

                            score_find(selected_log, previous_log, combined_server_path_rel)
                        
                        else: # breaks for loop if log loopback count has been exceeded
                            break

                    has_shmoovin, shmoovin_type = shmoovin_check(combined_server_path_rel)
                    
                    if has_shmoovin:
                        sorted_scores = sort_score("leaderboard.txt",class_cfg,combined_server_path_rel)
                        finalstr, finalstr_html = format_scores(sorted_scores, class_cfg, "discord","leaderboard", show_input,use_short_name)
                    final_sector_str,final_sector_str_html = format_sector(show_input, use_short_name, combined_server_path_rel, class_cfg)
                
                elif server_type == "acServer":
                    findtimevanilla()
                
                times = sort_score("laptimes.txt", class_cfg, combined_server_path_rel)
                finaltimes, finaltimes_html = format_scores(times, class_cfg, "discord","laptimes", show_input, use_short_name)
                
                if final_sector_str != "" and "currently empty" in finaltimes.lower():
                    finaltimes = ""
                
                if final_sector_str_html != "" and "currently empty" in finaltimes_html.lower():
                    finaltimes_html = ""
                finaltimes_combined = finaltimes + "\n" + final_sector_str
                
                while len(finaltimes_combined) >= 1024 or len(finalstr) >= 1024:                       
                    print(f"\ndata to send to discord is too big, limiting number of entries to {leaderboardlimit} and turning off input recording\n")
                    finaltimes,_ = format_scores(times,class_cfg,"discord","laptimes",False,True)
                    final_sector_str,final_sector_str_html = format_sector(False,True)
                    finaltimes_combined = finaltimes + "\n" + final_sector_str
                    
                    if has_shmoovin == True:
                        finalstr,_ = format_scores(scores,class_cfg,"discord","leaderboard",False,True)
                    
                    if leaderboardlimit < 3:
                        finaltimes_combined = "you have too much text to fit atleast 3 scores in this embed, consider not using classes or limiting the amount of loop timings on the track."
                        finalstr = ""
                    
                    leaderboardlimit = leaderboardlimit - 1
                
                finaltimes_html = finaltimes_html + "\n" + final_sector_str_html 
                sendtowebhook(finalstr, finaltimes_combined, has_shmoovin,shmoovin_type, combined_server_path_rel)
                sendtohtml(finalstr_html,finaltimes_html,has_shmoovin,shmoovin_type, combined_server_path_rel, server_folder)
            
        
        deletemessage()
        delete_html(folders_in_servers_path )
    
    logging.debug(f"\nwaiting for {interval} minutes\n")
    time.sleep(interval*60)
