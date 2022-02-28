from flask import Flask, render_template
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import os
import requests
import certifi

load_dotenv()
ca = certifi.where()

def create_app():
    app = Flask(__name__)
    db = MongoClient(os.environ.get("MONGO_URI"), tlsCAFile=ca)
    app.db = db.weatherapp

    forecastTurku(app)

    @app.route("/")
    def home():
        return render_template("home.html")
    
    
    return app

def forecastTurku(app):
    API_KEY = os.environ.get("API_KEY")

    #Forms the API call url for openweathermap's Geocoding API
    location_base_url = "http://api.openweathermap.org/geo/1.0/direct"
    location = "Turku"
    country_code = "FI"
    location_request_url = f"{location_base_url}?q={location},{country_code}&appid={API_KEY}"
    location_response = requests.get(location_request_url)

    #Gets the latitude and longitude of the location if the request is ok
    if location_response.status_code == 200:
            location_data = location_response.json()
            location_lat = location_data[0]["lat"]
            location_lon = location_data[0]["lon"]

    else:
        print("error")

    #Forms the url for weather API call
    weather_base_url = "http://api.openweathermap.org/data/2.5/forecast"
    lat = location_lat
    lon = location_lon
    weather_request_url = f"{weather_base_url}?lat={lat}&lon={lon}&units=metric&appid={API_KEY}"
    weather_response = requests.get(weather_request_url)
    weather_data = weather_response.json()

    #Gets the weather data, goes through it and inserts the data into a weatherapp.{city name} collection
    if weather_response.status_code == 200:
            weather_data = weather_response.json()
            city = weather_data["city"]["name"]
            for n in weather_data["list"]:
                try:
                    id = n["dt"]
                    del n["dt"]
                    app.db.weatherapp["{}".format(city)].insert_one({"_id": id, "data": n})

                except DuplicateKeyError:
                    continue

    else:
        print("error")

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)