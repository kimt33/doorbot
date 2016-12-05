
def speak(self, channel, response):
    self.slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)
