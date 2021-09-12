###romespapa chess club web-site

> :warning: The design and frontend of the application is still in development

It is the deploy repo of the online chess club [web-site](https://rccapp.herokuapp.com/). It is hosted on Heroku and use
PostgreSQL DB. 

#### Before you start
* [Flask](https://flask.palletsprojects.com/en/2.0.x/)
* [SQLalchemy](https://docs.sqlalchemy.org/en/14/)
* [Heroku](https://devcenter.heroku.com/articles/getting-started-with-python)
* [Pandas](https://pandas.pydata.org/docs/)
* [Lichess API](https://lichess.org/api)

#### Description
The main feature of the web-site is an opportunity to see the leaderboard. All club activity data is parsed from lichess
api and collected in the db. Also, in addition to the result of the participant, it is recorded in the db
how many league points he received, depending on the rank:

| rank | points |
|------|--------|
| 1    | 10     |
| 2    | 7      |
| 3    | 5      |
| 4    | 3      |
| 5    | 1      |
| 5<   | 0      |

Every time someone visits the site, the function checks if there are any new swiss and 
adds new ones to db if there are:

```buildoutcfg
def update_db():
    """
    Update db data by comparing with lichess data
    :return:
    """
    swiss_as_list_of_string = requests.get('https://lichess.org/api/team/romes-papa-club/swiss').text.split('\n')
    swiss_as_list_of_json = [json.loads(i) for i in swiss_as_list_of_string[:-1]]

    swiss_ids = set([i['id'] for i in swiss_as_list_of_json])
    db_swiss_ids = set([i.lichess_id for i in list(db.session.query(Swiss).all())])

    db_users = set(User.query.all())
    swiss_users = set()

    for new_swiss in swiss_ids - db_swiss_ids:
        db.session.add(Swiss(
            lichess_id=new_swiss['id'],
            name=new_swiss['name'],
            start_at=datetime.datetime.strptime(new_swiss['startsAt'][:10], "%Y-%m-%d").date(),
            time_limit=new_swiss['clock']['limit'],
            increment=new_swiss['clock']['increment'],
            number_of_rounds=new_swiss['nbRounds'],
            number_of_players=new_swiss['nbPlayers']
        ))

        entries_as_list_of_string = requests.get(f'https://lichess.org/api/swiss/{new_swiss["id"]}/results').text.split(
            '\n')
        for entry_as_json in [json.loads(i) for i in entries_as_list_of_string[:-1]]:
            swiss_users.add(entry_as_json['username'])

            db.session.add(Entry(
                points=entry_as_json['points'],
                rank=entry_as_json['rank'],
                league_points=calculate_league_points(entry_as_json['rank']),
                swiss_lichess_id=new_swiss['id'],
                username=entry_as_json['username']
            ))

    for new_username in swiss_users - db_users:
        db.session.add(User(
            name=new_username
        ))

    db.session.commit()
    return
```

All information about the results of the players is aggregated and sorted by pandas:

```buildoutcfg
def get_leaderboard_data():
    """
    Return aggregated and sorted leaderbord from db
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
```
