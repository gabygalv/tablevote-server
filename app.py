from flask import jsonify, make_response, request, session
from flask_restful import Resource

import requests
import random

from config import app, api, db, API_KEY
from models import User, Party, PartyUser, PartyVote

class Signup(Resource):
    def post(self):
        data = request.get_json()
        print(data)
        try:
            new_user = User(
                username = data['username'],
                phone=data['phone']
            )
            new_user.password_hash = data['password']
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            return make_response(new_user.to_dict(), 201)

        except:
            return make_response({'error': 'signup exception'}, 422)

class CheckSession(Resource):

    def get(self):
        user_id = session.get('user_id')
        
        if not user_id:
            return {'error': 'Unauthorized'}, 401
        
        current_user = User.query.filter(User.id == user_id).first()
        return current_user.to_dict(), 200

class Login(Resource):
    
    def post(self):
        data = request.get_json()
        check_user = User.query.filter(User.phone == data['phone']).first()
        if check_user and check_user.authenticate(data['password']):
            session['user_id'] = check_user.id

            return make_response(check_user.to_dict(), 200)
        return {'error': 'Unauthorized'}, 401
        
class Logout(Resource):

    def delete(self):
        
        if session.get('user_id'):
            session['user_id'] = None
            return {}, 204
        return {'error': '401 Unauthorized'}, 401

class Home(Resource):
    
    def get(self):
        return '<h1>TableVote is alive!<h1>'
    
class Users(Resource):
    def get(self):
        users = [item.to_dict() for item in User.query.all()]
        return make_response(users, 200)

class MissedConnections(Resource):
    def get(self, id):
        user = User.query.get(id)
        print(user)
        if not user:
            return {'error': 'User not found'}, 404

        party_votes = PartyVote.query.join(PartyUser).filter(PartyUser.user_id == id).all()
        print(party_votes)
        restaurant_ids = [pv.restaurant for pv in party_votes]
        print(restaurant_ids)
        return make_response(restaurant_ids, 200)
    
class UserParties(Resource):
    def get(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404

        parties = Party.query.join(Party.party_users).filter(
            (Party.creator_id == user.id) | (PartyUser.user_id == user.id)).all()
        user_parties = [item.to_dict(rules=('party_users.user.username',)) for item in parties]
        return make_response(user_parties, 200)
    
class PartiesRestaurant(Resource):
    def get(self, id):
        
        party_users = PartyUser.query.filter_by(party_id=id).all()
        print(party_users)

        if not all([pu.voted for pu in party_users]):
            return {'error': 'not all users have voted'}, 404

        vote_counts = {}
        print(vote_counts)
        for party_user in party_users:
            party_vote = PartyVote.query.filter_by(partyuser_id=party_user.id).first()
            if not party_vote:
                return {'error': f'no vote found for user {party_user.id}'}, 404
            restaurant = party_vote.restaurant
            vote_counts[restaurant] = vote_counts.get(restaurant, 0) + 1

        print(vote_counts)
        if not vote_counts:
            return {'error': 'no votes found'}, 404

        max_count = max(vote_counts.values())
        candidates = [k for k, v in vote_counts.items() if v == max_count]

        if len(candidates) == 1:
            return candidates[0]
        else:
            return random.choice(candidates)
     
class PartiesById(Resource):
    def patch(self, id):
        data = request.get_json()
        to_update = Party.query.filter_by(id=id).first()
        if to_update:
            for attr in data:
                setattr(to_update, attr, data[attr])
            db.session.add(to_update)
            db.session.commit()
            return make_response(to_update.to_dict(), 200)
        else:
            return {'error': 'Party not found'}, 401
    def delete(self, id):
        to_delete = Party.query.filter(Party.id==id).first()
        db.session.delete(to_delete)
        db.session.commit()
        
        return make_response({'message': 'party successfully deleted!'}, 204)
    def get(self, id):
        party = Party.query.filter(Party.id==id).first()
        return make_response(party.to_dict(), 200)

class Parties(Resource):
    def get(self):
        parties = [item.to_dict() for item in Party.query.all()]
        return make_response(parties, 200)
    
    def post(self):
        if session.get('user_id'):
            data = request.get_json()

            new_party = Party(
                creator_id = data['creator_id'],
                location = data['location'],
                term = data['term'],
                radius = data['radius'],
                price = data['price']
                )
            db.session.add(new_party)
            db.session.commit()

            return make_response(new_party.to_dict(), 201)
        return {'error': 'Unauthorized'}, 401

class PartyUsers(Resource):
    def get(self):
        party_id = request.args.get('partyId', type=int) 
        party_users = PartyUser.query.filter_by(party_id=party_id).all() 
        print(party_users)
        return jsonify([party_users])
        
    def post(self):
        if session.get('user_id'):
            data = request.get_json()
        
            party_id = data.get('party_id')
            usernames = data.get('usernames')
            
            users = User.query.filter(User.username.in_(usernames)).all()
            for user in users:
                partuser = PartyUser(
                    party_id=party_id,
                    user_id=user.id
                )
                db.session.add(partuser)
            db.session.commit()
            return make_response({'message': 'PartyUsers added'}, 201)
        return make_response({'message': 'Unauthorized'}, 401)
    
class PartyUsersByID(Resource):
     def patch(self, party_id, user_id):
        data = request.get_json()
        to_update = PartyUser.query.filter_by(party_id=party_id, user_id=user_id).first()
        if to_update:
            to_update.voted = data['voted']
            db.session.commit()
            return make_response({'message': 'PartyUser updated successfully'}, 200)
        else:
            return {'error': 'PartyUser not found'}, 401

class PartyVotes(Resource):
    def get(self):
        party_votes = [item.to_dict() for item in PartyVote.query.all()]
        return make_response(party_votes, 200)
    def post(self):
        if session.get('user_id'):
            data = request.get_json()
            print(data)
            newVote = PartyVote(
                partyuser_id=data['partyuser_id'],
                restaurant=data['restaurant'],
                voted=data['voted']
            )
            db.session.add(newVote)
            db.session.commit()
            return make_response(newVote.to_dict(), 201)
        return make_response({'message': 'Unauthorized'}, 401)

class YelpSearch(Resource):
    def get(self, ):
        location = request.args.get('location')
        term = request.args.get('term')
        radius = request.args.get('radius')
        price = request.args.get('price')
        sort = 'best_match'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {API_KEY}',
        }

        params = {
            'location': location,
            'term': term,
            'radius': radius,
            'price': price,
            'sort_by': sort,
            'limit': 20
        }
        response = requests.get('https://api.yelp.com/v3/businesses/search?', headers=headers, params=params)

        return response.json()

class YelpSearchById(Resource):
    def get(self,id ):

        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json',
        }

        response = requests.get(f'https://api.yelp.com/v3/businesses/{id}', headers=headers)

        return response.json()
    
api.add_resource(Home, '/')
api.add_resource(Users, '/users')
api.add_resource(MissedConnections, '/users/<int:id>/missed')
api.add_resource(UserParties, '/users/<int:user_id>/parties')
api.add_resource(Parties, '/parties')
api.add_resource(PartiesById, '/parties/<string:id>')
api.add_resource(PartiesRestaurant, '/partiesrestaurant/<string:id>')
api.add_resource(PartyUsers, '/partyusers')
api.add_resource(PartyUsersByID, '/partyusers/<string:party_id>/<int:user_id>')
api.add_resource(PartyVotes, '/partyvotes')
api.add_resource(YelpSearch, '/yelpsearch')
api.add_resource(YelpSearchById, '/yelpsearchbyid/<string:id>')
api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')

if __name__ == '__main__':
    app.run(port=5555, debug=True)