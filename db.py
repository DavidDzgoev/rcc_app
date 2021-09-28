import pandas as pd
import numpy as np
import datetime
from app import db
import requests
import json


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f'User-{self.name}'


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Float)
    rank = db.Column(db.Integer)
    league_points = db.Column(db.Integer)

    swiss_lichess_id = db.Column(db.String, db.ForeignKey('swiss.lichess_id'), nullable=False)
    swiss = db.relationship('Swiss', backref=db.backref('entries', lazy=True))

    username = db.Column(db.String, db.ForeignKey('user.name'), nullable=False)
    user = db.relationship('User', backref=db.backref('entries', lazy=True))

    def __init__(self, points, rank, league_points, swiss_lichess_id, username):
        self.points = points
        self.rank = rank
        self.league_points = league_points
        self.swiss_lichess_id = swiss_lichess_id
        self.username = username

    def __repr__(self):
        return f'<Entry-{self.swiss_lichess_id}-{self.username}>'


class Swiss(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lichess_id = db.Column(db.String, unique=True)
    name = db.Column(db.String)
    start_at = db.Column(db.Date)
    time_limit = db.Column(db.Integer)
    increment = db.Column(db.Integer)
    number_of_rounds = db.Column(db.Integer)
    number_of_players = db.Column(db.Integer)
    season_name = db.Column(db.String)

    def __init__(self, lichess_id, name, start_at, time_limit, increment, number_of_rounds, number_of_players,
                 season_name):
        self.lichess_id = lichess_id
        self.name = name
        self.start_at = start_at
        self.time_limit = time_limit
        self.increment = increment
        self.number_of_rounds = number_of_rounds
        self.number_of_players = number_of_players
        self.season_name = season_name

    def __repr__(self):
        return f'<Tournament-{self.name}-{self.lichess_id}'


class Season(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

    def __init__(self, name, start_date, end_date):
        self.name = name
        self.start_date = start_date
        self.end_date = end_date

    def __repr__(self):
        return f'{self.name}'


def calculate_league_points(rank: int, season_name):
    """
    Calculate how much leagues points players gets for the rank(place) he took on the tournament
    :param rank: int
    :param season_name: str
    :return:
    """

    # todo создать таблицу в дб
    points_dict = {
        '2021 - Spring': {
            1: 10,
            2: 7,
            3: 5,
            4: 3,
            5: 1
        },

        '2021 - Autumn': {
            x: y for x, y in zip(range(1, 11), range(10, -1, -1))
        }
    }

    try:
        season_points = points_dict[season_name]
    except KeyError:
        raise KeyError  # todo обработка ошибки

    try:
        res = season_points[rank]
        return res
    except:
        return 0


def get_season_by_date(date):
    return db.session.query(Season.name).filter((Season.start_date <= date) & (Season.end_date >= date)).first()[0]


def fill_db():
    """
    Parse data of all tournaments of the club from lichess api and collect it in the db
    :return: None
    """
    # todo: make cycle
    db.session.add(Season(
        name='2021 - Spring',
        start_date=datetime.date(2021, 4, 4),
        end_date=datetime.date(2021, 6, 13)
    ))

    db.session.add(Season(
        name='2021 - Autumn',
        start_date=datetime.date(2021, 9, 26),
        end_date=datetime.date(2021, 12, 31)
    ))
    db.session.commit()

    swiss_as_list_of_string = requests.get('https://lichess.org/api/team/romes-papa-club/swiss').text.split('\n')
    swiss_as_list_of_json = [json.loads(i) for i in swiss_as_list_of_string[:-1]]

    for swiss in swiss_as_list_of_json:
        season_name = get_season_by_date(datetime.datetime.strptime(swiss['startsAt'][:10], "%Y-%m-%d").date())
        db.session.add(Swiss(
            lichess_id=swiss['id'],
            name=swiss['name'],
            start_at=datetime.datetime.strptime(swiss['startsAt'][:10], "%Y-%m-%d").date(),
            time_limit=swiss['clock']['limit'],
            increment=swiss['clock']['increment'],
            number_of_rounds=swiss['nbRounds'],
            number_of_players=swiss['nbPlayers'],
            season_name=season_name
        ))

        entries_as_list_of_string = requests.get(
            f'https://lichess.org/api/swiss/{swiss["id"]}/results').text.split('\n')

        for entry_as_json in [json.loads(i) for i in entries_as_list_of_string[:-1]]:
            if not list(db.session.query(User).filter(User.name == entry_as_json['username']).all()):
                db.session.add(User(
                    name=entry_as_json['username']
                ))

            db.session.add(Entry(
                points=entry_as_json['points'],
                rank=entry_as_json['rank'],
                league_points=calculate_league_points(entry_as_json['rank'], season_name),
                swiss_lichess_id=swiss['id'],
                username=entry_as_json['username']
            ))

    db.session.commit()
    return


def update_db():
    """
    Update db data by comparing with lichess data
    :return:
    """
    swiss_as_list_of_string = requests.get('https://lichess.org/api/team/romes-papa-club/swiss').text.split('\n')
    swiss_as_list_of_json = [json.loads(i) for i in swiss_as_list_of_string[:-1]]

    swiss_ids = set([i['id'] for i in swiss_as_list_of_json])
    db_swiss_ids = set([i.lichess_id for i in list(db.session.query(Swiss).all())])

    swiss_as_dict = dict(zip([i['id'] for i in swiss_as_list_of_json], swiss_as_list_of_json))

    for new_swiss in swiss_ids - db_swiss_ids:
        s = swiss_as_dict[new_swiss]
        season_name = get_season_by_date(datetime.datetime.strptime(s['startsAt'][:10], "%Y-%m-%d").date())
        db.session.add(Swiss(
            lichess_id=s['id'],
            name=s['name'],
            start_at=datetime.datetime.strptime(s['startsAt'][:10], "%Y-%m-%d").date(),
            time_limit=s['clock']['limit'],
            increment=s['clock']['increment'],
            number_of_rounds=s['nbRounds'],
            number_of_players=s['nbPlayers'],
            season_name=season_name
        ))

        entries_as_list_of_string = requests.get(f'https://lichess.org/api/swiss/{s["id"]}/results').text.split(
            '\n')
        for entry_as_json in [json.loads(i) for i in entries_as_list_of_string[:-1]]:
            if not list(db.session.query(User).filter(User.name == entry_as_json['username']).all()):
                db.session.add(User(
                    name=entry_as_json['username']
                ))

            db.session.add(Entry(
                points=entry_as_json['points'],
                rank=entry_as_json['rank'],
                league_points=calculate_league_points(entry_as_json['rank'], season_name),
                swiss_lichess_id=s['id'],
                username=entry_as_json['username']
            ))

    db.session.commit()
    return


def get_leaderboard_data(season):
    """
    Return aggregated and sorted leaderbord from db
    :param season: str - season name
    :return: dict
    """
    df = pd.read_sql(db.session.query(Entry, Swiss.season_name).join(
        Swiss,
        Entry.swiss_lichess_id == Swiss.lichess_id,
        isouter=True).filter(Swiss.season_name == str(season)).statement, db.session.bind, index_col='id')

    leaderboard_as_df = df.groupby('username').agg(
        sum_league_points=('league_points', 'sum'),
        mean_points=('points', 'mean'),
        mean_rank=('rank', 'mean'),
        sum_entries=('swiss_lichess_id', 'count')
    )
    leaderboard_as_df = leaderboard_as_df.round({'mean_points': 2, 'mean_rank': 2})
    leaderboard_as_df.sort_values(by='sum_league_points', ascending=False, inplace=True)
    leaderboard_as_df.reset_index(inplace=True)

    return leaderboard_as_df.to_dict('index')


def get_prev_swiss_date(season):
    """
    Returns info about swiss by season name
    :param season:
    :return: dict
    """
    df = pd.read_sql(db.session.query(Swiss, Entry.username).join(
        Entry,
        Entry.swiss_lichess_id == Swiss.lichess_id,
        isouter=True).filter(
        (Entry.rank == 1) & (Swiss.season_name == str(season))).statement, db.session.bind, index_col='id')

    df['time_limit'] = df['time_limit'] // 60
    df['start_at'] = pd.to_datetime(df['start_at']).dt.strftime('%d.%m.%Y')

    return df.to_dict('index')


def get_seasons():
    """
    Return list of seasons names as str
    :return: list of str from old to new
    """
    return [str(i) for i in db.session.query(Season).order_by(Season.id).all()]


def get_counter_stats():
    """
    Return stats for template "О нас.html"
    :return: dict {'number_of_seasons', 'number_of_swiss', 'number_of_players'}
    """
    number_of_players = len(db.session.query(User).all())
    number_of_swiss = len(db.session.query(Swiss).all())
    number_of_seasons = len(db.session.query(Season).all())

    return {'number_of_seasons': number_of_seasons,
            'number_of_swiss': number_of_swiss,
            'number_of_players': number_of_players}


if __name__ == '__main__':
    # print(get_prev_swiss_date(None))
    # print(get_leaderboard_data(None))
    db.create_all()
    fill_db()
    # update_db()
