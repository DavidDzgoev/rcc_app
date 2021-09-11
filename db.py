import pandas as pd
import numpy as np
import datetime
from main import db
import requests
import json


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Float)
    rank = db.Column(db.Integer)
    league_points = db.Column(db.Integer)

    swiss_lichess_id = db.Column(db.String, db.ForeignKey('swiss.id'), nullable=False)
    swiss = db.relationship('Swiss', backref=db.backref('entries', lazy=True))

    username = db.Column(db.Integer, db.ForeignKey('user.name'), nullable=False)
    user = db.relationship('User', backref=db.backref('entries', lazy=True))

    def __init__(self, points, rank, league_points, swiss_lichess_id, username):
        self.points = points
        self.rank = rank
        self.league_points = league_points
        self.swiss_lichess_id = swiss_lichess_id
        self.username = username

    def __repr__(self):
        return '<Entry %r>' % self.username


class Swiss(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lichess_id = db.Column(db.String, unique=True)
    name = db.Column(db.String)
    start_at = db.Column(db.Date)
    time_limit = db.Column(db.Integer)
    increment = db.Column(db.Integer)
    number_of_rounds = db.Column(db.Integer)
    number_of_players = db.Column(db.Integer)

    def __init__(self, lichess_id, name, start_at, time_limit, increment, number_of_rounds, number_of_players):
        self.lichess_id = lichess_id
        self.name = name
        self.start_at = start_at
        self.time_limit = time_limit
        self.increment = increment
        self.number_of_rounds = number_of_rounds
        self.number_of_players = number_of_players

    def __repr__(self):
        return '<Tournament %r>' % self.name


def calculate_league_points(rank: int):
    """
    Calculate how much leagues points players gets for the rank(place) he took on the tournament
    :param rank: int
    :return:
    """
    points_dict = {
        1: 10,
        2: 7,
        3: 5,
        4: 3,
        5: 1
    }
    if rank > 5:
        return 0
    else:
        return points_dict[rank]


def fill_db():
    """
    Parse data from lichess api and collect it in the db
    :return: None
    """
    swiss_as_list_of_string = requests.get('https://lichess.org/api/team/romes-papa-club/swiss').text.split('\n')
    swiss_as_list_of_json = [json.loads(i) for i in swiss_as_list_of_string[:-1]]

    db_users_as_set = set(User.query.all())
    swiss_users_as_set = set()

    for swiss in swiss_as_list_of_json:
        db.session.add(Swiss(
            lichess_id=swiss['id'],
            name=swiss['name'],
            start_at=datetime.datetime.strptime(swiss['startsAt'][:10], "%Y-%m-%d").date(),
            time_limit=swiss['clock']['limit'],
            increment=swiss['clock']['increment'],
            number_of_rounds=swiss['nbRounds'],
            number_of_players=swiss['nbPlayers']
        ))

        entries_as_list_of_string = requests.get(f'https://lichess.org/api/swiss/{swiss["id"]}/results').text.split(
            '\n')
        for entry_as_json in [json.loads(i) for i in entries_as_list_of_string[:-1]]:
            swiss_users_as_set.add(entry_as_json['username'])

            db.session.add(Entry(
                points=entry_as_json['points'],
                rank=entry_as_json['rank'],
                league_points=calculate_league_points(entry_as_json['rank']),
                swiss_lichess_id=swiss['id'],
                username=entry_as_json['username']
            ))

    new_users = swiss_users_as_set - db_users_as_set
    for username in new_users:
        db.session.add(User(
            name=username
        ))

    db.session.commit()
    return


def make_leaderboard():
    """
    Make aggregated and sorted leaderbord from db
    :return: dict
    """
    df = pd.read_sql(db.session.query(Entry).statement, db.session.bind, index_col='id')
    leaderboard_as_df = df.groupby('username').agg(sum_league_points=('league_points', 'sum'),
                                                   mean_points=('points', 'mean'),
                                                   mean_rank=('rank', 'mean'),
                                                   sum_entries=('swiss_lichess_id', 'count')
                                                   )
    leaderboard_as_df.sort_values(by='sum_league_points', ascending=False, inplace=True)

    return leaderboard_as_df.to_dict('index')


if __name__ == '__main__':
    db.create_all()
    fill_db()
