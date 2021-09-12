from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://khwvbuqamcctie' \
                                        ':7faf7cc39a759fdc3942331bff81104100cffb18a92481b9bae9e22de297f83e@ec2-34-196' \
                                        '-238-94.compute-1.amazonaws.com:5432/d6lhs24vjd9397'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['JSON_SORT_KEYS'] = False
db = SQLAlchemy(app)


@app.route("/")
def hello_world():
    update_db()
    return get_leaderboard_data()


if __name__ == '__main__':
    from db import update_db, get_leaderboard_data
    app.run()
