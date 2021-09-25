from flask import Flask, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__, template_folder='templates/test', static_url_path='', static_folder='templates/test')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rcc.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://khwvbuqamcctie' \
                                        ':7faf7cc39a759fdc3942331bff81104100cffb18a92481b9bae9e22de297f83e@ec2-34-196' \
                                        '-238-94.compute-1.amazonaws.com:5432/d6lhs24vjd9397'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['JSON_SORT_KEYS'] = False
db = SQLAlchemy(app)


@app.route('/')
async def root():
    return redirect('/about', code=302)


@app.route('/standings')
async def standings(season=None):
    update_db()
    return render_template('Таблица-лидеров.html', df=get_leaderboard_data())


@app.route('/prev_swiss')
async def prev_swiss(season=None):
    update_db()
    return render_template('Предыдущие-турниры.html', df=get_leaderboard_data())


@app.route('/about')
async def about():
    update_db()
    return render_template('О-нас.html', stats=get_counter_stats())


if __name__ == '__main__':
    from db import update_db, get_leaderboard_data, get_counter_stats
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
