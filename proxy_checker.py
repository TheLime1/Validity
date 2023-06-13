import os
import random
import requests

source1 = os.environ['SOURCE1']
response = requests.get(source1)
proxies = response.text.split("\n")

proxies = random.sample(proxies, 5)  # !comment when done testing

with open("proxy_list.txt", "a") as f:
    for proxy in proxies:
        try:
            response = requests.get(
                "http://httpbin.org/ip", proxies={"http": proxy, "https": proxy}, timeout=5)
            if response.ok:
                print(f"{proxy} is online")
                f.write(f"{proxy}\n")
                f.flush()
            else:
                print(f"{proxy} is offline")
        except:
            print(f"{proxy} is offline")
