
def listen(self, sounds, sound_type='dm'):
    return direct_messages(self.call_name, sounds)

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
    message : str
        Direct message
    channel : str
        Channel from which the message arrived
    (None, None)
        If the message is not directed at the bot
    """
    if not hasattr(sounds, '__iter__'):
        raise TypeError('Given sounds must be iterable')

    message, channel = None, None
    for sound in sounds:
        if not isinstance(sound, dict):
            raise TypeError('Each sound must be a dictionary')
        try:
            # FIXME: assumes that the message always starts with <@userid> if dm
            #        not so nice if multiple @user are present
            message = sound['text'].split(host)[1].strip()
            channel = sound['channel']
        except (KeyError, IndexError):
            pass
    return message, channel


