import datetime
import action


def shush(client, db_conn, user, channel):
    """Tell people to be quiet.

    Parameters
    ----------
    client : SlackClient
        Slack client that will be used to send the message.
    db_conn : sqlite3.Connection
        Database connection object.
    user : str
        User that requests people to be quiet.
    channel : str
        Channel that will be shushed.

    """
    db_conn.execute("INSERT INTO quietlog (time, userid) VALUES (?,?)",
                    (str(datetime.datetime.now()), user))
    db_conn.commit()
    action.speak(client, channel, 'Shhhhhh', '')
    raise action.ActionInputError('Bleep bloop.')
