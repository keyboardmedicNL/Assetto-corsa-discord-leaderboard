# important!
since the last release the script has undergone an entire refactor, most importantly for the user the script now uses .yaml files for the configs instead of .json, the script will automaticly convert your old json config to yaml on first run. any needed changes to the config need to happen in the yaml files going forward.

you do need to add the logging.yaml file included in the config folder in the repo manually

# what does it do:
a server sided script that reads logs from assettoserver and acServer for lap times, stage times (found on shutoko), shmoovin score entries and general server information and posts them to a leaderboard posted via discord webhooks aswell as html files in a html folder in the root of the script to use as live overlays in obs.

it makes as many messages as there are servers and will delete them if the server no longer exsists.

it loops trough a parent folder housing all servers and uses a configurable identifier to identify server folders. if it sees a server folder it looks in that folder for a logs folder or a results folder where it will then loop trough the last log file to find score entries. it will NOT work with different folder structures (example below). it saves the scores and laptimes to a leaderboard txt and a laptimes txt in the root of the server wich can be added manually to remove or reset scores. AssettoServer Sectors/stages are saved to a txt file called (sectorname)-sector.txt

If there is no shmoovin script present in the csp config in the server folders cfg folder it will not trigger and leave the folder alone.
It gets the server name from the server config.

laptimes and full server info can be set on or off in the configs as described below.

# screenshots

![alt text](screenshot6.png)

![alt text](screenshot7.png)

# how to use:
1. install python on your system from the python website https://www.python.org/downloads/ make sure to select add python to path
2. install the requests module trough pip with the following command in a terminal
```
python -m pip install requests
```
3. in the config folder copy the provided example_config.yaml and rename it to config.yaml
4. configure the config.json as needed:
```
# required parameters:
web_hook_url: Your_discord_webhook_url
server_adress: 127.0.0.1 # ip to your server
server_adress_display: 127.0.0.0 # ip to display in the leaderboards to allow users to connect
folder_identifier: your_server_folder_identifier # a unique identifier in folder names that all your server folders have in common (used to filter out offline or motballed servers)
servers_pathlst: # a list of folders to check for servers
- path_to_your_assetto_servers_parent_folder

# optional parameters
#interval: 10 # time in minutes to check for new scores or entries
#leaderboard_limit: 10 # amount of entries you want to display in your leaderboard
#log_lookback: 10 # how many log files to look back for new scores or laptimes
#banned_words: # a list of words to not display in the leaderboards
#- penis
#- vagina
#- retard
#drift_script:
#- your_shmoovin_drift_script_url
#overtake_script:
#- your_shmoovin_overtake_script_url
#show_input: false # wether or not to display input method in leaderboards (requires assettoserver plugin)
#use_short_name: false # wether or not to shorten usernames in the leaderboards
#only_leaderboards: false # wether or not to display the leaderboard with server info or just the leadeboards
#time_before_retry: 60 # amount of time in seconds between retrying an http request if it errors out
#max_errors_allowed: 3 # how many times an http request can error out before the script crashes

```
5. save the file and run the script:   
on windows: with the provided start.bat file OR trough a terminal with "python leaderboard.py".   
on linux: in the terminal with "python src/leaderboard.py".   

* alternativly you can build your own docker image with the dockerfile provided or use mine with the following command
```
docker run -dit --name shmoovin-discord-leaderboard -v /path/to/assetto/servers:/usr/src/app/servers -v /path/to/config:/usr/src/app/config keyboardmedic/shmoovin-discord-leaderboard:latest
```
* example folder structure with the identifier set as "(server" :  
-> Assetto servers  
--> (server 1) this is a server  
---> logs  
--> (server 2) this is another server  
---> logs
-> acServers   
--> (server 3) this is yet another server  
---> results  

# extra configuration options

* optionally to ignore laptimes, shmoovin scores or sort by class for a certain server you can create a file in the server root with the name "discordbotcfg.yaml"
in the file add the following lines, an example can be found in the config folder, to define wich car goes in what class make a class entry like above and add the classnames for the car in there within "" seperated by , :
```
show_sectors: true # Wether or not to show sector entries or NA in the leaderboard
show_shmoovin: true # Wether or not to show shmoovin entries or NA in the leaderboard
show_times: true # Wether or not to show laptime entries or NA in the leaderboard
class_cfg: # a dict of class names with its containing car file names to sort your leaderboard by car classes 
  '2004':
  - ks_ferrari_f2004
  '2010':
  - lotus_exos_125_s1
  '2017':
  - ks_ferrari_sf70h
  60s:
  - ks_ferrari_312_67
  - lotus_49
  70s:
  - ferrari_312t
  - ks_lotus_72d
  80s:
  - lotus_98t
```

* should not be needed but just in case: to remove or resend a leaderboard delete all txt files in the folder ./config/messages and manually delete the leaderboard message on discord .

* to remove an entry from the leaderboards delete the entry in the corresponding file (leaderboard.txt or laptimes.txt in the server root) and delete the corresponding log line in the logs

# disclaimer
scripts are written by an amateur, use at your own risk...
