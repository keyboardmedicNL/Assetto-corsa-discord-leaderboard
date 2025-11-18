import yaml
import logging

default_config = {
    "twitch_api_id":"",
    "twitch_api_secret":"",
    "discord_webhook_url":"",
    "poll_interval":10,
    "allowed_categories":[],
    "message_before_embed":"",
    "use_offline_messages":False,
    "team_name": "",
    "excluded_uids":[],
    "use_skybass": False,
    "names_to_ignore": [{
        "name":"name",
        "replace_with":"nothing"
        }],
    "time_before_retry":60,
    "max_errors_allowed":3
}

# loads config from file
def load_config() -> dict:
    with open("config/config.yaml") as config_file:
        config_yaml = yaml.safe_load(config_file)
        merged_config = config_object({**default_config, **config_yaml})
    if merged_config.twitch_api_id == "YOUR_API_ID" or merged_config.twitch_api_secret == "YOUR_API_SECRET" or merged_config.discord_webhook_url == "YOUR_WEBHOOK_URL":
        raise RuntimeError("you are missing required values in your config. please fill them in and try again")
    else:
        logging.debug("succesfully loaded config")       
        return(merged_config)


class config_object:
    def __init__(self, d=None):
        if d is not None:
            for key, value in d.items():
                setattr(self, key, value)
