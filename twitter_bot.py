import sys
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, task
from twisted.python import log

import simplejson, urllib

class TwitterBot(irc.IRCClient):
    got_Pong = True
    nickname = 'MLGSC2Scores'
    password = 'kD3pbGTiPg'
    last_tweet_id ='0'

    def signedOn(self):
        for chan in self.factory.channel:
            log.msg('Joining channel ' + chan)
            self.join(chan)

        self.lc = task.LoopingCall(self.update_twitter)
        self.lc.start(24, False)

    def update_twitter(self):
        rate_limit_status=get_rate_status()
        
        if int(rate_limit_status['remaining_hits']) > 1:
            last_tweet = get_last_tweet('mlgsc2scores')

            if long(self.last_tweet_id) < long(last_tweet['id']):
                log.msg('Latest tweet: ' + last_tweet['text'])
                    
                self.last_tweet_id = last_tweet['id']
                for channel in channels:
                    self.say(channel, last_tweet['text'])
        else:
            log.msg('Rate limit reached!')
            self.msg('OTSTomcat','Rate limit reached!')

class TwitterBotFactory(protocol.ClientFactory):
    protocol = TwitterBot

    def __init__(self, channels):
        self.channel = channels
    
    def clientConnectionLost(self, connector, reason):
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed: ", reason
        reactor.stop()

def get_last_tweet(user):
    url = "https://twitter.com/statuses/user_timeline.json?id=" + user
    result = simplejson.load(urllib.urlopen(url))
    
    return result[0]

def get_rate_status():
    url = "http://api.twitter.com/1/account/rate_limit_status.json"
    result = simplejson.load(urllib.urlopen(url))

    return result
if __name__ == '__main__':

    log.startLogging(sys.stdout)

    channels = ['day9tv', 'mlg', 'starcraft2.no']
    f = TwitterBotFactory(channels)

    log.msg('Connecting...')
    reactor.connectTCP("irc.quakenet.org", 6667, f)
    reactor.run()