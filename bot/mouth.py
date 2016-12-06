
def speak(self, channel, response):
    """ Writes in the appropriate channel

    Parameters
    ----------
    channel : str
        Name of channel stored in Slack client
    response : str
        What bot will write

    """
    self.slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)
