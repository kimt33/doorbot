"""Module for managing group member database."""
from action import ActionInputError
import utils


def add(db_conn, *args):
    """Adds a member to the database.

    Parameters
    ----------
    name : str
        Name of person.
    userid : str
        (Slack) User ID of person.
    email : str
        Email of person.
    role : str
        Role of person.
        One of 'Undergrad', "Master's", "Ph.D.", "Postdoc", and "Professor".

    """
    try:
        name, userid, slack_id, email, role = args
    except TypeError:
        raise ActionInputError('To add a member to the Ayer\'s lab group member database, you must '
                               'provide the name, (Slack) userid, email, and position of the '
                               'new member in the given order. Each entry must be delimited from '
                               'one another with a comma. If you are missing any of these '
                               'information, just leave the information blank.')
    db_conn.cursor().execute('INSERT INTO members (name, userid, email, role) VALUES (?,?,?,?)',
                             (name, userid, email, role))
    db_conn.commit()


def modify(db_conn, item, to_val, *identifiers):
    """Modify existing member data.

    Parameters
    ----------
    item : str
        One of 'id', 'name', 'userid', 'email', or 'role'.
    to_val : str
        Value to which data is changed.
    identifiers : list
        List of alternating keys and values that identify the person.

    """
    where_command, vals = utils.where_from_identifiers(*identifiers)
    cursor = db_conn.cursor()
    cursor.execute('SELECT * FROM members {0} '.format(where_command), vals)
    rows = cursor.fetchall()
    if len(rows) == 0:
        raise ActionInputError('I could not find anyone from those information.')
    elif len(rows) > 1:
        raise ActionInputError('I found multiple peopl that match those descriptions. '
                               'Could you be more specific?')
    else:
        cursor.execute('UPDATE members SET {0}=? WHERE id=?'.format(item), (to_val, rows[0][0]))
        db_conn.commit()


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
                 'role': 'Role'}
    col_formats = {'id': '{: <4}',
                   'name': '{: <30}',
                   'userid': '{: <10}',
                   'slack_id': '{: <20}',
                   'email': '{: <40}',
                   'role': '{: <20}'}
    col_ids = {'id': 0,
               'name': 1,
               'userid': 2,
               'slack_id': 3,
               'email': 4,
               'role': 5}

    cursor = db_conn.cursor()

    if len(column_identifiers) == 0:
        column_identifiers = {'id', 'name', 'userid', 'slack_id', 'email', 'role'}

    diff = set(col_names.keys()).diff(set(column_identifiers))
    if len(diff) != 0:
        raise ActionInputError('I could not find any information that goes by {0}'.format(diff))

    message_format = u''.join(col_formats[i] for i in column_identifiers) + u'\n'
    message = message_format.format(*[col_names[i] for i in column_identifiers])

    for row in cursor.execute('SELECT * FROM members ORDER BY dates_away'):
        row_data = []
        for identifier in column_identifiers:
            index = col_ids[identifier]
            row_data.append(row[index])
        # construct message
        message += message_format.format(*row_data)

    raise ActionInputError(message)


def import_from_slack(slack_client, db_conn):
    """Import the group member information from Slack Client."""
    names = []
    userids = []
    slack_ids = []
    emails = []
    roles = []

    cursor = db_conn.cursor()

    for i in slack_client.api_call('users.list')['members']:
        # check if already in database
        cursor.execute("SELECT rowid FROM members WHERE userid = ?", (i['name'],))
        if cursor.fetchone():
            continue

        names.append(i['profile'].get('real_name', ''))
        userids.append(i['name'])
        slack_ids.append(i['id'])
        emails.append(i['profile'].get('email', ''))
        roles.append('')
        cursor.executemany('INSERT INTO members (name, userid, slack_id, email, role) '
                           'VALUES (?,?,?,?,?)',
                           zip(names, userids, slack_ids, emails, roles))
    db_conn.commit()
