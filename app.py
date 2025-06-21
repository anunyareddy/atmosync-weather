from flask import Flask, render_template, request, redirect, url_for
import requests
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
API_KEY = "d2b213888bc439e15cbeb1f97cbc771b"  # ✅ This is a working key

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%a'):
    return datetime.fromtimestamp(value).strftime(format)

def get_weather(lat, lon):
    try:
        # Current weather API
        current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        current_response = requests.get(current_url)
        current = current_response.json()

        # Forecast API (3-hour intervals for 5 days)
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        forecast_response = requests.get(forecast_url)
        forecast = forecast_response.json()

        # 🧠 Debugging Output
        print("Current Weather Response:", current)
        print("Forecast Response:", forecast)

        # Safety check
        if current.get("cod") != 200 or forecast.get("cod") != "200":
            return {"error": "Weather data not found. API key may be invalid or restricted."}

        # Parse current weather
        weather_data = {
            "temp": round(current["main"]["temp"]),
            "description": current["weather"][0]["description"].capitalize(),
            "humidity": current["main"]["humidity"],
            "wind": round(current["wind"]["speed"]),
            "icon": current["weather"][0]["icon"],
            "condition": current["weather"][0]["main"],
        }

        # Parse hourly forecast (next 5 x 3-hr blocks)
        hourly_data = []
        for hour in forecast["list"][:5]:
            temp = round(hour["main"]["temp"])
            precipitation = int(hour.get("pop", 0) * 100)
            wind = round(hour["wind"]["speed"])
            icon = hour["weather"][0]["icon"]
            dt = datetime.strptime(hour["dt_txt"], "%Y-%m-%d %H:%M:%S").timestamp()
            hourly_data.append([temp, precipitation, wind, icon, dt])

        # Daily aggregation from 3-hr forecast
        daily_buckets = defaultdict(list)
        for entry in forecast["list"]:
            date = entry["dt_txt"].split(" ")[0]
            daily_buckets[date].append(entry)

        daily_data = []
        for i, (day, entries) in enumerate(daily_buckets.items()):
            temps = [e["main"]["temp"] for e in entries]
            rain = sum([e.get("rain", {}).get("3h", 0) for e in entries])
            icon = entries[0]["weather"][0]["icon"]
            dt = datetime.strptime(day, "%Y-%m-%d").timestamp()
            daily_data.append([round(max(temps)), round(min(temps)), round(rain, 1), dt, icon])
            if len(daily_data) == 7:
                break

        weather_data["hourly"] = hourly_data
        weather_data["daily"] = daily_data
        return weather_data

    except Exception as e:
        return {"error": f"API failed: {str(e)}"}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/entry', methods=['GET', 'POST'])
def entry():
    if request.method == 'POST':
        lat = request.form['lat']
        lon = request.form['lon']
        date = request.form['date']
        time = request.form['time']
        return redirect(url_for('sub', lat=lat, lon=lon, date=date, time=time))
    return render_template('entry.html')

@app.route('/sub')
def sub():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    date = request.args.get('date')
    time = request.args.get('time')
    weather = get_weather(lat, lon)
    today = datetime.now().weekday()
    return render_template('sub.html', lat=lat, lon=lon, date=date, time=time, weather=weather, today=today)

if __name__ == '__main__':
    app.run(debug=True)
