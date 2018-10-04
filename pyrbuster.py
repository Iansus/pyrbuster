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

'''
Buster class and variables
'''

# DEFAULTS
R_HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:45.0) Gecko/20100101 Firefox/45.0'}
R_PROXIES = {}
R_COOKIES = {}
R_TIMEOUT = 5
R_WAIT = 5

# CLASS
class Buster(threading.Thread):

    #def __init__(self, testList, code, codes, url, ext, dodirs):
    def __init__(self, poolbase, workerId, statusCodes, baseUrl, extensionList, testDirectories, outputStream, sleepTime, outputLock):

        threading.Thread.__init__(self)

        # Class attributes
        self.__pool = poolbase
        self.__done = []
        self.__id = workerId
        self.__statusCodes = statusCodes
        self.__baseUrl = baseUrl
        self.__extensionList = extensionList
        self.__testDirectories = testDirectories
        self.__increment = len(self.__extensionList) if not testDirectories else 1+len(self.__extensionList)
        self.__current = 0
        self.__outputStream = outputStream
        self.__sleepTime = sleepTime
        self.__outputLock = outputLock

    def kill(self):
        self.alive = False

    def log(self, m, l):
        logger.log(l, m)

    def getTotal(self):
        return self.__increment * (len(self.__pool) + len(self.__done))

    def getCurrent(self):
        return self.__current

    def run(self):

        self.alive = True
        while True:

            if not self.alive:
                break

            # Is there sthing to do?
            if len(self.__pool)==0:
                logger.debug('Worker %d has nothing to do, sleeping for %d seconds...' % (self.__id, R_WAIT))
                time.sleep(R_WAIT)
                continue

            # Remove from pool, add to done 
            uri = self.__pool.pop(0)
            self.__done.append(uri)

            success = []
            
            # Test with extensions
            for ext in self.__extensionList:
                success += self.__testUrl(uri, ext)

            # Test with directory
            if self.__testDirectories:
                success += self.__testUrl(uri, '/')
                
            # Optionnally output to output stream
            if len(success)>0 and self.__outputStream is not None:
                
                wData = ''
                for retval in success:
                    wData += retval+'\n'
                
                self.__outputLock.acquire()
                self.__outputStream.write(wData)
                self.__outputStream.flush()
                self.__outputLock.release()
                
            
    def __testUrl(self, uri, ext):

        requestOk = 3
        ret = []
        while requestOk > 0:
            try:
                # Build URL
                fullurl = '%s%s%s' % (self.__baseUrl, uri, ext)
                r = requests.get(fullurl, headers=R_HEADERS, timeout=R_TIMEOUT, cookies=R_COOKIES, proxies=R_PROXIES, verify=False, allow_redirects=False)
                requestOk = 0
                logger.debug('trying "%s" [%d]' % (fullurl, r.status_code))

                # Is it OK for us ?
                if r.status_code in self.__statusCodes:
                    logger.info('URL "%s" is valid [%d]' % (fullurl, r.status_code))
                    ret = ['[%d]\t%s' % (r.status_code, fullurl)]
                else:   
                    ret = []

            except (requests.ConnectionError, requests.exceptions.ReadTimeout), e:
                requestOk -= 1
                if requestOk == 0:
                    logger.error('Connection error on "%s"', (fullurl))

            if self.__sleepTime > 0:
                time.sleep(self.__sleepTime)

        self.__current +=1

        return ret

'''
Types for argument parser
'''
def type_auto_int(s):
    try:
        return int(s, 0)
    except ValueError, e:
        raise argparse.ArgumentTypeError('Cannot parse int: {0}'.format(e))

def type_int_comma_list(s):
    try:
        return map(type_auto_int, s.split(','))
    except Exception, e:
        raise argparse.ArgumentTypeError('Cannot parse comma list: {0}'.format(e))

def type_ext_list(s):

    if s is None:
        return []

    else:
        return ['.'+e for e in s.strip().split(',')]

def type_url(s):
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
        raise argparse.ArgumentTypeError('Cannot parse url: {0}'.format(e))

def type_input_file(s):
    try:

        f = open(s, 'r')
        c = f.read()
        f.close()

        return c

    except Exception, e:
        raise argparse.ArgumentTypeError('Cannot use file: {0}'.format(e))

def type_output_file(s):
    try:

        f = open(s, 'w')
        return f

    except Exception, e:
        raise argparse.ArgumentTypeError('Cannot use file: {0}'.format(e))


'''
Main
'''
if __name__ == '__main__':

    # Argument parser and options
    ap = argparse.ArgumentParser()

    ap.add_argument('-t', '--target', dest='target', help='Target **host**, including scheme (HTTP, HTTPS)', required='True', type=type_url)
    ap.add_argument('-p', '--port', dest='port', default=80, help='Target port (default:80)', type=type_auto_int)
    ap.add_argument('-b', '--base-uri', dest='baseuri', default='/', help='Base URI, default is /')
    ap.add_argument('-n', '--nb-threads', dest='nthreads', default=1, help='Number of threads', type=type_auto_int)
    ap.add_argument('-l', '--list-codes', dest='list', default='200,403', help='List of correct HTTP error codes', type=type_int_comma_list)
    ap.add_argument('-w', '--wordlist', dest='wl', help='Wordlist', required=True, type=type_input_file)
    ap.add_argument('-e', '--extension', dest='ext', help='Extension to search for', type=type_ext_list)
    ap.add_argument('-d', '--directories', dest='dirs', action='store_true', help='Search for directories')
    ap.add_argument('-v', '--verbose', dest='verb', action='store_true', default=False, help='Increase verbosity')
    ap.add_argument('-o', '--output', dest='output', help='Output file', type=type_output_file)
    ap.add_argument('-s', '--sleep', dest='sleep', help='Sleep for x seconds between each request (by thread)', type=float, default=0)

    ap.add_argument('--proxy', dest='proxy')
    ap.add_argument('--cookies', dest='cookies', help='Example: cookie1=v1&cookie2=v2')
    ap.add_argument('--timeout', dest='timeout', help='Set request timeout', type=float)

    args = ap.parse_args()

    # Quick checks on args
    if not (args.ext or args.dirs):
        logger.error('Either extension or directory is required')
        sys.exit(1)

    if args.verb:
        logger.setLevel(logging.DEBUG)

    if args.proxy:
        R_PROXIES = {'http': args.proxy, 'https':args.proxy, 'ftp':args.proxy}

    if args.cookies:
        cookies = args.cookies.split('&')
        R_COOKIES = {k:v for k,v in [e.split('=') for e in cookies]}

    if args.timeout:
        R_TIMEOUT = args.timeout
        
    if args.ext is None:
        args.ext = []

    # Sanitize uri
    baseUri = args.baseuri if args.baseuri[-1]=='/' else args.baseuri+'/'
    url = '%s:%d%s' % (args.target, args.port, baseUri)
    logger.info('using URL %s' % url)

    # Sanitize file contents
    urilist = args.wl.replace('\r\n','\n').split('\n')
    urilist = [e for e in urilist if len(e)>0 and e[0]!='#']
    l = len(urilist)

    logger.info('All arguments OK, starting PyrBuster, stop with CTRL-C')

    # Create and start threads
    threads = []
    lock = threading.Lock()
    for i in range(args.nthreads):
        b = Buster(urilist[i*l/args.nthreads:(i+1)*l/args.nthreads], i, args.list, url, args.ext, args.dirs, args.output, args.sleep, lock)
        b.daemon = True
        threads.append(b)
        b.start()

    # Print progress
    try:
        while True:
            time.sleep(0.5)

            totalSize = 0
            currentProgress = 0
            for thread in threads:
                currentProgress += thread.getCurrent()
                totalSize += thread.getTotal()

            sys.stdout.write('\r%d/%d' % (currentProgress, totalSize))
            sys.stdout.flush()

    except KeyboardInterrupt:
        if args.output is not None:
            args.output.close()
            
        print ''
        logger.info('Exiting on ctrl-c')
