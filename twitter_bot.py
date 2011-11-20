import ConfigParser
import sys
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, task
from twisted.python import log

import simplejson, urllib

class TwitterBot(irc.IRCClient):
    got_Pong = True
    last_tweet_id ='0'

    def __init__(self, config):
        self.nickname = config.get('twitter_bot', 'nickname')
        self.password = config.get('twitter_bot', 'password')
        self.owner = config.get('twitter_bot', 'owner')
        self.channels = config.get('twitter_bot', 'channels').split(', ')
        self.trigger = config.get('twitter_bot', 'trigger')
        self.twitter_account = config.get('twitter_bot', 'twitter_account')

    def signedOn(self):
        for chan in self.channels:
            log.msg('Joining channel ' + chan)
            self.join(chan)

        self.lc = task.LoopingCall(self.update_twitter)
        self.lc.start(24, False)

    def update_twitter(self):
        rate_limit_status=get_rate_status()
        
        if int(rate_limit_status['remaining_hits']) > 1:
            last_tweet = get_last_tweet(self.twitter_account)

            if long(self.last_tweet_id) < long(last_tweet['id']):
                log.msg('Latest tweet: ' + last_tweet['text'])
                    
                self.last_tweet_id = last_tweet['id']
                for chan in self.channels:
                    self.say(chan, last_tweet['text'])
        else:
            log.msg('Rate limit reached!')
            self.msg(self.owner,'Rate limit reached!')

    def privmsg(self, user, channel, msg):
        user = user.split('!', 1)[0]

        if channel == self.nickname:
            log.msg('Message received: <' + user + '> ' + msg)

            if user == self.owner and self.trigger in msg:
                if 'addchannel' in msg:
                    chan = msg.split()[1]
                    self.join(chan)
                    self.channels.append(chan)

                if 'leavechannel' in msg:
                    chan = msg.split()[1]
                    self.leave(chan)
                    self.channels.remove(chan)

class TwitterBotFactory(protocol.ClientFactory):
    
    def __init__(self, config):
        self.config = config

    def buildProtocol(self, addr):
        return TwitterBot(self.config)

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

    config = ConfigParser.ConfigParser()
    config.read('twitter_bot.cfg')

    f = TwitterBotFactory(config)

    log.msg('Connecting...')
    reactor.connectTCP(config.get('twitter_bot', 'irc_server'), int(config.get('twitter_bot', 'irc_server_port')), f)
    reactor.run()