""" Little tools that prevents me from going crazy
"""

def nice_options(options, end_delimiter='or', last_comma=True, quote='`'):
    """ Turns a list of things into syntatically nice english list

    Parameters
    ----------
    options : list
        List of words
    end_delimited : str
        Word that will be used for the last item
    last_comma : bool
        Flag for adding comma before the final delimiter
    quote : str
        String that will encase each word

    Example
    -------
    >>> nice_options(['a','b','c'], end_delimited='or')
    'a, b, or c'

    """
    options = ['{0}{1}{0}'.format(quote, i) for i in options]
    phrase = ', '.join(options[:-1])
    if last_comma:
        end_delimiter = ', {0}'.format(end_delimiter)
    if len(options) > 1:
        phrase += '{0} {1}'.format(end_delimiter, options[-1])
    return phrase

def where_from_identifiers(*identifiers):
    """ Given a set of identifiers, constructs the WHERE command that retrieves
    that matches the identifiers

    Parameters
    ----------
    identifiers : list
        List of alternating keys and values

    Returns
    -------
    where_command : str
        WHERE command that is used in sql
    vals : list
        List of values that will be assigned to each key
    rows : list
        List of SQL rows
    """
    where_command = ''
    vals = []
    if len(identifiers) > 0:
        where_command += 'WHERE '
        keys = identifiers[0::2]
        vals = identifiers[1::2]
        where_command += ' '.join('{0}=?'.format(i) for i in keys)
    return where_command, vals
