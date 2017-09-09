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
                    """Act according to the message."""
                    utils.make_errors(actions, speak)
                    try:
                        action.act(arguments, actions)
                    except action.ActionInputError as error:
                        speak(error.msg)
                    except TypeError:
                        # FIXME: need to handle bad input to function
                        pass

                # door
                if args[0] == 'door' or msg['channel'].name == '1door':
                    if args[0] == 'door':
                        args = args[1:]
                    door_actions = {'open': lambda: door.open_door(db_conn, msg['user']),
                                    'add': lambda: door.add(db_conn, msg['user'], *args),
                                    'modify': lambda: door.change_permission(db_conn, msg['user'],
                                                                             *args),
                                    'error': lambda: speak("I'm sorry, {0}, but I'm afraid I can't "
                                                           "do that.".format(msg['user']))}
                    act(args, door_actions)
                # members
                elif args[0] == 'members':
                    args = args[1:]
                    member_actions = {'add': None,
                                      'add_away': None,
                                      'modify': None,
                                      'import_from_slack': None}
                    act(args, member_actions)
                # quiet
                elif args[0] == 'quiet':
                    quiet_actions = {'quiet': None}
                    act(args, quiet_actions)
                # print
                elif args[0] == 'print':
                    args = args[1:]
                    print_actions = {'print': None}
                    act(args, print_actions)
                # meetings
                elif args[0] == 'meetings':
                    args = args[1:]
                    meeting_actions = {}
                    act(args, meeting_actions)
                # money
                elif args[0] == 'money':
                    args = args[1:]
                    money_actions = {}
                    act(args, money_actions)
                # random draw
                elif args[0] == 'random':
                    args = args[1:]
                    random_actions = {}
                    act(args, random_actions)
                # otherwise
                else:
                    speak("I don't understand what you want me to do. Please give one of the "
                          "following keywords: `door`, `members`, `quiet`, `print`, `meetings`, "
                          "`money`, and `random`.")

            # 1 second delay between reading from firehose
            time.sleep(1)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
