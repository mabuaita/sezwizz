import os
import logging
from pythonjsonlogger import jsonlogger
import requests
from dotenv import load_dotenv
from langchain_community.utilities import OpenWeatherMapAPIWrapper
import google.genai as genai
from google.genai import types
import redis, json
from flask import Flask, jsonify
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter, Histogram, generate_latest
import time

redis_client = redis.StrictRedis(host='redis.sezwizz.xyz', port=6379, decode_responses=True)

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency in seconds', ['method', 'endpoint'])


def check_cache(key):
    cached_data = redis_client.get(key)
    if cached_data:
        return jsonify(cached_data)
    return (cached_data == False)

def update_cache(key, data):
    redis_client.set(key, json.dumps(data), ex=1800)

def check_api_keys():
    """ Check if necessary API keys are available in Streamlit secrets. """
    required_keys = ['GEMINI_API_KEY', 'OPENWEATHERMAP_API_KEY']
    missing_keys = [key for key in required_keys if key is None]
    if missing_keys:
        print(f'Missing API keys in secrets configuration: {", ".join(missing_keys)}')
    
def weather_agent(city, OPENWEATHERMAP_API_KEY):
# AI-Ready Wrapper (LangChain)
    OPENWEATHERMAP_API_KEY = os.environ["OPENWEATHERMAP_API_KEY"]
    print(OPENWEATHERMAP_API_KEY)
    weather = OpenWeatherMapAPIWrapper()
    data = weather.run(city)
    return data

def get_gemini_summary(weather_data_str, GEMINI_API_KEY, api_key):
    if not GEMINI_API_KEY:
        #app.logger.warning("GEMINI_API_KEY not set. Skipping summary.")
        return "AI summary feature disabled: Gemini API key not set."
    
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)

        genai.Client(api_key=GEMINI_API_KEY)
        #model = genai.GenerativeModel(model_name='gemini-1.5-flash-8B')
        # Craft a good prompt!
        content = (
            f"You are a friendly weather assistant. Based on this weather data string: "
            f"'{weather_data_str}', provide a short, engaging weather summary "
            f"(1-2 sentences) for the general public. Include one small, actionable "
            f"tip for the day (e.g., 'Don't forget your umbrella!' or 'Perfect day for a walk!')."
        )
        response = client.models.generate_content(model='gemini-2.0-flash',contents=content,config=types.GenerateContentConfig(
    tools=[{'code_execution': {}}] ))
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        #app.logger.error(f"Error with Gemini API: {e}")
        # Check for specific Gemini API errors if the SDK provides them
        # For example, if e has a 'message' attribute:
        return f"AI summary currently unavailable. Error: {getattr(e, 'message', str(e))}"
    
def cityweather(city):
    """get api leys from environ variables, these variables should be updated via queries to secret stores"""
    # Load environment variables from .env file
    load_dotenv()
    # Access environment variables as if they came from the actual environment
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GOOGLE_API_KEY = os.getenv('GEMINI_API_KEY')
    OPENWEATHERMAP_API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')

    check_api_keys()

    cached_data = check_cache(key=city)
    if cached_data:
        return cached_data
    weather_data_str = weather_agent(city, OPENWEATHERMAP_API_KEY)
    update_cache(key=city, data=weather_data_str)

    #response = get_gemini_summary(weather_data_str, GEMINI_API_KEY, api_key=GOOGLE_API_KEY)
    return weather_data_str

app = Flask(__name__)
metrics = PrometheusMetrics(app)

@app.route('/metrics')
def metrics():
    return generate_latest()

# Configure the logger
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
handler.setFormatter(formatter)

# Clear default handlers and add the new one
app.logger.handlers = []
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

@app.route("/")
def help():

    # Log key-value pairs by passing a dictionary
    app.logger.info({"message": "Request received", "method": "GET", "path": "/"})

    return "Please include '/weather/<city>' parameter....such as https://weather.sezwizz.xyz/weather/london"

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/weather', defaults={'city': None})
# for furture enhancement, we should introduce a geo-locator app to use current city by default

@app.route('/weather/<city>')

def weather_endpoint(city):

    # Log key-value pairs by passing a dictionary
    app.logger.info({"message": "Request received", "method": "GET", "path": "/"})


    # In this endpoint we create two metrics: a Counter that tracks the total number of HTTP requests
    # (with labels for method, endpoint, and status code), and a Histogram that measures request duration.

    # The /metrics endpoint returns all metrics in Prometheus format using the generate_latest() function. 
    # In the home route handler, the code measures how long it takes to process the request then records 
    # that duration in the histogram using the .observe() method and increments the request counter using
    # .inc(). The labels allow you to filter and aggregate metrics in your Prometheus queries.

    # This simple instrumentation captures request counts and latencies, giving visibility into the service's
    # performance.

# Start timer
    start_time = time.time()
    if not city:
        return jsonify({'error': 'City parameter is required'}), 400
    response = cityweather(city)

    duration = time.time() - start_time
    REQUEST_LATENCY.labels(method='GET', endpoint='/').observe(duration)
    REQUEST_COUNT.labels(method='GET', endpoint='/', status=200).inc()
    REQUEST_COUNT.labels(method='GET', endpoint='/', status=400).inc()
    REQUEST_COUNT.labels(method='GET', endpoint='/', status=404).inc()
    REQUEST_COUNT.labels(method='GET', endpoint='/', status=500).inc()
    REQUEST_COUNT.labels(method='GET', endpoint='/', status=503).inc()

    
    return response

if __name__ == "__main__":
#    metrics = PrometheusMetrics(app)
    app.run(debug=False, host='0.0.0.0', port=3777)
