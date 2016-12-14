import os
import time
from slackclient import SlackClient
import bot

# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

status_channel = [i['id'] for i in slack_client.api_call("groups.list")['groups']
                  if i['name']=='botty_home'][0]

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("ayerslab_bot connected and running!")
        ayersbot = bot.brain.Brain(BOT_ID, slack_client, status_channel)
        while True:
            sound = ayersbot.listen(slack_client.rtm_read(), sound_type='all')
            if sound:
                ayersbot.process(sound['channel'],
                                 sound['message'],
                                 user=sound['user'],
                                 time=sound['time'],
                                 dm=sound['dm'])
            ayersbot.timed_process(time.time()//1)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
