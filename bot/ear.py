
def listen(self, sounds, sound_type='dm'):
    if sound_type == 'dm':
        return direct_messages(self.call_name, sounds)
    elif sound_type == 'all':
        return all_messages(self.call_name, sounds)

def direct_messages(host, sounds):
    """ Extract direct message from input

    Parameters
    ----------
    host : str
        User receiving the message
    sounds : str
        Real time messages from Slack client.
        Output of rtm_read() from a Slack client

    Returns
    -------
    sound : dict
        'channel' : str
            Channel from which the message arrived
        'user' : str
            User from which the message is sent
        'message' : str
            Direct message
        {}
            If the message is not directed at the bot
    """
    if not hasattr(sounds, '__iter__'):
        raise TypeError('Given sounds must be iterable')

    output = {}
    for sound in sounds:
        # NOTE: not too sure what multiple sound means
        if not isinstance(sound, dict):
            raise TypeError('Each sound must be a dictionary')
        try:
            # FIXME: assumes that the message always starts with <@userid> if dm
            #        not so nice if multiple @user are present
            output['message'] = sound['text'].split(host)[1].strip()
            output['channel'] = sound['channel']
            output['user'] = sound['user']
            output['time'] = sound['ts']
        except (KeyError, IndexError):
            pass
    return output


def all_messages(host, sounds):
    """ Extract all messages from input

    Parameters
    ----------
    host : str
        User receiving the message
    sounds : str
        Real time messages from Slack client.
        Output of rtm_read() from a Slack client

    Returns
    -------
    sound : dict
        'channel' : str
            Channel from which the message arrived
        'user' : str
            User from which the message is sent
        'message' : str
            Message
        'dm' : bool
            True if direct message
            False if direct message
        {}
            If the message is not directed at the bot
    """
    if not hasattr(sounds, '__iter__'):
        raise TypeError('Given sounds must be iterable')

    output = {}
    for sound in sounds:
        # NOTE: not too sure what multiple sound means
        if not isinstance(sound, dict):
            raise TypeError('Each sound must be a dictionary')
        try:
            if host in sound['text']:
                output['message'] = sound['text'].split(host)[1].strip()
                output['dm'] = True
            else:
                output['message'] = sound['text'].strip()
                output['dm'] = False
            output['channel'] = sound['channel']
            output['user'] = sound['user']
            output['time'] = sound['ts']
        except (KeyError, IndexError):
            pass
    return output
