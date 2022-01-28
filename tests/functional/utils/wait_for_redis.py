import sys
import time
from redis import Redis

def try_connect(host,port):
    while True:
        try:
            r = Redis(host, socket_connect_timeout=1)  # short timeout for the test
            r.ping()
            break
        except :
            time.sleep(1)


if __name__ == "__main__":
    try_connect(sys.argv[1],sys.argv[2])
