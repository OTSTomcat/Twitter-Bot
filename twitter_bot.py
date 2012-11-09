import ConfigParser
import sys
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, threads
from twisted.python import log
from oauth import oauth
from twittytwister import twitter

class TwitterBot(irc.IRCClient):
    got_Pong = True
    last_tweet_id ='0'

    def __init__(self, config):
	self.config = config
        self.nickname = config.get('twitter_bot', 'nickname')
        self.password = config.get('twitter_bot', 'password')
        self.owner = config.get('twitter_bot', 'owner')
        self.channels = config.get('twitter_bot', 'channels').split(', ')
        self.trigger = config.get('twitter_bot', 'trigger')

	self.follow_id = config.get('twitter_bot', 'follow_id')

	consumer_key = config.get('oauth', 'consumer_key')
	consumer_secret = config.get('oauth', 'consumer_secret')
	access_token_key = config.get('oauth', 'access_token_key')
	access_token_secret = config.get('oauth', 'access_token_secret')
	
	self.consumer = oauth.OAuthConsumer(consumer_key, consumer_secret)
	self.token = oauth.OAuthToken(access_token_key, access_token_secret)

    def say_tweet(self, tweet):
	for chan in self.channels:
		self.say(chan, tweet)
	
    def signedOn(self):
        for chan in self.channels:
            log.msg('Joining channel ' + chan)
            self.join(chan)

	self.start_monitor(self.follow_id)

    def start_monitor(self, twitter_user_id):
	feed = twitter.TwitterFeed(consumer=self.consumer, token=self.token)
	monitor = twitter.TwitterMonitor(feed.filter, lambda entry: self.say_tweet(entry.text.encode('utf-8')), {'follow': twitter_user_id})

	monitor.startService()

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

if __name__ == '__main__':

    log.startLogging(sys.stdout)

    config = ConfigParser.ConfigParser()
    config.read('twitter_bot.cfg')

    f = TwitterBotFactory(config)

    log.msg('Connecting...')
    reactor.connectTCP(config.get('twitter_bot', 'irc_server'), int(config.get('twitter_bot', 'irc_server_port')), f)
    reactor.run()

