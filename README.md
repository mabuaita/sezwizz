# Alertmanager Routing

route:
  receiver: default
  group_by: [alertname, service]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
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
      group_wait: 10m

receivers:
  - name: default
    slack_configs:
      - channel: '#alerts'

  - name: pagerduty
    pagerduty_configs:
      - service_key: 'your-pagerduty-key'

  - name: slack-critical
    slack_configs:
      - channel: '#incidents'

  - name: ticketing-system
    webhook_configs:
      - url: 'https://tickets.example.com/webhook'


[Learn more about creating GitLab projects.](https://docs.gitlab.com/ee/gitlab-basics/create-project.html)
