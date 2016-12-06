
def speak(self, channel, response, dm=''):
    """ Talks through Slack client

    Parameters
    ----------
    channel : str
        Name of channel stored in Slack client
    response : str
        What bot will write
    dm : str
        User to directly message

    """
    if dm != '':
        response = '<@{0}> {1}'.format(dm, response)
    self.slack_client.api_call("chat.postMessage", channel=channel,
                               text=response, as_user=True)
