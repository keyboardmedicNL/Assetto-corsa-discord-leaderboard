import yaml
import logging

default_config = {
    "interval": 1,
    "servers_pathlst": ["ACSERVERS(0.52)"],
    "folder_identifier": "(server",
    "leaderboard_limit": 10,
    "web_hook_url":"",
    "drift_script":[],
    "overtake_script":[],
    "server_adress":"",
    "server_adress_display":"",
    "only_leaderboards":"false",
    "show_input": "false",
    "log_to_file": "false",
    "use_short_name": "false",
    "banned_words":["penis","vagina","nigger"],
    "log_lookback": "3"
}

# loads config from file
def load_config() -> dict:
    with open("config/config.yaml") as config_file:
        config_yaml = yaml.safe_load(config_file)
        merged_config = config_object({**default_config, **config_yaml})
    logging.debug("succesfully loaded config")       
    return(merged_config)


class config_object:
    def __init__(self, d=None):
        if d is not None:
            for key, value in d.items():
                setattr(self, key, value)

if __name__ == "__main__":
    load_config()