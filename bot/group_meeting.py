""" Module for interfacing group meeting code with bot

Takes commands from Slack client and translate them into script

"""
import re
from datetime import datetime, timedelta
from random import random
from .action import Action, BadInput, Messaging
from .utils import nice_options, where_from_identifiers

class GroupMeeting(Action):
    """ Action class for group meeting management
    """
    def __init__(self, db_conn):
        """
        Parameters
        ----------
        db_conn : sqlite3.Connection
            Database object
        """
        self.db_conn = db_conn
        self.cursor = self.db_conn.cursor()
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        if u'group_meetings' not in (j for i in self.cursor.fetchall() for j in i):
            self.cursor.execute('''CREATE TABLE group_meetings
            (id INTEGER PRIMARY KEY,
             date TEXT NOT NULL,
             presenter INTEGER,
             chair INTEGER,
             title TEXT)''')
            self.db_conn.commit()
        # FIXME: there should be a better way for this
        self.col_ids = {'id':0,
                        'date':1,
                        'presenter':2,
                        'chair':3,
                        'title':4,}

    @property
    def name(self):
        return 'group meeting'

    @property
    def init_response(self):
        return ('I can only do one of {0} when managing group meetings'
                ''.format(nice_options(self.options.keys(), 'or')))

    @property
    def options(self):
        return {'add' : self.add,
                'list' : self.list}

    def is_valid_date(self, date_str):
        """ Checks if given date is valid

        Parameters
        ----------
        date_str : str
            Date written as yyyy-mm-dd

        Returns
        -------
        True if valid
        False if not
        """
        if date_str in ['next']:
            return True
        try:
            datetime.strptime(date_str, '%Y-%m-%d').date()
            return True
        except ValueError:
            return False


    def select_member_volunteer(self, job='', date_str=''):
        """ Asks users to volunteer
        """
        pass

    def select_member_random(self, date_obj, job):
        """ Selects member

        Parameters
        ----------
        date_obj : datetime.date
            Date of presentation
        job : str
            What role is being selected
            One of ['presenter', 'chair]
        """
        # find people that are present
        people_present = []
        for row in self.cursor.execute('SELECT id, name, dates_away FROM members'):
            # translate date
            dates = re.findall(r'\d\d\d\d-\d\d-\d\d', row[2])[:2]
            dates = [datetime.strptime(i, '%Y-%m-%d').date() for i in dates]
            to_dates = dates[0::2]
            from_dates = dates[0::1]
            for to_date, from_date in zip(to_dates, from_dates):
                if to_date < date_obj:
                    # ASSUME away_dates are in descending order
                    # there is no need to loop through all dates if a date is
                    # we find a valid date
                    people_present.append(row[0])
                    break
                elif from_date <= date_obj <= to_date:
                    # if person is away on that day, break out of loop
                    break
            else:
                # if end of for loop reached
                people_present.append(row[0])

        # find time since last presentation
        time_since_last = []
        for i in people_present:
            self.cursor.execute('SELECT * FROM group_meetings WHERE {0}=?'
                                ' ORDER BY date DESC'.format(job), (i,))
            last_date = self.cursor.fetchone()
            if last_date in [None, '']:
                last_date = datetime.min.date()
            else:
                last_date = datetime.strptime(last_date[1], '%Y-%m-%d').date()
            time_since_last.append((date_obj - last_date).days)
        time_since_last = [i if i>27 else 0 for i in time_since_last]

        # you can't present and chair at the same time
        other = ''
        if job == 'presenter':
            other = 'chair'
        elif job == 'chair':
            other = 'presenter'
        self.cursor.execute("SELECT {0} FROM group_meetings WHERE date=? "
                            " AND ({1} is null OR {1}='')".format(other, job),
                            (date_obj.isoformat(), ))
        other = self.cursor.fetchone()
        if other not in ['', None]:
            time_since_last[people_present.index(other[0])] = 0

        # turn timedelta into weight
        probs = [weight*random() for weight in time_since_last]
        # normalize
        probs = [prob/sum(probs) for prob in probs]

        # winner
        return people_present[probs.index(max(probs))]

    def add(self, date_str='', job='', person=''):
        """ Add a presentation

        Parameters
        ----------
        date_str : str
            String that describes the date
            In form yyyy-mm-dd
        job : str
            One of 'presenter' or 'chair'
        person : str
            Some sort of identification of person
            Can be one of 'id', 'userid', 'slack_id', 'name'
        """
        if not self.is_valid_date(date_str):
            raise BadInput('What is the date of the presentaton?'
                           ' It must be one of "next" or "yyyy-mm-dd".')

        # get the data
        self.cursor.execute('SELECT * FROM group_meetings ORDER BY date DESC')
        row = self.cursor.fetchone()

        # find the date
        date_obj = None
        if date_str == 'next':
            last_date = datetime.strptime(row[1], '%Y-%m-%d').weekday()
            weekday_diff = timedelta(days=7 - datetime.today().weekday() + last_date)
            date_obj = datetime.today().date() + weekday_diff
            # FIXME: message
        else:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        # find job
        if job not in ['presenter', 'chair', 'both']:
            raise BadInput('What job would you like me to assign?'
                           ' It must be one of "presenter", "chair" or "both".',
                           args=(date_str,))
        # FIXME: garbage stuff
        is_fucking_hassel = False
        if job == 'both':
            job = 'presenter'
            is_fucking_hassel = True

        #find person
        if person == '':
            raise BadInput('Who would you like to assign?'
                           ' It should be a name or "random"',
                           args=(date_str, job, ))

        if person == 'random':
            person = self.select_member_random(date_obj, job)
        self.cursor.execute('SELECT id FROM members WHERE id=?'
                            ' or name=? or userid=? or slack_id=?',
                            (person, )*4)
        matches = self.cursor.fetchall()
        if len(matches) == 0:
            raise BadInput('I could not find anyone whose id, name,'
                           ' userid, or slackid is {0}.\n'
                           'Would you care to try again?'.format(person),
                           args=(date_str, job,))
        elif len(matches) > 1:
            raise BadInput('I found more than one person whose id, name,'
                           ' userid, or slackid is {0}.\n'
                           'Would you care to try again?'.format(person),
                           args=(date_str, job,))
        else:
            person = matches[0][0]

        # Add data
        self.cursor.execute('SELECT * FROM group_meetings WHERE date=?',
                            (date_obj.isoformat(), ))
        rows = self.cursor.fetchall()
        if len(rows) == 0:
            self.cursor.execute('INSERT INTO group_meetings (date, {0})'
                                ' VALUES (?,?)'.format(job),
                                (date_obj.isoformat(), person))
        elif len(rows) == 1:
            if rows[0][self.col_ids[job]] in [None, '']:
                self.cursor.execute('UPDATE group_meetings SET {0}=? WHERE id=?'.format(job),
                                    (person, rows[0][self.col_ids['id']]))
            else:
                # FIXME
                raise Messaging('There already is a person assigned.')
        else:
            # FIXME
            raise Messaging('There are more than one meetings to assign to.'
                            " I don't know what to do.")
        self.db_conn.commit()

        #FIXME: PLOP PLOP
        if is_fucking_hassel:
            self.add(date_str, 'chair', 'random')

    def list(self):
        """ Shows all presentations that satifies some conditions

        Parameters
        ----------
        """
        #FIXME: identifier?
        self.cursor.execute('SELECT * FROM group_meetings ORDER BY date DESC')
        rows = self.cursor.fetchall()
        message = '{0:<4}{1:<10}{2:<20}{3:<20}{4:<40}\n'.format('id', 'date', 'presenter', 'chair', 'title')
        for row in rows:
            data_id = row[0]
            date = row[1]
            self.cursor.execute('SELECT name FROM members WHERE id=?', (row[2],))
            presenter = str(self.cursor.fetchone())
            self.cursor.execute('SELECT name FROM members WHERE id=?', (row[3],))
            chair = str(self.cursor.fetchone())
            title = row[4]
            message += '{0:<4}{1:<10}{2:<20}{3:<20}{4:<40}\n'.format(data_id, date, presenter, chair, title)
        raise Messaging(message)

    def modify(self, item='', to_val='', *identifiers):
        """ Modifies existing group meeting data

        Parameters
        ----------
        item : str
            One of 'id', 'date', 'presenter', 'chair', or 'title'
            or 'permission'
        to_val : str
            Value to change to
        identifiers : list
            List of alternating key and value of the person
        """
        if item == '' or item not in self.col_ids.keys():
            raise BadInput('What would you like to change? It should be'
                           ' one of {0}'.format(nice_options(self.col_ids.keys())))
        if to_val == '':
            raise BadInput('What would you like to change it to?',
                           args=(item,))

        if item == 'date' and not self.is_valid_date(to_val):
            raise BadInput('The date must be one of "next" or "yyyy-mm-dd".')

        # check identifier
        if len(identifiers) == 0 or (len(identifiers) % 2 == 1 and
                                     identifiers[-1] not in self.col_ids.keys()):
            raise BadInput('What can you tell me about this presentation?'
                           ' You can give me one of {0}.'
                           ''.format(nice_options(self.col_ids.keys())),
                           args=(item, to_val) + tuple(identifiers[:-1]))
        elif len(identifiers) % 2 == 1:
            raise BadInput('What is the {0} of this presentation?'
                           ''.format(identifiers[-1]),
                           args=(item, to_val) + tuple(identifiers))

        where_command, vals = where_from_identifiers(*identifiers)
        self.cursor.execute('SELECT * FROM members {0} '.format(where_command), vals)
        rows = self.cursor.fetchall()
        if len(rows) == 0:
            messages = ['{0} is {1}'.format(i, j) for i, j in zip(identifiers, identifiers[1:])]
            raise Messaging('I could not find any presentation where {0}'
                            ''.format(nice_options(messages, 'and')))
        elif len(rows) > 1:
            messages = ['{0} is {1}'.format(i, j) for i, j in zip(identifiers, identifiers[1:])]
            raise BadInput('There seems to be more than one presentation where {0}.'
                           ' Could you tell me more about this person?'
                           ' You can give me one of {1}.'
                           ''.format(nice_options(messages, 'and'),
                                     nice_options(self.col_ids.keys())),
                           args=(item, to_val) + tuple(identifiers))
        else:
            self.cursor.execute('UPDATE members SET {0}=? WHERE id=?'.format(item),
                                (to_val, rows[0][0]))
            self.db_conn.commit()
