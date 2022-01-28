import requests
import sys
import time

def try_connect(host,port):
    while True:
        try:
            resp1 = requests.head('http://'+host+':'+port, headers={'content-type': 'application/json', 'charset': 'UTF-8'})
            break
        except :
            time.sleep(1)


if __name__ == "__main__":
    try_connect(sys.argv[1],sys.argv[2])
