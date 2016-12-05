import os
import time
from slackclient import SlackClient
import bot

# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("ayerslab_bot connected and running!")
        ayersbot = bot.brain.Brain(BOT_ID, slack_client)
        while True:
            command, channel = ayersbot.listen(slack_client.rtm_read())
            if command and channel:
                ayersbot.process(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
