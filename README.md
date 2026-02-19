# About The Project

This is a freiendly weather map app that renders weather information by city. It uses Langchain AI agents to wrap around openweather map app to render the information. It also has the option of using Genai Generative model to render friendly messages.

# Getting Started

**Prerequisites**

You need an api key from openweathermap, it's free unless you exceed the quota.

**Installation**

This app can be run be run in a container or locally, a requirements.txt file is included. If you run it in your dev environment make sure you activate your venv  virtual environment.

All that's needed is to clone this repository.

# Features

- Renders weather information by city, example: https://weather.sezwizz.xyz/weather/paris. 
- Caches the query for 30 minutes, refresh the query, you will notice the second response is jesonified, because it was retrived from redis.
- Limits each user to 30 queries per hour, 200 per day.
- Instrumented to render metrics for prometheus to scape, https://weather.sezwizz.xyz/metrics.
- Health checker, https://weather.sezwizz.xyz/health.
- Log collection via Loki, uses structured logging (key/value pairs) for better usability: formatter = jsonlogger.JsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')

========================================================================================

# prometheus.yml

**global:**

    scrape_interval: 15s
    scrape_timeout: 10s
    evaluation_interval: 15s

**scrape_configs:**

  Self-monitoring

    - job_name: 'prometheus'
      static_configs:
    - targets: ['localhost:9090']

  Application servers grouped by service

     - job_name: 'api-gateway'
      static_configs:
      - targets:
          - 'weather.sezwizz.xyz:8080'
        labels:
          service: 'weather-app'
          tier: 'frontend'

      - job_name: 'redis'
      static_configs:
      - targets:
          - 'redis-exporter-1:9121'
        labels:
          database: 'redis'

  Infrastructure monitoring
  
  - job_name: 'node'
    static_configs:
      - targets:
          - 'server1.prod.internal:9100'
          - 'server2.prod.internal:9100'
          - 'server3.prod.internal:9100'
          - 'server4.prod.internal:9100'
        labels:
          datacenter: 'us-east-1'
  
  **---------------------------------------------------------------------------------------------------**

# Alertmanager Routing

**route:**

    receiver: default
    group-by: [alertname, service]
    group-wait: 30s
    group-interval: 5m
    repeat-interval: 4h

**routes:**
    # Critical production alerts page immediately, warnings create tickets
    
    - match:
        severity: critical
        environment: production
      receiver: pagerduty
      continue: true

    # Also send to Slack for visibility
    - match:
        severity: critical
      receiver: slack-critical

    # Warnings create tickets
    - match:
        severity: warning
      receiver: ticketing-system
      group-wait: 10m

**receivers:**
  .
  - name: default
    slack-configs:
      - channel: '#alerts'
  - name: pagerduty
    pagerduty_configs:
      - service_key: 'your-pagerduty-key'
  - name: slack-critical
    slack-configs:
      - channel: '#incidents'
  - name: ticketing-system
    webhook_configs:
      - url: https://tickets.example.com/webhook
  .

      **--------------------------------------------------------------------------------------------------------------------**

# Observability

In the code we instrumented the app to create two metrics: a Counter that tracks the total number of HTTP requests
(with labels for method, endpoint, and status code), and a Histogram that measures request duration.
The /metrics endpoint returns all metrics in Prometheus format using the generate_latest() function.
The code measures how long it takes to process the request then records the duration in the histogram using the .observe() method
and increments the request counter using .inc(). The labels allow you to filter and aggregate metrics in your Prometheus queries.

`# Start timer

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
    REQUEST_COUNT.labels(method='GET', endpoint='/', status=503).inc()`

From above we're able to calculate Latency, Requests per Second (Rate), Error rates, and Irate:
# Endpoint Metric Definition
| Metric.       | Description                                                                   |
| ------------- | ----------------------------------------------------------------------------- |
|  Latency      |    The median 50th (P50) and 99th percentile (P99) round-trip latency times.  |    
|  Errors/Sec   |    The number of errors (4xx and 5xx) processed per second.                   |
|  Rate()       |    The number of requests processed per second.                               |
|  Irate()      |    Instantaneous per-second rate of change.                                   |

* rate() averages no. of request over the scraping period, giving a trend that helps plan capacity.
** irate() is burstable in nature and is instrumental in expaling what is happening in the moment.
