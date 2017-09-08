"""Module for wrapping basic actions of the slack bot."""


def speak(client, channel, message, user):
    """Send message through Slack client.

    Parameters
    ----------
    client : SlackClient
        Slack client that will be used to send the message.
    channel : str
        Name of channel stored in Slack client
    message : str
        What bot will write
    user : str
        User to directly message

    """
    message = '<@{0}> {1}'.format(user, message)
    client.api_call("chat.postMessage", channel=channel, text=message, as_user=True)


class ActionInputError(Exception):
    """Exception raised within the provided action for bad input."""
    pass


def act(arguments, actions):
    """Executes appropriate actions given the string arguments.

    Parameters
    ----------
    arguments : list of str
        Arguments provided by the user.
    actions : dict
        Actions that corresponds to the given arguments.
        Dictionary where the keys are the arguments provided by the user and the values are the
        actions that corresponds to the arguments.
        If multiple arguments are required to trigger an action, the dictionary can be nested for
        additional arguments.
        The values are the action that will be executed. It will be a function that requires no
        arguments (this function will be executed without arguments).
        Each level of action must contain an error key that handles the action upon bad input.

    Raises
    ------
    ValueError
        If the given actions does not contain the key 'error'.

    """
    try:
        actions[arguments[0]](*arguments[1:])
    # NOTE: arguments[1:] will not raise an error if index 1 is out of bounds. it will just return
    #       and empty array
    # NOTE: KeyError will be caught first due to the order of execution.
    except (KeyError, IndexError):
        if 'error' not in actions:
            raise ValueError('The provided set of actions must contain the key `error` to handle '
                             'behaviour when bad arguments are provided:\n{0}'.format(actions))
        actions['error']()
    except TypeError:
        act(arguments[1:], actions[arguments[0]])
