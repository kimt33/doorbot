import os
import shlex
import sqlite3
import time
from slackclient import SlackClient
import action
import utils
import door

# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# instantiate Slack clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

status_channel = [i['id'] for i in slack_client.api_call("groups.list")['groups']
                  if i['name'] == 'botty_home'][0]

# read in database
db_conn = sqlite3.connect('ayerslab.db')
cursor = db_conn.cursor()
# initiate database
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
if u'members' not in (j for i in cursor.fetchall() for j in i):
    cursor.execute('CREATE TABLE members (id INTEGER PRIMARY KEY, name TEXT, userid TEXT NOT NULL, '
                   'slack_id TEXT, email TEXT, role TEXT)')
    db_conn.commit()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
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

            public = {i['id'] for i in slack_client.api_call("channels.list")['channels']
                      if i['is_member'] == 'true'}
            private = {i['id'] for i in slack_client.api_call("groups.list")['groups']}
            ims = {i['id'] for i in slack_client.api_call("im.list")['ims']}

            # parse messages (if info is a message that has been directly messaged to bot)
            msgs = [{'user': msg['user'],
                     'channel': msg['channel'],
                     'time': msg['ts'],
                     'message': msg['text'].strip()}
                    for msg in raw_info
                    if msg['type'].startswith('message')
                    and msg['channel'] in public | private | ims
                    and msg['user'] != BOT_ID]

            # process messages
            for msg in msgs:
                if msg['message'].startswith(host):
                    args = msg['message'].replace(host, '')
                else:
                    args = msg['message']

                # parse the arguments
                args = shlex.split(args)

                # configure speak
                def speak(message):
                    """Respond to the message."""
                    action.speak(slack_client, msg['channel'], message, msg['user'])

                # configure act
                def act(arguments, actions):
                    """Act according to the message.

                    Parameters
                    ----------
                    arguments : arguments for the
                    """
                    utils.make_errors(actions, speak)
                    try:
                        action.act(arguments, actions)
                    except action.ActionInputError as error:
                        speak(error.msg)
                    except Exception as error:
                        speak('DEBUG ME:\n{0}'.format(error.msg))

                if msg['channel'].name == '1door' and args[0] != 'door':
                    args = ['door'] + args

                actions = {
                    'door': {
                        'open': ['', door.open_door, db_conn, msg['user']],
                        'add': ['', door.add, db_conn, msg['user']],
                        'modify': ['', door.change_permission, db_conn, msg['user']],
                        'print_db': ['', door.print_db, db_conn, msg['user']],
                    },
                    'members': {
                        'add': ['', None],
                        'add_away': ['', None],
                        'modify': ['', None],
                        'import_from_slack': ['', None]
                    },
                    'quiet': ['', None],
                    'print': ['', None],
                    'meetings': {
                    },
                    'money': {
                    },
                    'random': {
                    },
                }
                act(args, actions)

            # 1 second delay between reading from firehose
            time.sleep(1)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
