import asyncio
import json
import websockets
import requests
from linkedlist import SortedCircularLinkedList as scll
import leader

#Using Localhost port 8000

async def main():
    node = leader.RingProtocolLeaderElection('localhost:8300','localhost:8400')
    while True:
        try:
            await node.listen()
        except Exception as e:
            print(f"\n\nException while listening to message : {e}\n")
            
asyncio.run(asyncio.sleep(15))       
asyncio.run(main())