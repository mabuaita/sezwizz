========================================================================================

# Alertmanager Routing

route:
  receiver: default
  group-by: [alertname, service]
  group-wait: 30s
  group-interval: 5m
  repeat-interval: 4h
  routes:
    # Critical production alerts page immediately
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

receivers:
  - name: default
    slack-configs:
      - channel: '#alerts'

  - name: pagerduty
    pagerduty-configs:
      - service-key: 'your-pagerduty-key'

  - name: slack-critical
    slack-configs:
      - channel: '#incidents'

  - name: ticketing-system
    webhook-configs:
      - url: 'https://tickets.example.com/webhook'

============================================================================================
