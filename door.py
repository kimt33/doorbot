import RPi.GPIO as GPIO
from threading import Timer
import datetime
from action import ActionInputError


def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(4, GPIO.OUT)


def set_on():
    GPIO.output(4, GPIO.HIGH)


def set_off():
    GPIO.output(4, GPIO.LOW)


def set_open():
    setup()
    set_on()
    Timer(3.0, set_off).start()


def has_permission(cursor, user, level='door'):
    """Checks if user has permission to open door.

    Parameters
    ----------
    cursor : sqlite3.Cursor
        Cursor object used to retrieve infromation from the database.
    user : str
        Identification of the user.
        Can be name, userid, slack id or id.
    level : {'door', 'admin'}
        If 'door', then checks permission to open door.
        If 'admin', then checks permission to administrate door access.

    Raises
    ------
    ValueError
        If level is not one of 'door' or 'admin'

    """
    if level not in ['door', 'admin']:
        raise ValueError('`level` must be one of `door` or `admin`')

    cursor.execute('SELECT id FROM members WHERE name=? OR userid=? OR slack_id=? OR id=?',
                   (user,)*4)
    rows = cursor.fetchall()

    if len(rows) > 1:
        raise ActionInputError('I found more than one person that goes by the identification, {0}'
                               ''.format(user))
    elif len(rows) == 1:
        allowed_options = ['admin'] + ['yesdoor'] if level == 'door' else []
        cursor.execute('SELECT permission FROM door WHERE id=?', (rows[0][0], ))
        permission = cursor.fetchone()
        return permission in allowed_options
    else:
        return False


def change_permission(db_conn, user, user_to_change, permission):
    """Change value permission of a user.

    Parameters
    ----------
    db_conn : sqlite3.Connection
        Database connection object.
    user : str
        User that wants to change the permission of another user.
    user_to_change : str
        User whose permission is to change.
    permission : str
        New permission of the user.

    """
    cursor = db_conn.cursor()
    if has_permission(cursor, user, level='admin'):
        cursor.execute('SELECT * FROM members WHERE name=? OR userid=? OR slack_id=? OR id=?',
                       (user_to_change,)*4)
        rows = cursor.fetchall()
        if len(rows) == 0:
            raise ActionInputError('I could not find anyone that goes by {0}.'
                                   ''.format(user_to_change))
        elif len(rows) > 1:
            raise ActionInputError('I found multiple people that goes by {0}.'
                                   ''.format(user_to_change))
        elif permission not in ['nodoor', 'yesdoor', 'admin']:
            raise ActionInputError('New permission must be one of `nodoor`, `yesdoor`, `admin`')
        else:
            cursor.execute('UPDATE members SET permission=? WHERE id=?', (permission, rows[0][0]))
            db_conn.commit()
            raise ActionInputError('Bleep bloop')
    else:
        raise ActionInputError('You do not have the permission.')


def add(db_conn, user, user_to_add):
    """Give user permission to open door and add to the database if not already added.

    Parameters
    ----------
    db_conn : sqlite3.Connection
        Database connection object.
    user : str
        User that wants to change the permission of another user.
    user_to_add : str
        User to add to the database.

    """
    cursor = db_conn.cursor()
    if has_permission(cursor, user, level='admin'):
        # find user to add
        cursor.execute('SELECT * FROM members WHERE name=? OR userid=? OR slack_id=? OR id=?',
                       (user_to_add,)*4)
        rows = cursor.fetchall()
        if len(rows) == 0:
            raise ActionInputError('I could not find anyone that goes by {0}.'.format(user_to_add))
        elif len(rows) > 1:
            raise ActionInputError('I found multiple people that goes by {0}.'.format(user_to_add))
        else:
            cursor.execute('UPDATE door SET permission=? WHERE id=?', ('yesdoor', rows[0][0]))
            db_conn.commit()
            raise ActionInputError('Bleep bloop')
    else:
        raise ActionInputError('You do not have the permission.')


def open_door(db_conn, user):
    """Open the door.

    Parameters
    ----------
    db_conn : sqlite3.Connection
        Database connection object.
    user : str
        Person who wants to open the door.

    """
    cursor = db_conn.cursor()
    if has_permission(cursor, user, level='door'):
        set_open()
        cursor.execute("INSERT INTO doorlog (time, userid) VALUES (?,?)",
                       (str(datetime.datetime.now()), user),)
        db_conn.commit()
        raise ActionInputError('Bleep bloop')
    else:
        raise ActionInputError("I'm sorry, {0}, but I'm afraid I can't do that.".format(user))


def print_db(db_conn, user):
    """Print database of users.

    Parameters
    ----------
    db_conn : sqlite3.Connection
        Database connection object.
    user : str
        Person who wants to print database of users.

    """
    cursor = db_conn.cursor()
    cursor.execute('SELECT * FROM members')
    members = cursor.fetchall()
    cursor.execute('SELECT permission FROM door')
    permissions = cursor.fetchall()

    msg_format = u'{0:>4}{1:>30}{2:>20}{3:>12}{4:>35}{5:>12}\n'
    msg = msg_format.format('id', 'name', 'userid', 'slack_id', 'email', 'permission')
    for member, permission in zip(members, permissions):
        msg += msg_format.format(*member, *permission)
    raise ActionInputError(msg)
