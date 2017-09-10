import os
import shutil
import urllib.request
from action import ActionInputError


def upload(msg):
    """Download the file provided in the Slack message data.

    Parameters
    ----------
    msg : dict
        Dictionary that contains the key 'download' and the url as the key.

    """
    try:
        url = msg['download']
    except KeyError:
        raise ActionInputError('You must upload the file and provide the command, `@bot upload`, as'
                               ' the comment to the uploaded file.')

    filename = url.split('/')[-1]
    # TODO: probably should put in some sort of limitation to the files that can be uploaded
    # if os.path.splitext(filename)[-1] != '.pdf':
    #     raise ActionInputError('You can only upload pdf files.')
    with urllib.request.urlopen(url) as response, open(os.path.join('/tmp', filename), 'wb') as fh:
        shutil.copyfileobj(response, fh)
    raise ActionInputError('Bleep bloop.')
