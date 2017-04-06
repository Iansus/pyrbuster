#!/usr/bin/python

import argparse
import logging
import requests
import sys
import threading
import time

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logging.basicConfig(format = '\r%(asctime)s] %(levelname)-9s %(message)s')
logger = logging.getLogger('main')
logger.setLevel(logging.INFO)

def auto_int(s):
    try:
        return int(s, 0)
    except ValueError, e:
        raise argparse.ArgumentTypeError('Cannot parse int: {0}'.format(e))


def int_comma_list(s):
    try:
        return map(auto_int, s.split(','))
    except Exception, e:
        raise argparse.ArgumentTypeError('Cannot parse comma list: {0}'.format(e))


def url(s):
    try:
        if not '://' in s:
            raise Exception('no scheme in URL')

        scheme, url = s.split('://')
        if scheme.lower() not in ['http', 'https']:
            raise Exception('only http/https supported')

        while s[-1]=='/':
            s = s[:-1]

        return s

    except Exception, e:
        raise argparse.ArgumentTypeError('Cannot use file: {0}'.format(e))


def file(s):
    try:

        f = open(s, 'r')
        c = f.read()
        f.close()

        return c

    except Exception, e:
        raise argparse.ArgumentTypeError('Cannot parse url: {0}'.format(e))


R_HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:45.0) Gecko/20100101 Firefox/45.0'}
R_PROXIES = {'http':'http://127.0.0.1:8080', 'https':'http://127.0.0.1:8080'}

class Buster(threading.Thread):

    def __init__(self, testList, code, codes, url, ext):

        threading.Thread.__init__(self)
        self.testList = testList
        self.url = url
        self.ext = '.'+ext if ext is not None else ''
        self.alive = False
        self.code = code
        self.codes = codes
        self.len = len(testList)
        self.cur = 0

    def kill(self):
        self.alive = False

    def log(self, m, l):
        logger.log(l, m)

    def run(self):

        self.alive = True
        for i in range(self.len):

            uri = self.testList[i]
            self.cur = i

            if not self.alive:
                break

            fullurl = '%s%s%s' % (self.url, uri, self.ext)
            r = requests.get(fullurl, headers=R_HEADERS, proxies=R_PROXIES, verify=False, allow_redirects=False)

            logger.debug('trying "%s" [%d]' % (fullurl, r.status_code))
            if r.status_code in self.codes:
                logger.info('URL "%s" is valid [%d]' % (fullurl, r.status_code))



if __name__ == '__main__':

    ap = argparse.ArgumentParser()

    ap.add_argument('-t', '--target', dest='target', help='Target **host**, including scheme (HTTP, HTTPS)', required='True', type=url)
    ap.add_argument('-p', '--port', dest='port', type=auto_int, default=80, help='Target port (default:80)')
    ap.add_argument('-b', '--base-uri', dest='baseuri', default='/', help='Base URI, default is /')
    ap.add_argument('-n', '--nb-threads', dest='nthreads', default=1, type=auto_int, help='Number of threads')
    ap.add_argument('-l', '--list-codes', dest='list', default='200,403', help='List of correct HTTP error codes', type=int_comma_list)
    ap.add_argument('-w', '--wordlist', dest='wl', help='Wordlist', required=True, type=file)
    ap.add_argument('-e', '--extension', dest='ext', help='Extension to search for')
    ap.add_argument('-v', '--verbose', dest='verb', action='store_true', default=False, help='Increase verbosity')

    args = ap.parse_args()

    if args.verb:
        logger.setLevel(logging.DEBUG)

    baseUri = args.baseuri if args.baseuri[-1]=='/' else args.baseuri+'/'
    url = '%s:%d%s' % (args.target, args.port, baseUri)

    logger.info('using URL %s' % url)

    urilist = args.wl.replace('\r\n','\n').split('\n')
    urilist = [e for e in urilist if len(e)>0 and e[0]!='#']
    l = len(urilist)

    threads = []
    for i in range(args.nthreads):
        b = Buster(urilist[i*l/args.nthreads:(i+1)*l/args.nthreads], i, args.list, url, args.ext)
        b.daemon = True
        threads.append(b)
        b.start()

    try:
        while True:
            time.sleep(0.5)

            ntot = 0
            for thread in threads:
                ntot += thread.cur

            sys.stdout.write('\r%d/%d' % (ntot, l))
            sys.stdout.flush()

    except KeyboardInterrupt:
        print ''
        logger.info('Exiting on ctrl-c')
