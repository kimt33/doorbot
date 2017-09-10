"""Module for managing group member database."""
from action import ActionInputError
import utils


def has_permission(cursor, user):
    """Checks if user has permission to modify database.

    Parameters
    ----------
    cursor : sqlite3.Cursor
        Cursor object used to retrieve infromation from the database.
    user : str
        Identification of the user.
        Can be name, userid, slack id or id.

    """
    cursor.execute('SELECT permission FROM members WHERE name=? OR userid=? OR slack_id=? OR '
                   'id=?', (user,)*4)
    rows = cursor.fetchall()

    if len(rows) > 1:
        raise ActionInputError('I found more than one person that goes by the identification, {0}'
                               ''.format(user))
    else:
        return len(rows) == 1 and rows[0][0] == 'admin'


def add(db_conn, user, name, userid, slack_id, email, role, permission, door_permission):
    """Adds a member to the database.

    Parameters
    ----------
    user : str
        Identification of the user that wants to add a member.
        Can be name, userid, slack id or id.
    name : str
        Name of person.
    userid : str
        (Slack) User ID of person.
    slack_id : str
        Identificaiton used within slack.
    email : str
        Email of person.
    role : str
        Role of person.
        One of 'Undergrad', "Master's", "Ph.D.", "Postdoc", and "Professor".
    permission : str
        Permission to control the bot.
        One of 'user' or 'admin'
    door_permission : str
        Permission to open the door.
        One of 'yesdoor' or  'nodoor'

    """
    cursor = db_conn.cursor()
    if has_permission(cursor, user):
        cursor.execute('INSERT INTO members (name, userid, slack_id, email, role, permission,'
                       ' door_permission) VALUES (?,?,?,?,?,?,?)',
                       (name, userid, slack_id, email, role, permission, door_permission))
        db_conn.commit()
    else:
        raise ActionInputError("You do not have the permission to add a new user.")


def modify(db_conn, user, item, to_val, *identifiers):
    """Modify existing member data.

    Parameters
    ----------
    db_conn : sqlite3.Connection
        Database connection object.
    user : str
        User that wants to change the information on a user.
    item : str
        One of 'id', 'name', 'userid', 'email', 'role', 'permission', 'door_permission'.
    to_val : str
        Value to which data is changed.
    identifiers : list
        List of alternating keys and values that identify the person.

    """
    if len(identifiers) % 2 != 0:
        raise ActionInputError('The identifier of the member must alternate between the item type '
                               'and the item value. For example, to find me, you can write `name '
                               'slackbot`')
    where_command, vals = utils.where_from_identifiers(*identifiers)

    cursor = db_conn.cursor()
    cursor.execute('SELECT id, slack_id, userid, name FROM members {0} '.format(where_command),
                   vals)
    rows = cursor.fetchall()
    if len(rows) == 0:
        raise ActionInputError('I could not find anyone from those information.')
    elif len(rows) > 1:
        raise ActionInputError('I found multiple people that match those descriptions. '
                               'Could you be more specific?')
    elif (has_permission(cursor, user) or
          (user in rows[0] and item not in ['permission', 'door_permission'])):
        cursor.execute('UPDATE members SET {0}=? WHERE id=?'.format(item), (to_val, rows[0][0]))
        db_conn.commit()
        raise ActionInputError('Bleep bloop')
    else:
        raise ActionInputError("You do not have the permission to modify this user's information")


def list(db_conn, *column_identifiers):
    """List the group members and their information.

    Parameters
    ----------
    column_identifiers : list
        List of columns that will be used to construct the list

    """
    col_names = {'id': 'Database ID',
                 'name': 'Name',
                 'userid': 'User ID',
                 'slack_id': 'Slack ID',
                 'email': 'Email',
                 'role': 'Role',
                 'door_permission': 'Door Permission',
                 'permission': 'Permission'}
    col_formats = {'id': '{: <12}',
                   'name': '{: <30}',
                   'userid': '{: <20}',
                   'slack_id': '{: <20}',
                   'email': '{: <40}',
                   'role': '{: <20}',
                   'door_permission': '{: <17}',
                   'permission': '{: <12}'}

    cursor = db_conn.cursor()

    if len(column_identifiers) == 0:
        column_identifiers = ['id', 'name', 'userid', 'slack_id', 'email', 'role',
                              'door_permission', 'permission']

    diff = set(column_identifiers) - set(col_names.keys())
    if len(diff) != 0:
        raise ActionInputError('I could not find any information that goes by {0}'.format(diff))

    message_format = u''.join(col_formats[i] for i in column_identifiers) + u'\n'
    message = message_format.format(*[col_names[i] for i in column_identifiers])

    for row in cursor.execute('SELECT {0} FROM members'.format(', '.join(column_identifiers))):
        # construct message
        message += message_format.format(*row)

    raise ActionInputError('\n' + message)


def import_from_slack(slack_client, db_conn):
    """Import the group member information from Slack Client."""
    names = []
    userids = []
    slack_ids = []
    emails = []
    roles = []
    permissions = []
    doors = []

    cursor = db_conn.cursor()

    for i in slack_client.api_call('users.list')['members']:
        # check if already in database
        cursor.execute("SELECT id FROM members WHERE slack_id = ?", (i['name'],))
        if cursor.fetchone():
            continue

        names.append(i['profile'].get('real_name', ''))
        userids.append(i['name'])
        slack_ids.append(i['id'])
        emails.append(i['profile'].get('email', ''))
        roles.append('')
        permissions.append('user')
        doors.append('nodoor')
    cursor.executemany('INSERT INTO members (name, userid, slack_id, email, role, permission, '
                       'door_permission) VALUES (?,?,?,?,?,?,?)',
                       zip(names, userids, slack_ids, emails, roles, permissions, doors))
    db_conn.commit()
