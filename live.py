import os
import sqlite3
import time
from slackclient import SlackClient
import action
import utils

# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

status_channel = [i['id'] for i in slack_client.api_call("groups.list")['groups']
                  if i['name'] == 'botty_home'][0]

# read in database
db_conn = sqlite3.connect('ayerslab.db')
cursor = db_conn.cursor()
# initiate database
if u'members' not in (j for i in cursor.fetchall() for j in i):
    cursor.execute('CREATE TABLE members (id INTEGER PRIMARY KEY, name TEXT, userid TEXT NOT NULL, '
                   'slack_id TEXT, email TEXT, role TEXT, dates_away TEXT, permission TEXT)')
    db_conn.commit()
if u'group_meetings' not in (j for i in cursor.fetchall() for j in i):
    cursor.execute('CREATE TABLE group_meetings (id INTEGER PRIMARY KEY, date TEXT NOT NULL, '
                   'presenter INTEGER, chair INTEGER, title TEXT)')
    db_conn.commit()

if __name__ == "__main__":
    if slack_client.rtm_connect():
        print("ayerslab_bot connected and running!")
        host = "<@{0}>".format(BOT_ID)
        while True:
            raw_info = slack_client.rtm_read()

            # parse messages (if info is a message that has been directly messaged to bot)
            msgs = [{'user': msg['user'],
                     'channel': msg['channel'],
                     'time': msg['ts'],
                     'message': msg['text'].split(host)[1].strip()}
                    for msg in raw_info
                    if msg['type'].startswith('message') and host in msg['text']]

            # process messages
            for msg in msgs:
                args = msg['message'].split()

                # configure speak
                def speak(message):
                    """Respond to the message."""
                    action.speak(slack_client, msg['channel'], message, msg['user'])

                # configure act
                def act(arguments, actions):
                    """Act according to the message."""
                    utils.make_errors(actions, speak)
                    try:
                        action.act(arguments, actions)
                    except action.ActionInputError as error:
                        speak(error.msg)

                # door
                # door_actions = {'open': None, 'add': None, 'modify': None,
                #                 'error': lambda: speak("I'm sorry, {0}, but I'm afraid I can't do"
                #                                        " that.".format(msg['user']))}
                # act(args, door_actions)

                # group members
                member_actions = {'add': None, 'add_away': None, 'modify': None,
                                  'import_from_slack': None}
                act(args, member_actions)

                # quiet
                # quiet_actions = {'quiet': None}
                # act(args, quiet_actions)

                # print
                # print_actions = {'print': None}
                # act(args, print_actions)

                # group meetings
                # meeting_actions = {}
                # act(args, meeting_actions)

                # money management
                # money_actions = {}
                # act(args, money_actions)

                # random draw
                # random_actions = {}
                # act(args, random_actions)

            # 1 second delay between reading from firehose
            time.sleep(1)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
