from datetime import datetime
from config import db, app
from models import User, Party, PartyUser, PartyVote

with app.app_context():

    print('deleting')
    PartyVote.query.delete()
    PartyUser.query.delete()
    Party.query.delete()
    User.query.delete()
    print('deleted')


    # create users
    print('..')
    user1 = User(username='gaby', phone='6024595353', password_hash='password')
    user2 = User(username='krista', phone='520555555', password_hash='password')
    user3 = User(username='val', phone='6026666666', password_hash='password')
    user4 = User(username='coco', phone='9288888888', password_hash='password')
    user5 = User(username='dolly', phone='6233333333', password_hash='password')
    print('adding')
    db.session.add_all([user1, user2, user3, user4, user5])
    db.session.commit()
    print('users committed!')


    # create parties
    print('..')
    party1 = Party(creator_id=user1.id, created_at=datetime.now(), location='tucson', radius='8045.0', term='Pizza', price='1')
    party2 = Party(creator_id=user2.id, created_at=datetime.now(), location='phoenix', radius='8045.0', term='Pizza', price='2')
    print('adding')
    db.session.add_all([party1, party2])
    db.session.commit()
    print('party committed!')


    # create party users
    print('..')
    partyuser1 = PartyUser(user_id=user1.id, party_id=party1.id, voted=False, updated_at=datetime.now())
    partyuser2 = PartyUser(user_id=user2.id, party_id=party2.id, voted=False, updated_at=datetime.now())
    print('adding')
    db.session.add_all([partyuser1, partyuser2])
    db.session.commit()
    print('partyusers committed!')

    
    #