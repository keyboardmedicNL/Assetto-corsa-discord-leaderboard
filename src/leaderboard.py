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
import requests_error_handler
import config_loader

configp = configparser.ConfigParser(strict=False)

color_list = [
    0xA4C400,
    0x60A917,
    0x008A00,
    0x00ABA9,
    0x1BA1E2,
    0x0050EF,
    0x6A00FF,
    0xAA00FF,
    0xF472D0,
    0xD80073,
    0xA20025,
    0xE51400,
    0xFA6800,
    0xF0A30A,
    0xE3C800
    ]

def sanitize_filename(name: str, replacement: str="_") -> str:
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', replacement, name)
    sanitized = sanitized.strip(" .")

    return sanitized if sanitized else "unnamed"

def shmoovin_check(combined_server_path_rel: str) -> tuple[str, str]:
    logging.debug(f"Checking if shmoovin exsists in csp_extra_options.ini for server {combined_server_path_rel}")
    
    has_shmoovin = False
    shmoovin_type = ""
    csp_extra_path = os.path.join(combined_server_path_rel, "cfg", "csp_extra_options.ini")

    if exists(csp_extra_path):
    
        try:
            configp.read(csp_extra_path, encoding='utf-8')
            scripttype = str(configp['SCRIPT_...']['SCRIPT'])
            scripttype = scripttype.replace("'","")

            if scripttype in config.overtake_script:
                shmoovin_type = "overtake"
                has_shmoovin = True
                logging.debug(f"shmoovin was found with the type = overtake")

            elif scripttype in config.drift_script:
                shmoovin_type = "drift"
                has_shmoovin = True
                logging.debug(f"shmoovin was found with the type = drift")
        except:
            logging.debug("unable to find script entry in csp extra options")

    return(has_shmoovin,shmoovin_type)

def get_server_cfg(combined_server_path_rel: str) -> tuple[dict, bool, bool, bool]:
    logging.debug(f"Checking if class_cfg exsists in discordbotcfg.ini for server {combined_server_path_rel}")

    if exists(os.path.join(combined_server_path_rel,"discordbotcfg.yaml")):
        server_config = config_loader.load_server_config(combined_server_path_rel)

        logging.debug(f"class_cfg = {server_config.class_cfg}, show_times = {str(server_config.show_times)}, show_shmoovin = {str(server_config.show_shmoovin)}, show_sectors = {str(server_config.show_sectors)}")
        return(server_config.class_cfg, server_config.show_times, server_config.show_shmoovin, server_config.show_sectors)

    else:
        class_cfg = {"none": ["none"]}
        show_times = True
        show_shmoovin = True
        show_sectors = True
        config_file_path = os.path.join(combined_server_path_rel,"discordbotcfg.json")

        if exists(config_file_path):
            with open(config_file_path) as config:
                configJson = json.load(config)
            
            try:
                class_cfg = configJson["classes"]
            except:
                pass

            try:
                show_times = configJson["showlaptimes"]
                if show_times.lower() == "false":
                    show_times = False
                else:
                    show_times = True
            except:
                pass

            try:
                show_shmoovin = configJson["showshmoovin"]
                if show_shmoovin.lower() == "false":
                    show_shmoovin = False
                else:
                    show_shmoovin = True
            except:
                pass

            try:
                show_sectors = configJson["showsectors"]
                if show_sectors.lower() == "false":
                    show_sectors = False
                else:
                    show_sectors = True
            except:
                pass

            data_for_yaml = {"class_cfg":class_cfg,"show_times":show_times,"show_shmoovin":show_shmoovin,"show_sectors":show_sectors}
            create_yaml(data_for_yaml,os.path.join(combined_server_path_rel,"discordbotcfg.yaml"))

            logging.debug(f"class_cfg = {class_cfg}, show_times = {str(show_times)}, show_shmoovin = {str(show_shmoovin)}, show_sectors = {str(show_sectors)}")    
    return(class_cfg, show_times, show_shmoovin, show_sectors)

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
        leaderboard_file_name = sanitize_filename(leaderboard_file_name)
        minutes,seconds = score.split(":")
        score = float(float(minutes)*60000)+float(float(seconds)*1000)

    if name_allowed:
        input_method = input_find(index_log_line, name, selected_log, previous_log)
        car = find_car(index_log_line, name, selected_log, previous_log)
        write_score(name, score, car, input_method, leaderboard_file_name, combined_server_path_rel)

def input_find(index_log_line: int ,name: str, selected_log: str, previous_log: str) -> str:
    logging.debug(f"Checking for input method for found score entry")

    with open(str(selected_log), encoding='utf-8', errors='ignore' "r") as log_file:
        selected_log_lines = log_file.readlines()

    input_method = "Unknown"

    for index_input, input_line in enumerate(reversed(selected_log_lines)):

        if index_input > len(selected_log_lines)-index_log_line and index_input < len(selected_log_lines):

            if (input_match := (re.findall(r".* \[INF\] CSP handshake received from.*InputMethod=\"(.*)\" .*", input_line))) and (str(name) in input_line):
                logging.debug(f"found input method on: {input_line.strip()}")
                input_method = input_match[0]
                break

    if input_method == "Unknown":

        try:
            logging.debug(f"could not find input method in current log for {str(name)}, trying in second latest log file {str(previous_log)}")

            with open(str(previous_log), encoding='utf-8', errors='ignore' "r") as second_log_file:
                loglines_second_last = second_log_file.readlines()
            
            for second_input_line in reversed(loglines_second_last):
                if (input_match := (re.findall(r".* \[INF\] CSP handshake received from.*InputMethod=\"(.*)\" .*", second_input_line))) and (str(name) in input_line):
                    logging.debug(f"found input method on: {second_input_line.strip()}")
                    input_method = input_match[0]
                    break

        except:
            logging.debug(f"could not find input method for {str(name)}")
            return(input_method)

    logging.debug(f"input_method = {input_method}")
    return(input_method)

def find_car(index_log_line: int ,name: str, selected_log: str, previous_log: str) -> str:
    logging.debug(f"Checking for car for found score entry") 

    car = "unknown"

    with open(str(selected_log), encoding='utf-8', errors='ignore' "r") as log_file:
        selected_log_lines = log_file.readlines()

    for index_car_line,car_line in enumerate(reversed(selected_log_lines)):

        if index_car_line > len(selected_log_lines)-index_log_line and index_car_line < len(selected_log_lines):

            if (car_match := (re.findall(".* \[INF\] .* \(.*\((.*)-.* has connected", car_line))) and (str(name) in car_line):
                logging.debug(f"found car on: {car_line.strip()}")
                car = car_match[0]
                break

    if car == "unknown":

        logging.debug(f"could not find car entry in current log for {str(name)}, trying in second latest log file {str(previous_log)}")

        with open(str(previous_log), encoding='utf-8', errors='ignore' "r") as f:
            loglines_second_last = f.readlines()
        
        for car_line in reversed(loglines_second_last):
            if (car_match := (re.findall(".* \[INF\] .* \(.*\((.*)-.* has connected", car_line))) and (str(name) in car_line):
                logging.debug(f"found car on: {car_line.strip()}")
                car = car_match[0]
                break

    logging.debug(f"car = {car}")
    return(car)

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
        
        #logging.debug(f"content that was written to {leaderboard_file_name} = \n{''.join(score_file_lines + score_file_lines_new)}")
        
# find laptimes for acServer sessions
def find_time_vanilla(combined_server_path_rel):
    logging.debug(f"Checking for acServer.exe score entries for server{combined_server_path_rel}") 
    try:
        latest_file = max(glob.glob(os.path.join(combined_server_path_rel,"results"),"*"), key=os.path.getctime)
        logging.debug(f"results file that is being read is: {latest_file}")
        
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
                                            logging.debug(f"new laptime for {name} in {car} with time {score}")
                            
                            if wasfound == False:
                                entry = f"{car},{name},{score}\n"
                                leaderboardlinesnew.append(entry)
                                logging.debug(f"new laptime for {name} in {car} with time {score}")
                            
                            leaderboardlinescomb = leaderboardlines + leaderboardlinesnew
                            leaderboardwrite = ''.join(leaderboardlinescomb)
                            leaderboard.seek(0)
                            leaderboard.truncate()
                            leaderboard.write(leaderboardwrite)
                            logging.debug(f"content that was written to laptimes.txt = \n{leaderboardwrite}")
    
    except Exception as e:
        logging.debug("An exception occurred attempting to find scores for a ACServer.exe server: ", str(e))

# checks if name is on banned names list
def check_name(name_to_check: str) -> bool:
    logging.debug(f"checking {name_to_check} to see if it matches any banned words")
    logging.debug(f"list of banned words to check against:\n{config.banned_words}")
    allowed = True
    for banned_word in config.banned_words:
        if banned_word.lower() in name_to_check.lower():
            allowed = False
            logging.debug(f"Found banned word: {banned_word} in the name: {name_to_check}\n")
            
    return(allowed)

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

def format_scores(scores, classcfg, score_type: str, show_input_discord: bool, use_short_name: bool, server_type: str = "assettoserver") -> tuple[str, str]:

    logging.debug(f"attempting to format scores with type {score_type} with classcfg {classcfg}") 
    
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
        
        if scorelength >= config.leaderboard_limit:
            scorelength = config.leaderboard_limit
        
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
                
                if show_input_discord and not use_short_name and server_type != "acserver":
                    finallist.append(f"{scorecounter}. {classcore[1]} - {score_input} - {score_format}\n")
                
                elif show_input_discord and use_short_name and server_type != "acserver":
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
        finalstr = "NA"
        finalstr_html = "<div class=\"namebox\">\n<p>NA</p>\n</div>\n"
    
    logging.debug(f"formatted scores for discord = \n{finalstr}")
    logging.debug(f"formatted scores for html = \n{finalstr_html}")

    return(finalstr, finalstr_html)

def format_sector(show_input_sector: bool, use_short_name: bool, combined_server_path_rel: str, classcfg) -> tuple[str, str]:
    server_files = os.listdir(combined_server_path_rel)
    combined_sectors = []
    combined_sectors_html = []
    
    for sector_file in server_files:
        if "-sector.txt" in str(sector_file):
            scores = sort_score(sector_file ,classcfg, combined_server_path_rel)
            times, times_html = format_scores(scores, classcfg, str(sector_file), show_input_sector, use_short_name)
            sector_name = str(sector_file.split("-sector")[0])
            combined_sectors.append(f"\n**{sector_name}**\n")
            combined_sectors.append(times)
            combined_sectors_html.append(f"\n<div class=\"sectorbox\">\n<h3>{sector_name}</h3>\n</div>\n")
            combined_sectors_html.append(times_html)

    if combined_sectors:
        final_sector_str = "".join(combined_sectors)
        final_sector_str_html = "".join(combined_sectors_html)
    else:
        final_sector_str = "NA"
        final_sector_str_html = "NA"

    return(final_sector_str,final_sector_str_html)

def send_to_html(shmoovin_score: str, lap_times: str, sector_times: str, shmoovin_type: str, combined_server_path_rel: str, server_folder: str):
    logging.debug(f"attempting to send formatted scores to html for server {combined_server_path_rel}") 
    configp.read(os.path.join(combined_server_path_rel,"server_cfg.ini"))
    name = str(configp['SERVER']['NAME'])

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
    
    times_html = f"{pre_html}<h1>{str(name)}</h1>\n</div>{lap_times}\n{refresh_script}"
    times_html_file = os.path.join("html",f"{server_folder}-times.html")
    edit_html(times_html_file, times_html)

    shmoovin_html = f"{pre_html}<h1>{str(name)}</h1>\n</div>\n<div class=\"classbox\">\n<h3>{shmoovin_type}</h3>\n</div>\n{shmoovin_score}\n{refresh_script}"
    shmoovin_html_file = os.path.join("html",f"{server_folder}-shmoovin.html")
    edit_html(shmoovin_html_file, shmoovin_html)

    sector_html = f"{pre_html}<h1>{str(name)}</h1>\n</div>{sector_times}\n{refresh_script}"
    sector_html_file = os.path.join("html",f"{server_folder}-sectors.html")
    edit_html(sector_html_file, sector_html)

def edit_html(file: str, html: str):
    if exists (file):
        with open(file, encoding='utf-8', errors='ignore', mode="r+") as html_file:
            html_file.seek(0)
            html_file.truncate()
            html_file.write(html)
            logging.debug(f"wrote html to {file} with content\n{html}")
    else:
        with open(file, encoding='utf-8', errors='ignore', mode="w") as html_file:
            html_file.write(html)
            logging.debug(f"created html in {file}, with content\n{html}")

def send_to_web_hook(combined_server_path_rel: str, main_loop_counter: int, shmoovin_score : str, lap_times: str, sector_times: str, show_times: bool, show_shmoovin: bool, show_sectors: bool, shmoovin_type: str):
    logging.debug(f"attempting to send scores to discord for server {combined_server_path_rel}")

    server_cfg_file =  os.path.join(combined_server_path_rel,"cfg","server_cfg.ini")

    configp.read(server_cfg_file)
    name = str(configp['SERVER']['NAME'])

    # checks if laptimes and shmoovin score should be shown
    if not show_times:
        lap_times = "NA"
    if not show_shmoovin:
        shmoovin_score = "NA"
    if not show_sectors:
        sector_times = "NA"
    
    # checks if full server status should be shown and formats data for it
    if not config.only_leaderboards:
        configp.read(server_cfg_file)
        http_port = str(configp['SERVER']['HTTP_PORT'])
        serverhttp = f"{config.server_adress}:{http_port}"
        try:
            rl = requests.get(f"http://{serverhttp}/INFO")
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
    
    if main_loop_counter >= len(color_list):
        color = color_list[main_loop_counter-len(color_list)]
    else:
        color = color_list[main_loop_counter]

    # returns correct format based on selected parameters
    if not config.only_leaderboards:
        logging.debug(f"posting/updating message with full server info, shmoovin and laptimes for server {combined_server_path_rel}")
        data = {"embeds": [
                {
                    "title": name,
                    "description":"",
                    "color": color,
                    "fields": [
                        {
                            "name": f":race_car:",
                            "value": f"[***Click here to connect***](https://acstuff.ru/s/q:race/online/join?ip={config.server_adress_display}&httpport={http_port})",
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
                            "value": lap_times,
                        },
                        {
                            "name": "sector times",
                            "value": sector_times,
                        },
                        {
                            "name": f"Shmoovin {shmoovin_type} score",
                            "value": shmoovin_score,
                        },
                        {
                            "name": "",
                            "value": "[***get this bot***](https://github.com/keyboardmedicNL/Assetto-corsa-discord-leaderboard)"
                        }
                    ],
                        "timestamp": datetime.datetime.now(timezone.utc).isoformat()
                }
            ]}
    else:
        logging.debug(f"posting/updating message with shmoovin and laptimes for server {combined_server_path_rel}")
        data = {"embeds": [
                {
                    "title": name,
                    "description":"",
                    "color": color,
                    "fields": [
                        {
                            "name": "Laptimes",
                            "value": lap_times,
                        },
                        {
                            "name": "sector times",
                            "value": sector_times,
                        },
                        {
                            "name": f"Shmoovin {shmoovin_type} score",
                            "value": shmoovin_score,
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

        request_url_combined = f"{config.web_hook_url}/messages/{messageid}"
        requests_error_handler.handle_request_error(request_type="patch", request_url=request_url_combined, request_json=data, request_params={'wait': 'true'})

    # creates leaderboard message if not allready created
    
    else:
        logging.debug(f"json data being send to webhook is: \n{data}\n")

        request_json = requests_error_handler.handle_request_error(request_type="post", request_url=config.web_hook_url, request_json=data, request_params={'wait': 'true'})
        jsonifyd_request = request_json.json()
        messageid = jsonifyd_request["id"]

        if not exists("config/messages"):
            os.mkdir("config/messages")
        
        with open(f"config/messages/{main_loop_counter}.txt", 'w') as File:
            File.write(f"{messageid}")
            
        logging.debug(f"{messageid} saved in file {main_loop_counter}.txt")

def delete_message(main_loop_counter: int):
    logging.debug(f"checking if messages need to be deleted if unused") 
    message_lst= os.listdir("config/messages")
    
    for index,message in enumerate(message_lst):
        
        if index > main_loop_counter:
            
            with open(f"config/messages/{message}") as File:
                message_id = str(File.readline())

            rl = requests.delete(f"{config.web_hook_url}/messages/{message_id}",params={'wait': 'true'})
            time.sleep(1)

            request_url_combined = f"{config.web_hook_url}/messages/{messageid}"
            request_json = requests_error_handler.handle_request_error(request_type="delete", request_url=request_url_combined, request_params={'wait': 'true'}, status_type_ok=[204])

            os.remove(f"config/messages/{message}")
            
            logging.debug(f"removing unused message file {message}")

def delete_html(server_folders: list):
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

def create_yaml(data_for_yaml: str, path_to_file: str):
    yaml_string = yaml.dump(data_for_yaml)

    with open(path_to_file,"x") as yaml_file:
        yaml_file.write(yaml_string)

    logging.debug(f"converted old config to yaml with data =\n{str(data_for_yaml)}")

def main():
    logging.info("Starting assetto discord leaderboards...")
    logging.info("Only errors will be displayed here unless otherwise configured.....")
    initial_loop_finished = False

    while True:
        # loop trough folders in server folder
        main_loop_counter = -1
    
        for servers_path in config.servers_pathlst:
            #set default vars for use in instance of loop // replace with defaults in functions later
            has_shmoovin = False

            folders_in_servers_path= os.listdir(str(servers_path))

            logging.debug(f"list of folders to check:{folders_in_servers_path}")
            logging.debug(f"checking {config.log_lookback} logs back for entries")

            for server_folder in folders_in_servers_path:
                
                combined_server_path_rel = os.path.join(servers_path,server_folder)
                
                # checks if folder is actually a server folder
                if config.folder_identifier in server_folder.lower() and os.path.isdir(combined_server_path_rel):
                    logging.debug(f"checking server {combined_server_path_rel}")

                    has_score_file_check("leaderboard.txt",combined_server_path_rel)
                    has_score_file_check("laptimes.txt",combined_server_path_rel)
                    server_type = server_type_check(combined_server_path_rel)
                    class_cfg, show_times, show_shmoovin, show_sectors = get_server_cfg(combined_server_path_rel)

                    laptimes_discord = "NA"
                    laptimes_html = "NA"
                    main_loop_counter = main_loop_counter+1
                    
                    sector_times_discord = "NA"
                    sector_times_html = "NA"

                    shmoovin_score_discord = "NA"
                    shmoovin_score_html = "NA"
                    shmoovin_type = ""

                    if server_type == "AssettoServer":

                        # sorts logs in a list by creation date with newest first
                        sorted_log_files = sorted(glob.glob(os.path.join(combined_server_path_rel,"logs","*")), key=os.path.getctime, reverse=True) 
                        
                        for log_index, selected_log in enumerate(sorted_log_files):

                            if (log_index < config.log_lookback and log_index != (len(sorted_log_files)-1)) and not initial_loop_finished : # checks if current logs are within the set amount of logs to look back at
                                
                                if log_index != (len(sorted_log_files)-1):
                                    previous_log = sorted_log_files[int(log_index + 1)]
                                else:
                                    previous_log = selected_log

                                logging.debug(f"Log file that is being read is: {str(selected_log)}")

                                score_find(selected_log, previous_log, combined_server_path_rel)
                            
                            else: # breaks for loop if log loopback count has been exceeded or when initial loop is complete

                                try:
                                    previous_log = sorted_log_files[int(log_index + 1)]
                                except:
                                    previous_log = selected_log
                                
                                logging.debug(f"Log file that is being read is: {str(selected_log)}")

                                score_find(selected_log, previous_log, combined_server_path_rel)

                                break


                        has_shmoovin, shmoovin_type = shmoovin_check(combined_server_path_rel)
                        
                        if has_shmoovin:
                            sorted_scores = sort_score("leaderboard.txt",class_cfg,combined_server_path_rel)
                            shmoovin_score_discord, shmoovin_score_html = format_scores(sorted_scores, class_cfg, "leaderboard", config.show_input, config.use_short_name)
                        sector_times_discord, sector_times_html = format_sector(config.show_input, config.use_short_name, combined_server_path_rel, class_cfg)
                    
                    elif server_type == "acServer":
                        find_time_vanilla(combined_server_path_rel)
                    
                    laptimes_raw = sort_score("laptimes.txt", class_cfg, combined_server_path_rel)
                    laptimes_discord, laptimes_html = format_scores(laptimes_raw, class_cfg, "laptimes", config.show_input, config.use_short_name, server_type)
                    
                    send_to_web_hook(combined_server_path_rel, main_loop_counter, shmoovin_score_discord, laptimes_discord,sector_times_discord, show_times, show_shmoovin, show_sectors, shmoovin_type)
                    send_to_html(shmoovin_score_html, laptimes_html, sector_times_html, shmoovin_type, combined_server_path_rel, server_folder)
                
            
            delete_message(main_loop_counter)
            delete_html(folders_in_servers_path)

        initial_loop_finished = True
        logging.debug(f"waiting for {config.interval} minutes")
        time.sleep(config.interval*60)

if __name__ == "__main__":

    # loads config
    if exists(os.path.join("config","config.yaml")):
        config = config_loader.load_config()
        logging.debug("succesfully loaded yaml config")
        
    else:
        # load legacy config
        with open("config/config.json") as config:
            configJson = json.load(config)
            class config:
                interval = configJson["interval"]
                servers_pathlst = configJson["serverspath"]
                web_hook_url = configJson["webhookurl"]
                folder_identifier = configJson["folderindentifier"]
                leaderboard_limit = int(configJson["leaderboardlimit"])
                drift_script = configJson["shmoovindrifturl"]
                overtake_script = configJson["shmoovinovertakeurl"]
                banned_words = configJson["banned_words"]
                log_lookback = int(configJson["log_lookback"])
                server_adress = configJson["serveradress"]
                server_adress_display = configJson["serveradressdisplay"]

                only_leaderboards = configJson["onlyleaderboards"]
                if only_leaderboards.lower() == "true":
                    only_leaderboards = True
                
                elif only_leaderboards.lower() == "false":
                    only_leaderboards = False

                show_input = configJson["show_input"]
                if show_input.lower() == "true":
                    show_input = True
                
                elif show_input.lower() == "false":
                    show_input = False

                use_short_name = configJson["use_short_name"]
                if use_short_name.lower() == "true":
                    use_short_name = True
                
                elif use_short_name.lower() == "false":
                    use_short_name = False

        # builds dict to export to yaml
        config_for_yaml = {
            "interval":config.interval,
            "servers_pathlst":config.servers_pathlst,
            "web_hook_url":config.web_hook_url,
            "folder_identifier":config.folder_identifier,
            "leaderboard_limit":config.leaderboard_limit,
            "drift_script":config.drift_script,
            "overtake_script":config.overtake_script,
            "banned_words":config.banned_words,
            "log_lookback":config.log_lookback,
            "server_adress":config.server_adress,
            "server_adress_display":config.server_adress_display,
            "only_leaderboards":config.only_leaderboards,
            "show_input":config.show_input,
            "use_short_name":config.use_short_name,
            "time_before_retry":60,
            "max_errors_allowed":3
            }
            
        create_yaml(config_for_yaml,"config/config.yaml")   
        
        logging.debug("succesfully loaded legacy config")

    sys.excepthook = housey_logging.log_exception

    main()
