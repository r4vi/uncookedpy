from flask import Flask
from flask import request
import requests, json
from fsa import get_match
from rq import Connection, Queue
from db import User, db_session
from settings import clientid, secret, push_secret, API_VERSION, REPLY_URL, AUTHENTICATE_URL, AUTHORIZE_URL, SELF_URL

app = Flask(__name__)


def get_token(foursquare_id):
    u = User.query.filter(User.foursquare_id == foursquare_id).first()
    if u:
        return u.access_token
    else:
        raise ValueError('user not registered')

def reply(checkin_id, lat, lng, foursquare_id, name=None):
    url = REPLY_URL.format(checkin_id=checkin_id)
    match = get_match(lat, lng, name=name)
    if match:
        text = "{name} has a hygene rating of {rating} as of {date}".format(**match)
        payload={'CHECKIN_ID': checkin_id,
                'text': text[:200],
                'oauth_token': get_token(foursquare_id),
                'v': API_VERSION}
        resp = requests.post(url, data=payload)

@app.route('/')
def index():
    return '<a href="{AUTHENTICATE_URL}">go go go</a>'.format(AUTHENTICATE_URL=AUTHENTICATE_URL)

@app.route('/checkin', methods=['GET','POST'])
def checkin():    
    if request.form['secret'] == push_secret:
        parsed_checkin = json.loads(request.form['checkin'])
        checkin_id = parsed_checkin.get('id')
        # only reply if the venue is new
        venue = parsed_checkin.get('venue')
        foursquare_id = parsed_checkin.get('user',{}).get('id')
        if venue and venue.get('beenHere',{}).get('count',-1) == 0:
            name = venue.get('name')
            lat = venue.get('location',{}).get('lat')
            lng = venue.get('location',{}).get('lng')
            if all(map(bool,[name,lat,lng, foursquare_id])):
                try:
                    reply(checkin_id, lat, lng, foursquare_id, name)
                except:
                    pass
    return 'OK'

@app.route('/callback', methods=['GET','POST'])
def callback():
    code=request.args.get('code')
    if not code:
        return 'failed'
    url = AUTHORIZE_URL.format(code=code, 
        client_id=clientid,
        secret=secret)
    resp = requests.get(url)
    if resp.ok:
        access_token = resp.json()['access_token']
        # now get 4sq id and name from self endpoint
        payload = {'oauth_token': access_token,
                   'v': API_VERSION}
        resp2 = requests.get(SELF_URL, params=payload)
        if resp2.ok:
            user_w = resp2.json()
            user = user_w.get('response',{}).get('user',{})
            if user:
                name = user.get('firstName') + ' ' + user.get('lastName','')
                foursquare_id = user.get('id')
                u = User.query.filter(User.foursquare_id == foursquare_id).first()
                if u:
                    u.access_token = access_token
                    db_session.commit()
                else:
                    u = User(foursquare_id, access_token, name)
                    db_session.add(u)
                    db_session.commit()

                return 'callback ok (POST)'
    else:
        return 'something went wrong...'

@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()


if __name__ == '__main__':
    app.run(debug=True, port=3000)
