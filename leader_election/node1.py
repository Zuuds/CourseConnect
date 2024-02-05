import asyncio
import json
import traceback
import websockets
import requests
from linkedlist import SortedCircularLinkedList as scll
import leader

#Using Localhost port 8100
async def main():
    node = leader.RingProtocolLeaderElection('localhost:8100','localhost:8200')
    await node.listen()
    
        

asyncio.run(asyncio.sleep(5))
asyncio.run(main())

