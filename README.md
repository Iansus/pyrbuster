# pyrbuster
Python based directory buster

```
usage: pyrbuster.py [-h] -t TARGET [-p PORT] [-b BASEURI] [-n NTHREADS]
                    [-l LIST] -w WL [-e EXT] [-v] [--proxy PROXY]
                    [--cookies COOKIES] [--timeout TIMEOUT]

optional arguments:
  -h, --help            show this help message and exit
  -t TARGET, --target TARGET
                        Target **host**, including scheme (HTTP, HTTPS)
  -p PORT, --port PORT  Target port (default:80)
  -b BASEURI, --base-uri BASEURI
                        Base URI, default is /
  -n NTHREADS, --nb-threads NTHREADS
                        Number of threads
  -l LIST, --list-codes LIST
                        List of correct HTTP error codes
  -w WL, --wordlist WL  Wordlist
  -e EXT, --extension EXT
                        Extension to search for
  -v, --verbose         Increase verbosity
  --proxy PROXY
  --cookies COOKIES     Example: cookie1=v1&cookie2=v2
  --timeout TIMEOUT     Set request timeout
```

## Know issues

### InsecureRequestWarning

If you have the following error message `cannot import name InsecureRequestWarning`, the issue is due to an old version of requests.
To solve it, run:
* `sudo pip install --upgrade pip`
* `sudo pip install --upgrade requests`

## TODO

### Short term
* Allow for more tuning options (User-Agent and other custom headers)
* Smart recursive scanning

### Medium term
* Pause and restore scans

### Very long term
* GUI
* Code comments
* Documentation
