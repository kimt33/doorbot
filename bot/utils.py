""" Little tools that prevents me from going crazy
"""

def nice_options(options, end_delimiter='or', last_comma=True):
    """ Turns a list of things into syntatically nice english list

    Parameters
    ----------
    options : list
        List of words
    end_delimited : str
        Word that will be used for the last item

    Example
    -------
    >>> nice_options(['a','b','c'], end_delimited='or')
    'a, b, or c'

    """
    phrase = ', '.join(options[:-1])
    if last_comma:
        end_delimiter = ', {0}'.format(end_delimiter)
    if len(options) > 1:
        phrase += '{0} {1}'.format(end_delimiter, options[-1])
    return phrase
