# what does it do:
a server sided script that reads logs from assettoserver and acServer for lap times, shmoovin score entries and general server information and posts them to a leaderboard posted via discord webhooks.

it makes as many messages as there are servers and will delete them if the server no longer exsists.

it loops trough a parent folder housing all servers and uses a configurable identifier to identify server folders. if it sees a server folder it looks in that folder for a logs folder or a results folder where it will then loop trough the last log file to find score entries. it will NOT work with different folder structures (example below). it saves the scores and laptimes to a leaderboard txt and a laptimes txt in the root of the server wich can be added manually to remove or reset scores.

If there is no shmoovin script present in the csp config in the server folders cfg folder it will not trigger and leave the folder alone.
It gets the server name from the server config.

laptimes and full server info can be set on or off in the configs as described below.

# screenshots

![alt text](screenshot3.png)

![alt text](screenshot4.png)

![alt text](screenshot5.png)

# how to use:
1. install python on your system from the python website https://www.python.org/downloads/ make sure to select add python to path
2. install the requests module trough pip with the following command in a terminal
```
python -m pip install requests
```
3. in the config folder copy the provided example_config.json and rename it to config.json
4. configure the config.json as needed:
```
{
    "interval": time in minutes on how often the script should update the leaderboards,
    "serverspath": ["path/to/server_parent_folder1", "path/to/server_parent_folder2"],
    "folderindentifier": "identifier to recognize server folder",
    "leaderboardlimit": how much entries should be displayed on the leaderboard,
    "webhookurl":"url to your discord webhook",
    "shmoovindrifturl":["url to drift script"],
    "shmoovinovertakeurl":["url to overtake script"],
    "serveradress":"ip adress of server",
    "serveradressdisplay":"ip adress used in bot messages and link (incase serveradress is localhost)",
    "onlyleaderboards":"wether or not to show the full server info or leadeboards only, set to "true" or "false" "
}
```
5. save the file and run the script:   
on windows: with the provided start.bat file OR trough a terminal with "python leaderboard.py".   
on linux: in the terminal with "python leaderboard.py".   

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

* optionally to ignore laptimes or sort by class for a certain server you can create a file in the server root with the name "discordbotcfg.json"
in the file add the following lines, an example can be found in the config folder, to define wich car goes in what class make a class entry like above and add the classnames for the car in there within "" seperated by , :
```
{
"showlaptimes":"True",
"classes":{
    "2017":["ks_ferrari_sf70h"],
    "2010":["lotus_exos_125_s1"],
    "2004":["ks_ferrari_f2004"],
    "80s":["lotus_98t"],
    "70s":["ferrari_312t","ks_lotus_72d"],
    "60s":["ks_ferrari_312_67","lotus_49"]
    }
}
```

* should not be needed but just in case: to remove or resend a leaderboard delete all txt files in the folder ./config/messages and manually delete the leaderboard message on discord .

* to remove an entry from the leaderboards delete the entry in the corresponding file (leaderboard.txt or laptimes.txt in the server root) and delete the corresponding log line in the logs

# disclaimer
scripts are written by an amateur, use at your own risk...
