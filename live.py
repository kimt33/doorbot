import os
import shlex
import sqlite3
import time
from slackclient import SlackClient
import action
import utils
import door
import members

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
if u'door' not in (j for i in cursor.fetchall() for j in i):
    cursor.execute('CREATE TABLE door (id INTEGER PRIMARY KEY, permission TEXT NOT NULL)')
    cursor.execute('SELECT id FROM members')
    for i in cursor.fetchall():
        cursor.execute('INSERT INTO door (permission) VALUES (?)', ('admin',))
    db_conn.commit()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
if u'doorlog' not in (j for i in cursor.fetchall() for j in i):
    cursor.execute('''CREATE TABLE doorlog
    (id INTEGER PRIMARY KEY,
        time TEXT NOT NULL,
        userid TEXT NOT NULL)''')
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

            # parse messages (if info is a message that has been directly messaged to bot)
            msgs = [{'user': msg['user'],
                     'channel': msg['channel'],
                     'time': msg['ts'],
                     'message': msg['text'].strip()}
                    for msg in raw_info
                    if msg['type'].startswith('message')
                    and 'subtype' not in msg  # skip edited messages
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
                        speak(str(error))
                    except Exception as error:
                        speak('I ENCOUNTERED AN UNEXPECTED ERROR. DEBUG ME HUMAN!')
                        raise error

                cursor.execute("SELECT userid FROM members WHERE slack_id = ?", (msg['user'],))
                try:
                    readable_user = cursor.fetchone()[0]
                except IndexError:
                    readable_user = msg['user']
                dict_channels = {i['name']: i['id']
                                 for i in slack_client.api_call("channels.list")['channels']}

                if msg['channel'] == dict_channels['1door'] and args[0] != 'door':
                    args = ['door'] + args

                actions = {
                    'door': {
                        'open': ['', door.open_door, db_conn, readable_user],
                        'add': ['To add a user to access the door, you must provide an '
                                'identification of the user, like their name or Slack id.',
                                door.add, db_conn, readable_user],
                        'modify': ["To modify a user's permission to open the door, you must "
                                   "provide the identification of the user whose permission you'd "
                                   "like to change and the type of permission. The permission can "
                                   "be one of `yesdoor`, `nodoor`, and `admin`.",
                                   door.change_permission, db_conn, readable_user],
                        'print_db': ['', door.print_db, db_conn, readable_user],
                    },
                    'members': {
                        'add': ['To add a member to the Ayer\'s lab group member database, you must'
                                ' provide the name, (Slack) userid, email, and position of the '
                                'new member in the given order. The entries are space delimited, '
                                'which means that you must encase multiword entries within quotes. '
                                'If you are missing any of these information, just leave the '
                                'information blank.',
                                members.add, db_conn],
                        'modify': ["To modify a member's information in the database, you must "
                                   "provide the column that you'd like to modify, the new value, "
                                   "and identifiers of the members (alternating between the column "
                                   "and its value).",
                                   members.modify, db_conn],
                        'list': ["To list the members' information in the database, you must "
                                 "provide the idenfiers of the members (alternating between the "
                                 "column and its value).",
                                 members.list, db_conn],
                        'import_from_slack': ['', members.import_from_slack, slack_client, db_conn]
                    },
                    'quiet': ['', None],
                    'print': ['', None],
                    # 'meetings': {
                    # },
                    # 'money': {
                    # },
                    # 'random': {
                    # },
                }
                act(args, actions)

            # 1 second delay between reading from firehose
            time.sleep(1)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
