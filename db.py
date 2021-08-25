from main import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)

    def __init__(self, username):
        self.username = username

    def __repr__(self):
        return '<User %r>' % self.username


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Float)
    rank = db.Column(db.Integer)
    performance = db.Column(db.Integer)

    swiss_lichess_id = db.Column(db.String, db.ForeignKey('swiss.id'), nullable=False)
    swiss = db.relationship('Swiss', backref=db.backref('entries', lazy=True))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('entries', lazy=True))

    def __init__(self, points, rank, performance, swiss_lichess_id, user_id):
        self.points = points
        self.rank = rank
        self.performance = performance
        self.swiss_lichess_id = swiss_lichess_id
        self.user_id = user_id

    def __repr__(self):
        return '<Entry %r>' % self.user_id


class Swiss(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lichess_id = db.Column(db.String, unique=True)
    name = db.Column(db.String)
    start_at = db.Column(db.Time)
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
