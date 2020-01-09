# noaa-alerts-python
send noaa hydrometer alerts to a slack channel or to a FlashLex device.

# what does thos project do?
This repo is intended to provide a simple early warning system for flooding by leveraging the NOAA hydrometer gauges alerts RSS feeds. We are impress and thankful that the NOAA agency exists and provides such free services to help people and property safety.

# installing stuff
```
python3 -m venv ./venv
source venv/bin/activate
$(pwd)/venv/bin/python3 -m pip install --upgrade pip
$(pwd)/venv/bin/python3 -m pip install -r requirements.txt
```

# running from command line
`$(pwd)/venv/bin/python -u $(pwd)/app.py --config $(pwd)/config.yml`

# creating the systemd service
```
$(pwd)/venv/bin/python3 makeservice.py -d $(pwd) -t noaaalerts.service.mustache > noaaalerts.service
```

Instructions for setting up your service can be found at https://www.raspberrypi-spy.co.uk/2015/10/how-to-autorun-a-python-script-on-boot-using-systemd/

```
sudo cp noaaalerts.service /lib/systemd/system/noaaalerts.service
sudo chmod 644 /lib/systemd/system/noaaalerts.service
sudo systemctl daemon-reload
sudo systemctl enable noaaalerts.service
```

# sending alerts to slack
If you would like to set a threshold for alerting via slack you can easily use the [Slack Webhook API](https://api.slack.com/messaging/webhooks). You will need to supply the incoming URL to alert based on the forecasted threshold. 

```yaml
noaa-alerts:
  sources:
    - guage-id: 'vwbc1'
      name: 'VWBC1 - Sacramento River at Vina-Woodson Bridge (California)'
      source-type: rss
      path: 'https://water.weather.gov/ahps2/rss/alert/vwbc1.rss'
      schedule:
        rate: 'minutes'
        value: 2
      trigger:
          match: 'Highest Projected Forecast Available'
          minor: 180.0
          moderate: 189.5
          major: 190.0
      notifications:
        # curl -X POST -H 'Content-type: application/json' --data '{"text":"Hello, World!"}' https://hooks.slack.com/services/TDAR6YHA/ARPLKLD9R/fFgHkOSooperSecretSBye56YsSL4L
        - name: 'VWBC1 - Sacramento River at Vina-Woodson Bridge'
          type: 'SlackWebhook'
          content:
            - '*VWBC1 - Sacramento River at Vina-Woodson Bridge Above Threshold 180 ft*'
            - 'https://water.weather.gov/ahps2/hydrograph.php?gage=vwbc1&wfo=sto'
          path: 'https://hooks.slack.com/services/TDAR6YHA/ARPLKLD9R/fFgHkOSooperSecretSBye56YsSL4L'
```
# sending alerts to FlashLex
Imagine you want to sound an alarm to warn people that a flood is predicted. You could easily create an IOT device to flash lighs, send emails or turn on a siren using [FlashLex](https://flashlex.com).

Feel free to investigate more information on how to [start developing your own apps using FlashLex](http://docs.flashlex.com.s3-website-us-east-1.amazonaws.com/flashlex-docs/v1.5/index.html)

```yaml
noaa-alerts:
  sources:
    - guage-id: 'syco3'
      name: 'SYCO3 - Johnson Creek near Sycamore (Oregon) - FlashLex'
      source-type: rss
      path: 'https://water.weather.gov/ahps2/rss/alert/syco3.rss'
      schedule:
        rate: 'minutes'
        value: 8
      trigger:
          match: 'Highest Projected Forecast Available'
          minor: 5.0 
          moderate: 10.3 
          major: 10.3 
      notifications:
        - name: 'SYCO3 Johnson Creek at Sycamore'
          type: 'FlashLex'
          baseUrl: 'https://api.flashlex.com/dev'
          thingId: '48338542-9866-1046-9ecc-ad74e1807cc5'
          headers:
            Authorization: "Basic SooperSecr3t"
```

