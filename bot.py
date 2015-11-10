#!/usr/bin/env python3
"""Bot that replies to any @mention with Taylor Swift lyrics."""

from twitter import Twitter, TwitterStream, OAuth
from pprint import pformat
import random
import logging

# API_KEY, API_SECRET, ACCESS_TOKEN, and ACCESS_TOKEN_SECRET come from here!
import secrets


log = logging.getLogger('PySwizzle')


class PySwizzle(object):

    def __init__(self, username='pyswizzle'):
        self.username = username
        self.events = {}
        self.commands = {}
        self.stream = None
        self.lyrics = None

    def initialize_twitter(self, access_token=secrets.ACCESS_TOKEN,
                           access_token_secret=secrets.ACCESS_TOKEN_SECRET,
                           api_key=secrets.API_KEY,
                           api_secret=secrets.API_SECRET):
        log.debug('INITIALIZING TWITTER')
        auth = OAuth(access_token, access_token_secret, api_key, api_secret)
        t = Twitter(auth=auth)
        ts = TwitterStream(domain='userstream.twitter.com', auth=auth)

        self.twitter = t
        self.stream = ts.user()

    def load_lyrics(self, filename='taylor.txt'):
        # open up a file and get a list of lines of lyrics (no blank lines)
        with open(filename) as lyrics_file:
            self.lyrics = [l.strip() for l in lyrics_file if l != "\n"]

    def diagnostic_send_tweet(self, msg, **kwargs):
        log.critical('SEND: "%s"' % msg)

    def send_tweet(self, msg, reply_to=None):
        if reply_to is None:
            self.t.statuses.update(status=msg)
        else:
            self.t.statuses.update(status=msg, in_reply_to_status_id=reply_to)

    def handle_tweet(self, tweet):
        if tweet['user']['screen_name'] != self.username:
            # Pick a lyric, compose a reply, and send it!
            line = random.choice(self.lyrics)
            reply = '@' + tweet['user']['screen_name'] + ' ' + line
            self.send_tweet(reply, reply_to=tweet['id'])

    def run(self):
        # The user may want to substitute a mock stream or different lyrics.
        if self.stream is None:
            self.initialize_twitter()
        if self.lyrics is None:
            self.load_lyrics()

        for tweet in self.stream:

            # Log a pretty representation of the tweet.
            log.debug('TWEET:' + pformat(tweet))

            if 'event' in tweet:
                if tweet['event'] in self.events:
                    log.info('HANDLING EVENT "%s".' % tweet['event'])
                    self.events[tweet['event']](tweet)
                else:
                    log.info('UNHANDLED EVENT "%s".' % tweet['event'])

            elif 'hangup' in tweet:
                # open a new connection
                log.warning('TWITTER HANGUP.  RECONNECTING...')
                self.initialize_twitter()

            elif 'text' in tweet:
                log.info('HANDLING TWEET: @%s: \"%s\"' %
                         (tweet['user']['screen_name'], tweet['text']))
                self.handle_tweet(tweet)


def main():
    from argparse import ArgumentParser, FileType
    import sys
    parser = ArgumentParser(description='Run pyswizzle bot.')

    parser.add_argument('--local', type=FileType('r'), default=None,
                        help='use a script of tweets instead of going live')
    parser.add_argument('--log-file', type=FileType('w'), default=sys.stdout,
                        help='file to log to (stdout by default)')
    parser.add_argument('--level', type=str, default='CRITICAL',
                        help='log level for output')

    args = parser.parse_args()

    log.addHandler(logging.StreamHandler(args.log_file))
    log.setLevel(logging.getLevelName(args.level))

    bot = PySwizzle()
    if args.local is not None:
        # don't be stupid please
        bot.stream = eval(args.local.read())
        bot.send_tweet = bot.diagnostic_send_tweet
    bot.run()

if __name__ == '__main__':
    main()
