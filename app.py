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

from lxml import html
from os.path import dirname, abspath

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')

LOGGER = logging.getLogger(__name__)

class SlackWebhookNotification:
    def __init__(self, source, notification, lines):
        self.source = source
        self.lines = lines
        self.notification = notification

    @staticmethod    
    def matches(notification):
        return (re.search("^SlackWebhook", notification['type']) != None)
    
    def notify(self):
        """
        # curl -X POST -H 'Content-type: application/json' --data '{"text":"Hello, World!"}' https://hooks.slack.com/services/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
        """

        self.notification['content'].extend(self.lines)
        #notityLines = self.notification['content'].extend(self.lines) 
        #print('\n'.join(self.notification['content']))
        
        response = requests.post(self.notification['path'], data=json.dumps({'mrkdwn': True, 'text':'\n'.join(self.notification['content'])}), headers={'Content-type':'application/json'})
        print('NOTIFY SlackWebhook!', self.notification['path'], response)


class FlashLexNotification:
    def __init__(self, source, notification, lines):
        self.source = source
        self.lines = lines
        self.notification = notification
    
    @staticmethod    
    def matches(notification):
        return (re.search("^FlashLex", notification['type']) != None)

    @classmethod
    def notify(self):
        pass


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
    print(source['trigger'])
    #filter the criteria
    for line in lines:
        x = re.search("^{0}".format(source['trigger']['match']), line)
        if(x):
            #print(line, x)
            parts = line.split()
            
            if(len(parts)==6):
                height = float(parts[4])
                if height>=source['trigger']['minor']:
                    print('ALERTING level above minimum threshold:{0}'.format(source['trigger']['minor']))
                    return True

                else:
                    print('Forcasted level {0} ft is below minor threshold {1} ft'.format(height, source['trigger']['minor']))
    return False

def makeNotifier(notification, source, lines):
    if(SlackWebhookNotification.matches(notification)):
        return SlackWebhookNotification(source, notification, lines)
    else:
        return None

def notifySource(source, lines):
    for notification in source['notifications']:
        notifier = makeNotifier(notification, source, lines)
        if(makeNotifier != None):
            notifier.notify()
        
def parseSource(source):
    d = None
    if(source['source-type'] == 'rss'):
        d = feedparser.parse(source['path'])    
    
    if(d != None):
        for entry in d['entries']:
            forecastLines = getForecastLines(entry['summary'])
            if linesIsTriggered(source, forecastLines):
                notifySource(source, forecastLines)

def main(argv):
    print("starting noaa-alerts app.")

    # Read in command-line parameters
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config", action="store", 
        required=True, dest="config", help="the YAML configuration file")

    args = parser.parse_args()
    config = loadConfig(args.config)['noaa-alerts']

    for source in config['sources']:
        
        if(source['schedule']['rate'] == 'day'):
            schedule.every().day.at(source['schedule']['value']).do(parseSource, source=source )
        if(source['schedule']['rate'] == 'hours'):
            schedule.every(source['schedule']['value']).hours.do(parseSource, source=source )
        if(source['schedule']['rate'] == 'minutes'):
            print(source['schedule'])
            schedule.every(source['schedule']['value']).minutes.do(parseSource, source=source )

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main(sys.argv[1:])