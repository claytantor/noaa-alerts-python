import logging
import argparse
import yaml
import sys, os
import feedparser
import requests
import json
import re
import schedule
import time
import requests

from lxml import html
from os.path import dirname, abspath

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')

LOGGER = logging.getLogger(__name__)

class SlackWebhookNotification:
    def __init__(self, source, notification, lines, isTriggeredResponse):
        self.source = source
        self.lines = lines
        self.notification = notification
        self.isTriggeredResponse = isTriggeredResponse

    @staticmethod    
    def matches(notification):
        return (re.search("^SlackWebhook", notification['type']) != None)
    
    def notify(self):
        """
        # curl -X POST -H 'Content-type: application/json' --data '{"text":"Hello, World!"}' https://hooks.slack.com/services/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
        """
        self.notification['content'].extend(self.lines)
        
        response = requests.post(self.notification['path'], data=json.dumps({'mrkdwn': True, 'text':'\n'.join(self.notification['content'])}), headers={'Content-type':'application/json'})
        print('NOTIFY SlackWebhook!', self.notification['path'], response)


class FlashLexNotification:
    def __init__(self, source, notification, lines, isTriggeredResponse):
        self.source = source
        self.lines = lines
        self.notification = notification
        self.isTriggeredResponse = isTriggeredResponse

    
    @staticmethod    
    def matches(notification):
        return (re.search("^FlashLex", notification['type']) != None)

    def notify(self):
        
        authResponse = requests.request("GET", '{0}/v1/token'.format(self.notification['baseUrl']), headers=self.notification['headers'])
        if(authResponse.status_code==200):
            authModel = json.loads(authResponse.text)
            # print("access token",authModel['accessToken'])

            url = '{0}/v1/things/{1}/publish'.format(self.notification['baseUrl'], self.notification['thingId'])

            messageModel = {
                "body": "{notificationName}|{actual}".format(notificationName=self.notification['name'], actual=self.isTriggeredResponse['actual']), 
                "color": "#42f584", 
                "type": "metric", 
                "behavior": "number", 
                "font": "md-1",
                "elapsed": 20.0 }

            headers = {
                'Content-Type': "application/json",
                'Authorization': "Bearer {0}".format(authModel['accessToken'])
            }

            response = requests.request("POST", url, data=json.dumps(messageModel), headers=headers)

            if(response.status_code>299):
                print("Error sending message to thing.", response.status_code, response.text)
            else:
                print("Notifying FlashLex", messageModel)


        else:
            print(authResponse)
        

def loadConfig(configFile):
    cfg = None
    with open(configFile, 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    return cfg

def getForecastLines(elementString):
    tree = html.fromstring(elementString.replace('\n',''))
    forcasts = tree.xpath('//div/text()')
    return forcasts

def linesIsTriggered(source, lines):
    # print(source['trigger'])
    #filter the criteria

    for line in lines:
        x = re.search("^{0}".format(source['trigger']['match']), line)
        if(x):
            parts = line.split()
            
            if(len(parts)==6):
                height = float(parts[4])
                if height>=source['trigger']['minor']:
                    print('ALERTING level above minimum threshold:{0}'.format(source['trigger']['minor']))
                    return {
                        'name': source['name'],
                        'match': source['trigger']['match'],
                        'isTriggered':True,
                        'threshold':source['trigger']['minor'],
                        'actual':height
                    }

                else:
                    print('Forcasted level {0} ft is below minor threshold {1} ft'.format(height, source['trigger']['minor']))
    return {
        'isTriggered':False
    }

def makeNotifier(notification, source, lines, isTriggeredResponse):
    if(SlackWebhookNotification.matches(notification)):
        return SlackWebhookNotification(source, notification, lines, isTriggeredResponse)
    elif(FlashLexNotification.matches(notification)):
        return FlashLexNotification(source, notification, lines, isTriggeredResponse)
    else:
        return None

def notifySource(source, lines, isTriggeredResponse):
    for notification in source['notifications']:
        notifier = makeNotifier(notification, source, lines, isTriggeredResponse)
        # print("notifySource", type(notifier))
        if(makeNotifier != None):
            notifier.notify()
        
def parseSource(source):
    d = None
    if(source['source-type'] == 'rss'):
        d = feedparser.parse(source['path'])    
    
    if(d != None):
        for entry in d['entries']:
            forecastLines = getForecastLines(entry['summary'])
            isTriggeredResponse = linesIsTriggered(source, forecastLines)
            if isTriggeredResponse['isTriggered']:
                notifySource(source, forecastLines, isTriggeredResponse)

def main(argv):
    print("starting noaa-alerts app.")

    # Read in command-line parameters
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config", action="store", 
        required=True, dest="config", help="the YAML configuration file")

    args = parser.parse_args()
    config = loadConfig(args.config)['noaa-alerts']

    for source in config['sources']:
        print(source['name'], source['schedule']) 
        if(source['schedule']['rate'] == 'day'):
            schedule.every().day.at(source['schedule']['value']).do(parseSource, source=source )
        if(source['schedule']['rate'] == 'hours'):
            schedule.every(source['schedule']['value']).hours.do(parseSource, source=source )
        if(source['schedule']['rate'] == 'minutes'):
            schedule.every(source['schedule']['value']).minutes.do(parseSource, source=source )

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main(sys.argv[1:])
