""" Module for interfacing group member database with bot

Takes commands from Slack client and translate them into script

"""
import re
from datetime import datetime, date
from . import action

class GroupMember(action.Action):
    """ Action class for group member management
    """
    def __init__(self, actor):
        """
        Parameters
        ----------
        actor : Brain
            Brain instance that describes the acting bot
        db : str
            Name of the database file
        """
        super(GroupMember, self).__init__(actor)
        self.db_conn = self.actor.db_conn
        self.cursor = self.actor.cursor
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        if u'members' not in (j for i in self.cursor.fetchall() for j in i):
            self.cursor.execute('''CREATE TABLE members
            (id INTEGER PRIMARY KEY,
             name TEXT,
             userid TEXT NOT NULL,
             slack_id TEXT,
             email TEXT,
             role TEXT,
             dates_away TEXT,
             permission TEXT)''')
            self.db_conn.commit()
        # FIXME: there hsould be a better way for this
        self.col_ids = {'id':0,
                        'name':1,
                        'userid':2,
                        'slack_id':3,
                        'email':4,
                        'role':5,
                        'dates_away':6,
                        'permission':7}

    @property
    def name(self):
        return 'members'

    @property
    def init_response(self):
        return ('I can only do one of {0}'
                ' when managing group members').format(self.options.keys())

    @property
    def options(self):
        return {'add':self.add, 'list':self.list, 'modify':self.modify,
                'import':self.import_from_slack}

    def add(self, name='', userid='', slack_id='', email='', role='', is_away='', permission=''):
        if name == '':
            raise action.BadInputError('What is their name?')
        if userid == '':
            raise action.BadInputError("What is their Slack username?"
                                       " If you don't know, just write `None`.",
                                       args=(name,))
        if slack_id == '':
            raise action.BadInputError("What is their Slack ID?"
                                       " If you don't know, just write `None`",
                                       args=(name, userid))
        if email not in ['', 'None']:
            raise action.BadInputError('What is their email address?',
                                       args=(name, userid, slack_id))

        roles = ['undergrad', 'Master\'s', 'PhD', 'Postdoc', 'Professor']
        if role == '' or role not in roles:
            raise action.BadInputError('What is their role in the group?'
                                       ' It should be one of {0}.'.format(roles),
                                       args=(name, userid, slack_id, email))
        if is_away == '' and is_away in ['yes', 'no']:
            raise action.BadInputError('Are they away from the lab? It should be one of "yes" or "no".',
                                       args=(name, userid, slack_id, email, role))
        dates_away = ''
        if is_away == 'yes':
            dates_away = '(9999-12-31:{0})'.format(date.today().isoformat())
        elif is_away == 'no':
            dates_away = ''

        permission = 'user'

        if userid == 'None':
            userid = ''
        if slack_id == 'None':
            slack_id = ''

        self.cursor.execute('INSERT INTO members'
                            ' (name, userid, slack_id, email, role, dates_away, permission)'
                            ' VALUES (?,?,?,?,?,?,?)',
                            (name, userid, slack_id, email, role, dates_away, permission))
        self.db_conn.commit()

    def modify(self, item='', to_val='', *identifiers):
        if item == '' or item not in self.col_ids.keys():
            raise action.BadInputError('What would you like to change? It should be'
                                       ' one of {0}'.format(self.col_ids.keys()))
        if to_val == '':
            raise action.BadInputError('What would you like to change it to?',
                                       args=(item,))
        if len(identifiers) == 0:
            raise action.BadInputError('Can you tell me more about this person?'
                                       ' Could you tell me the one or more of {0}}?'
                                       ' And could you delimit the value with `=`?'
                                       ' For example, `name=ayersbot`.'.format(self.col_ids.keys()),
                                       args=(item, to_val))

        where_command = ' WHERE '
        vals = []
        for identifier in identifiers:
            key, val = identifier.split('=')
            where_command += '{0}=? '.format(key)
            vals.append(val)

        self.cursor.execute('SELECT * FROM members'+where_command, vals)
        rows = self.cursor.fetchall()
        if len(rows) == 0:
            raise action.BadInputError('I could not find anyone using {0}'.format(identifiers))
        elif len(rows) > 1:
            raise action.BadInputError('There seems to be more than one person that'
                                       ' satisfies {0}. Could you give more information'
                                       ' on the person?'.format(identifiers),
                                       args=(item, to_val) + tuple(identifiers))
        # update table
        self.cursor.execute('UPDATE members SET {0}=?'.format(item)+where_command,
                            [to_val,]+vals)
        self.db_conn.commit()

    def list(self, *column_identifiers):
        col_names =  {'id':'Database ID',
                      'name':'Name',
                      'userid':'User ID',
                      'slack_id':'Slack ID',
                      'email':'Email',
                      'role':'Role',
                      'dates_away':'Dates Away',
                      'is_away':'Away?',
                      'permission':'Permission'}
        col_formats = {'id':'{:<4}',
                       'name':'{:>30}',
                       'userid':'{:>10}',
                       'slack_id':'{:>20}',
                       'email':'{:>40}',
                       'role':'{:>20}',
                       'dates_away':'{:>15}',
                       'is_away':'{:>15}',
                       'permission':'{:>12}'}

        if len(column_identifiers) == 0:
            # column_identifiers = ['id', 'name', 'userid', 'email', 'role', 'is_away', 'permission']
            column_identifiers = ['id', 'name', 'userid', 'slack_id', 'email', 'role', 'dates_away', 'is_away', 'permission']

        message_format = u''.join(col_formats[i] for i in column_identifiers) + u'\n'
        message = message_format.format(*[col_names[i] for i in column_identifiers])

        for row in self.cursor.execute('SELECT * FROM members ORDER BY dates_away'):
            row_data = []
            for identifier in column_identifiers:
                # find dates
                if identifier == 'is_away':
                    dates = re.findall(r'\d\d\d\d-\d\d-\d\d', row[self.col_ids['dates_away']])
                    to_dates = dates[0::2]
                    from_dates = dates[1::2]
                    is_away = 'no'
                    for to_date, from_date in zip(to_dates, from_dates):
                        to_date = datetime.strptime(to_date, '%Y-%m-%d')
                        from_date = datetime.strptime(from_date, '%Y-%m-%d')
                        if from_date <= datetime.today() < to_date:
                            is_away = 'yes'
                            break
                    row_data.append(is_away)
                else:
                    index = self.col_ids[identifier]
                    row_data.append(row[index])
            # construct message
            message += message_format.format(*row_data)
        raise action.Messaging(message)

    def import_from_slack(self):
        names = []
        userids = []
        slack_ids = []
        emails = []
        roles = []
        away_dates = []
        permissions = []
        def check(profile, text):
            try:
                return profile[text]
            except KeyError:
                return ''
        for i in self.actor.slack_client.api_call('users.list')['members']:
            names.append(check(i['profile'], 'real_name'))
            userids.append(i['name'])
            slack_ids.append(i['id'])
            emails.append(check(i['profile'], 'email'))
            roles.append('')
            if 'status' not in i:
                away_dates.append('(9999-12-31:{0})'.format(date.today().isoformat()))
            else:
                away_dates.append('')
            permissions.append('user')
        self.cursor.executemany("""INSERT INTO members
                                (name, userid, slack_id, email, role, dates_away, permission)
                                VALUES (?,?,?,?,?,?,?)""",
                                zip(names, userids, slack_ids, emails, roles, away_dates, permissions))
        self.db_conn.commit()
