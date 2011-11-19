from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, task

import time, sys, simplejson, urllib

class TwitterBot(irc.IRCClient):
    got_Pong = True
    nickname = 'MLGSC2Scores'
    last_tweet_id ='0'

    def signedOn(self):
        self.join(self.factory.channel)
        self.join('mlg')

        self.lc = task.LoopingCall(self.update_twitter)
        self.lc.start(24, False)
        
    def privmsg(self, user, channel, msg):
        user = user.split('!', 1)[0]

    def update_twitter(self):
        rate_limit_status=get_rate_status()
        
        if(int(rate_limit_status['remaining_hits']) > 1):
            last_tweet = get_last_tweet('mlgsc2scores')

            if(long(self.last_tweet_id) < long(last_tweet['id'])):        
                self.last_tweet_id = last_tweet['id']
                self.say('day9tv', last_tweet['text'], length=None)
                self.say('mlg', last_tweet['text'], length=None)
        else:
            self.msg('OTSTomcat','Rate limit reached!')

class TwitterBotFactory(protocol.ClientFactory):
    protocol = TwitterBot

    def __init__(self, channel):
        self.channel = channel
    
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

    f = TwitterBotFactory('day9tv')
    reactor.connectTCP("irc.quakenet.org", 6667, f)
    reactor.run()
        
