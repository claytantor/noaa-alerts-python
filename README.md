# noaa-alerts-python
send noaa hydrometer alerts to the slack channel

## installing stuff
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

