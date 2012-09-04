from __future__ import division
import oauth2 as oauth
import httplib
import ConfigParser
import webbrowser
import sys, os
import base64
import random
import twitter
try:
    from urlparse import parse_qsl
except:
    from cgi import parse_qsl
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer


request_token = None
OAuth_VerifToken = None

class TwitterClient():
    class CallbackServer(BaseHTTPRequestHandler):
        # Handle the callback from Twitter
        def do_GET(self):
            try:
                # Easiest way to send the data back ot the main code seems to be
                # with a global variable. Ugly, but it works
                global OAuth_VerifToken
                OAuth_VerifToken = dict(parse_qsl(self.path.lstrip('/?')))
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write('<html><head><title>EnergyTweeter Authorisation Complete</title></head>')
                self.wfile.write('<body><h1>EnergyTweeter Authorisation Complete</h1>')
                self.wfile.write('<p>Setup is now complete for EnergyTweeter. ')
                self.wfile.write('You should now close this browser tab/window and return to EnergyTweeter</p></body>')
            except:
                print "Received exception %s (%s) sending webpage\n" % (sys.exc_info()[0], sys.exc_info()[1])
                self.send_response(500)
                raise

    def __init__(self, consumer_key='', consumer_secret='', config=None):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        if self.consumer_key == '' or self.consumer_secret == '':
            print "Consumer_Key and/or Consumer_Secret not set."
            print "You must register this app with Twitter."
            raise Exception
        self.request_token_url = 'https://api.twitter.com/oauth/request_token'
        self.access_token_url = 'https://api.twitter.com/oauth/access_token'
        self.authorization_url = 'https://api.twitter.com/oauth/authorize'
        self.signin_url = 'https://api.twitter.com/oauth/authenticate'
        self.config = config
        self.OAuthConsumer = oauth.Consumer(self.consumer_key, self.consumer_secret)
        self.signature_method = oauth.SignatureMethod_HMAC_SHA1()
        self.OAuthClient = oauth.Client(self.OAuthConsumer)
        self.TwitterAPI = None

    def setup(self, config):
        try:
            self.config.get('EnergyTweeter', 'ACCESS_TOKEN')
        except ConfigParser.NoSectionError:
            self.config.add_section('EnergyTweeter')
        except ConfigParser.NoOptionError:
            pass
        else:
            # Already have an access token, no need to re-do setup
            print "This application is already authorized. To re-setup, please remove the"
            print "ACCESS_TOKEN and ACCESS_SECRET from %s" % self.config.get('_Internal_', 'fname')
            return

        # Start the webserver on a random, high-numbered port
        try:
            server_port = random.randint(49152, 61000)
            server = HTTPServer(('', server_port), self.CallbackServer)
            print "Webserver waiting on port %d" % server_port
        except:
            # Can't start the server, fallback to 'oob' mode
            print "Received exception %s (%s) starting webserver\n" % (sys.exc_info()[0], sys.exc_info()[1])
            server_port = None
            #raise
        if server_port is not None:
            callback_url = "http://localhost:%d/" % server_port
        else:
            # We couldn't launch a server, so request the out-of-band PIN method
            print "Using OOB method"
            callback_url = 'oob'

        response, content = self.OAuthClient.request(self.request_token_url, 'POST', body='oauth_callback=%s' % callback_url)
        if response['status'] != '200':
            raise Exception("Invalid response from Twitter while requesting token: %s" % response['status'])
        else:
            request_token = dict(parse_qsl(content))
            if request_token['oauth_callback_confirmed'] != 'true':
                print "WARNING: OAuth Callback NOT confirmed"
        try:
            newpid = os.fork()
            if newpid == 0:
                # Child. Launch the webbrowser to allow the user to authenicate us

                # We now direct the user to a URL to authorize us.
                # Twitter will then redirect to CALLBACK_URL, where we should be waiting
                twitter_auth_url = "%s?oauth_token=%s" % (self.authorization_url, request_token['oauth_token'])
                try:
                    webbrowser.open(twitter_auth_url, new=2)
                except:
                    print "Can't launch a webbrowser. Please launch one manually, and navigate to:"
                    print "  %s" % twitter_auth_url
                os._exit(0)
            else:
                # Parent. Start serving. Wait for the twitter callback
                if server_port is not None:
                    print "Waiting for Twitter authorization"
                    server.handle_request()
                else:
                    OAuth_VerifToken['oauth_verifier'] = raw_input('Please enter the PIN Twitter has provided you here: ')
        except:
            print "Failed to get Twitter Authorisation: %s (%s)" % (sys.exc_info()[0], sys.exc_info()[1])
            raise

        if OAuth_VerifToken is None or not OAuth_VerifToken.has_key('oauth_verifier'):
            print "Failed to get Twitter Authorisation Token"
            return False
        if request_token is None or not request_token.has_key('oauth_token'):
            print "Failed to send Twitter Authorisation Token"
            return False
        if OAuth_VerifToken['oauth_token'] != request_token['oauth_token']:
            print "Invalid OAuthToken returned (sent %s, got %s)" % (OAuthVerif['oauth_token'], request_token['oauth_token'])
        else:
            # That's the hard stuff done. Now to swap our request token for an access token
            print "Creating Token(%s,%s)" % (request_token['oauth_token'], request_token['oauth_token_secret'])
            self.OAuthToken = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
            print "Setting Verifier(%s)" % OAuth_VerifToken['oauth_verifier']
            self.OAuthToken.set_verifier(OAuth_VerifToken['oauth_verifier'])
            client = oauth.Client(self.OAuthConsumer, self.OAuthToken)

            response, content = self.OAuthClient.request(self.access_token_url, "POST", body='oauth_verifier=%s' % OAuth_VerifToken['oauth_verifier'])
            if response['status'] != '200':
                print response
                print content
                raise Exception("Invalid response from Twitter while requesting token: %s" % response['status'])
            access_token = dict(parse_qsl(content))
            print access_token

            # Access Token received
            print "Access Token:"
            print "    - oauth_token        = %s" % access_token['oauth_token']
            print "    - oauth_token_secret = %s" % access_token['oauth_token_secret']

            self.config.set('EnergyTweeter', 'ACCESS_TOKEN', access_token['oauth_token'])
            self.config.set('EnergyTweeter', 'ACCESS_SECRET', access_token['oauth_token_secret'])
            return True

    def Tweet(self, string):
        if self.TwitterAPI is None:
            self.TwitterAPI = twitter.Api(consumer_key=self.consumer_key,
                                          consumer_secret=self.consumer_secret,
                                          access_token_key=self.config.get('EnergyTweeter', 'ACCESS_TOKEN'),
                                          access_token_secret=self.config.get('EnergyTweeter', 'ACCESS_SECRET'))
        if string is None:
            raise UserError("Can't tweet an empty string")
        return self.TwitterAPI.PostUpdate(string)


class EnergyTweeter:
    def __init__(self):
        self.client = None
        self.config = None
        self.Energy = None
        pass

    def LoadConfig(self, configfile='.EnergyTweeterRC'):
        self.config = ConfigParser.SafeConfigParser()
        fname = self.config.read(configfile)
        try:
            self.config.add_section("_Internal_")
        except DuplicateSectionError:
            pass
        self.config.set("_Internal_", "fname", ",".join(fname))
        # Twitter ask that this is not human readable.
        self.consumer_key = base64.b64decode('eElyNmx3MUx6a0ljUEg3SWU5Ykw0Zw==')
        self.consumer_secret = base64.b64decode('ZG5DeVJ4OWk0ejFuOHE3UUpPVUVTcjE2bW5WMmRCMjJ4V3h5OWdsNmJV')

    def Setup(self):
        self.client = TwitterClient(self.consumer_key, self.consumer_secret, self.config)
        self.client.setup(self.config)

    def GetEnergy(self, hostname, cron=False):
        import rrdtool
        import re
        import time
        import calendar

        RRDDIR = '/var/lib/munin'
        domain = host.split('.',1)[1]
        self.Energy = dict()

        tzoffset = calendar.timegm(time.localtime()) - calendar.timegm(time.gmtime())
        if not cron:
            print "Searching dir %s" % os.path.join(RRDDIR,domain)
        for filename in os.listdir(os.path.join(RRDDIR,domain)):
            matches = re.search(r"%s-currentcost-ch([0-9]+)-g" % host, filename)
            if matches is not None:
                channel = matches.group(1)
                print "Channel %s:" % channel
                (header,count,data) = rrdtool.fetch(os.path.join(RRDDIR,domain,filename),
                        "AVERAGE",
                        "-r", str(5*60),     # 5 minute steps
                        "-s", "00:00 yesterday",
                        "-e", "23:59 yesterday")
                if not cron:
                    print "Data from %s to %s (%s second steps)" % (time.strftime('%H:%M:%S, %d/%m/%Y', time.gmtime(header[0] + tzoffset)),
                                                                    time.strftime('%H:%M:%S, %d/%m/%Y', time.gmtime(header[1] + tzoffset)),
                                                                    str(header[2]))
                datasum = 0
                datamin = (None, None)
                datamax = (None, None)
                nancount = 0
                timestamp = header[0] + tzoffset
                for datum in data:
                    if datum[0] is None:
                        nancount += 1
                        continue
                    watts = float(datum[0])
                    watthours = watts/12    # 5 minute steps mean we need to divide by (60/5) to get per hour
                    timestamp += header[2]
                    if not cron:
                        print "%7.2f watts @ %s" % (watts, time.strftime('%H:%M:%S, %d/%m/%Y', time.gmtime(timestamp)))
                    datasum += watthours
                    if datamin[0] is None or watts < datamin[0]:
                        datamin = (watts, timestamp)
                    if datamax[0] is None or watts > datamax[0]:
                        datamax = (watts, timestamp)
                print "Total: %7.2f watt hours" % datasum
                print "Min:   %7.2f watts @ %s" % (datamin[0], time.strftime('%H:%M:%S, %d/%m/%Y', time.gmtime(datamin[1])))
                print "Max:   %7.2f watts @ %s" % (datamax[0], time.strftime('%H:%M:%S, %d/%m/%Y', time.gmtime(datamax[1])))
                if nancount > 0:
                   print "(      %7.5f%% (%d of %d samples are NaN)" % ((nancount/len(data)) * 100.0, nancount, len(data))
                self.Energy[channel] = (datasum, datamin, datamax, nancount/len(data))



        
    def TweetEnergy(self, energy=None, cron=False):
        import time
        if self.client is None:
            self.client = TwitterClient(self.consumer_key, self.consumer_secret, self.config)
        if energy is None:
            energy = self.Energy
        if energy is None:
            raise UserError("No Energy collected. Run 'GetEnergy' mode first!")

        for channel in range(1,10):
            if energy.has_key(str(channel)):
                if channel == 1:
                    # Whole House
                    #Example tweet: "Whole House Energy for DD/MM/YYYY: NN.NNNNkWh (Maximum: NNNNW @ HH:MM, Minimum: NNNNW @ HH:MM) #CurrentCost"
                    (datasum, (datamin,timemin), (datamax, timemax), nanratio) = energy[str(channel)]
                    if nanratio < 0.2:
                        tweet = "Whole House Energy for %(date)s: %(datasum)6.2fkWh\n * Maximum: %(datamax)4.0fW @ %(timemax)s\n * Minimum: %(datamin)4.0fW @ %(timemin)s\n#CurrentCost" % {'date'   : time.strftime("%d/%m/%Y", time.gmtime(time.time()-86400)),
                                          'datasum': datasum/1000,    # Convert from Wh to kWh
                                          'datamax': datamax,
                                          'timemax': time.strftime("%H:%M", time.gmtime(timemax)),
                                          'datamin': datamin,
                                          'timemin': time.strftime("%H:%M", time.gmtime(timemin))}
                        status = self.client.Tweet(tweet)
                        print "Posted Status #%s to %s" % (status.id, status.user.screen_name)
                    else:
                        print "Not posting status, NaN ratio is %7.5f%%" % (nanratio*100)
                else:
                    # Appliance
                    appliance = int(channel) - 1
                    # Example tweet: "Appliance #1  Energy for DD/MM/YYYY: NN.NNNNkWh (Maximum: NNNNW @ HH:MM, Minimum: NNNNW @ HH:MM) #CurrentCost"
                    (datasum, (datamin,timemin), (datamax, timemax), nanratio) = energy[str(channel)]
                    if nanratio < 0.2:
                        tweet = "Appliance #%(appl)-2d Energy for %(date)s: %(datasum)6.2fkWh\n * Maximum: %(datamax)4.0fW @ %(timemax)s\n * Minimum: %(datamin)4.0fW @ %(timemin)s\n#CurrentCost" % {'date'   : time.strftime("%d/%m/%Y", time.gmtime(time.time()-86400)),
                                          'datasum': datasum/1000,    # Convert from Wh to kWh
                                          'datamax': datamax,
                                          'timemax': time.strftime("%H:%M", time.gmtime(timemax)),
                                          'datamin': datamin,
                                          'timemin': time.strftime("%H:%M", time.gmtime(timemin)),
                                          'appl'   : appliance}
                        status = self.client.Tweet(tweet)
                        print "Posted Status #%s to %s" % (status.id, status.user.screen_name)
                    else:
                        print "Not posting status, NaN ratio is %7.5f%%" % (nanratio*100)



if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Tweet Energy')
    parser.add_argument('--mode', metavar='MODE', default='cron')
    parser.add_argument('-c', '--config', default='.EnergyTweeterRC')
    parser.add_argument('-H', '--host')
    args = parser.parse_args()

    ET = EnergyTweeter()
    ET.LoadConfig(configfile=args.config)

    try:
        host = ET.config.get('EnergyTweeter', 'host')
    except:
        try:
            host = args.host
        except:
            host = 'localhost.localdomain'


    if args.mode == 'setup':
        ET.Setup()
    elif args.mode == 'getenergy':
        ET.GetEnergy(host)
    elif args.mode == 'tweetenergy':
        ET.GetEnergy(host)
        ET.TweetEnergy()
    elif args.mode == 'cron':
        ET.GetEnergy(host, cron=True)
        ET.TweetEnergy(cron=True)
    else:
        print "MODE should be one of: setup, getenergy, tweetenergy, cron"

