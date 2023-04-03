import os
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
import requests

basedir = os.path.abspath(os.path.dirname(__file__))

db = SQLAlchemy()

app = Flask(__name__)

#Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'network.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

key = "YOUR_GOOGLE_API_KEY"
klinik_list = []

#Cafe TABLE Configuration
class Klinik(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Namn = db.Column(db.String(250), unique=True, nullable=False)
    Adress = db.Column(db.String(500), nullable=False)
    Postnummer = db.Column(db.Integer, nullable=False)
    Stad = db.Column(db.String(500), nullable=False)
    Landskap = db.Column(db.String(250), nullable=False)
    Fysioterapeut = db.Column(db.Integer, nullable=False)
    Läkare = db.Column(db.Integer, nullable=False)
    Skicka_biljett_till_klinik = db.Column(db.Integer, nullable=False)
    Kommentar = db.Column(db.String(500), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    long = db.Column(db.Float, nullable=False)

    with app.app_context():
        db.create_all()



with app.app_context():
    kliniker = db.session.query(Klinik).all()

for klinik in kliniker:
    klinik_list.append({
        'name': klinik.Namn,
        'address': klinik.Adress,
        'stad': klinik.Stad,
        'ladscape': klinik.Landskap,
        'doctor': klinik.Läkare,
        'physio': klinik.Fysioterapeut,
        'send_ticket': klinik.Skicka_biljett_till_klinik,
        'comment': klinik.Kommentar,
        'lat': float(klinik.lat),
        'long': float(klinik.long)
    })

#If you dont have the lat and lng coordinates
def add_lat_long(kliniker, key):
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    for clinic in kliniker:
        address = clinic["address"] + ", " + clinic["stad"]
        params = {"address": address, "key": key}
        response = requests.get(base_url, params=params).json()
        try:
            location = response["results"][0]["geometry"]["location"]
            clinic["lat"] = location["lat"]
            clinic["long"] = location["lng"]
        except (IndexError, KeyError):
            # Handle error when address is not found
            clinic["lat"] = None
            clinic["long"] = None

        with app.app_context():
            aktuell_klinik = Klinik.query.filter_by(Namn=clinic["name"]).first()
            aktuell_klinik.lat = clinic["lat"]
            aktuell_klinik.long = clinic["long"]
            db.session.commit()
    return kliniker

#Comment out if you need lat lng coordinates added to db
kliniker_with_lat_long = klinik_list

#Uncomment if need to add lat long to database
#kliniker_with_lat_long = add_lat_long(klinik_list, key)

@app.route("/")
def home():
    return render_template("index.html", kliniker=kliniker_with_lat_long, person_adress="")


#When user submits adress of a person to add on the map as a marker, returns all clinics aswell as the person adress inkluding lat long position
@app.route("/add_adress")
def add_adress():
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    submitted_address = request.args.get("person-adress")
    person_adress = [{'adress': submitted_address, 'lat': '', 'long': ''}]
    params = {"address": submitted_address, "key": key}
    response = requests.get(base_url, params=params).json()
    try:
        location = response["results"][0]["geometry"]["location"]
        person_adress[0]["lat"] = location["lat"]
        person_adress[0]["long"] = location["lng"]
    except (IndexError, KeyError):
        # Handle error when address is not found
        person_adress[0]["lat"] = None
        person_adress[0]["long"] = None
        print("Adress not found")
    return render_template("person.html", kliniker=kliniker_with_lat_long, person_adress=person_adress)


if __name__ == '__main__':
    app.run(debug=True)
