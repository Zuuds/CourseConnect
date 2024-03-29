"""Psudo Algo
each node has info about it's own ip, next node's ip and leader's ip

Leader election algorithm which follows below steps
step1: any node can initiate an election via the method election and passing None as as parameter and sends it's ip as election:ip to next node
step2: once a node receives a notification to initiate an election via election:ip msg, it calls method election which compares the current election:ip with its own ip, and forwards the bigger ip to next node in election:ip
step3: when incoming election:ip from election method == current(my own) ip. method elected leader is initiated. This method updates the local variable leader_ip and forwards elected leader ip to next node
step4: when a node received a msg elected leader ip, it calls method elected leader ito update the local variable leader_ip and forwards elected leader ip to next node
step5 if received a msg elected leader ip == current(my own) ip. algorithm stops
"""

import asyncio
import json
import traceback
import websockets
import requests
from linkedlist import SortedCircularLinkedList as scll

class Leader:
    def __init__(self, leader_ip, ring_nodes:scll()):
        self.leader_ip = leader_ip
        self.ring_nodes = ring_nodes

    def update_leader(self,leader_ip):
        self.leader_ip = leader_ip

    def get_leader(self):
        return self.leader_ip 

    def update_ring_nodes(self,ring_nodes:scll()):
        self.ring_nodes = ring_nodes
    
    async def update_successor_of_ring(self):
        try:
            if self.ring_nodes.head is None:
                return
            node = self.ring_nodes.head
            while True:
                curr_ip = node.data
                next_ip = node.get_successor(curr_ip)
                update_successor_msg =  {self.successor_key: next_ip}
                async with websockets.connect(f"ws://{curr_ip}") as websocket:
                    await websocket.send(json.dumps(update_successor_msg))
                node = node.next
                if node == self.ring_nodes.head:
                    break
        except Exception as e:
            print("\n\nException while updating successors of the ring : {e}\n")

    async def failure_handling(self, failed_ip):
        try:
            pred_ip = self.ring_nodes.get_predecessor(failed_ip)
            succ_ip = self.ring_nodes.get_successor(failed_ip)
            self.ring_nodes.remove_node(failed_ip)
            update_successor_msg =  {self.successor_key: succ_ip}
            async with websockets.connect(f"ws://{pred_ip}") as websocket:
                await websocket.send(json.dumps(update_successor_msg))
        except Exception as e:
            print("\n\nException while failure handling : {e}\n")

class RingProtocolLeaderElection:
    def __init__(self, my_ip, next_ip):
        self.my_ip = my_ip
        # self.my_ip = my_ip
        self.next_ip = next_ip
        self.leader = Leader('localhost:8100', scll())
        self.lock = asyncio.Lock()
        self.election_key = 'election'
        self.leader_elected_key = 'elected'
        self.allnodes_key = 'network'
        self.successor_key = 'successor'
        self.nodefail_key = 'nodefail'
        self.test_key = 'test'
    
    def get_public_ip(self):
        try: 
            url = 'https://api.ipify.org'
            response = requests.get(url)
            return response.text
        except Exception as e:
            print(f"\n\nError to get public Ip : {e}\n")
    
    async def send_msg(self, msg):
        async with websockets.connect(f"ws://{self.next_ip}") as websocket:
            msg = {"type":  "test", "ip": self.my_ip}
            await websocket.send(json.dumps(msg))

    async def initiate_election(self):
        async with websockets.connect(f"ws://{self.next_ip}") as websocket:
            msg = {"type": "election", "ip": self.my_ip}
            await websocket.send(json.dumps(msg))
            
    async def election(self, electing_ip):
        try:
            if electing_ip == self.my_ip:
                nodes = scll()
                nodes.add_node(self.my_ip)
                async with self.lock:
                    self.leader.update_leader(self.my_ip)
                    elected_leader_msg = {self.leader_elected_key: self.my_ip, self.allnodes_key:nodes}
                    async with websockets.connect(f"ws://{self.next_ip}") as websocket:
                        await websocket.send(json.dumps(elected_leader_msg))
            else:
                if electing_ip > self.my_ip:
                    election_msg = {self.election_key: electing_ip}
                elif electing_ip is None or electing_ip < self.my_ip:
                    election_msg = {self.election_key: self.my_ip}
                async with websockets.connect(f"ws://{self.next_ip}") as websocket:
                    await websocket.send(json.dumps(election_msg))
        except Exception as e:
            print(f"\n\nException while election : {e}\n")
        
    async def elected_leader(self, leader_ip, nodes:scll()):
        try:
            nodes.add_node(self.my_ip)
            async with self.lock:
                if self.leader.get_leader() == self.my_ip:
                    self.perform_leader_job(nodes)
                    return
                self.leader.update_leader(self.my_ip)
            elected_leader_msg =  {self.leader_elected_key: self.my_ip, self.allnodes_key:nodes}
            async with websockets.connect(f"ws://{self.next_ip}") as websocket:
                await websocket.send(json.dumps(elected_leader_msg))
        except Exception as e:
            print(f"\n\nException while updating elected leader: {e}\n")
        
    #Ask Divya
    async def perform_leader_job(self, nodes:scll()):
        try:
            #updates nodes list
            self.leader.update_ring_nodes(nodes)
            self.leader.update_successor_of_ring()
        except Exception as e:
            print(f"\n\nException performing leader's tasks: {e}\n")
        

    async def update_successor(self, successor_ip):
        self.next_ip = successor_ip
    

    # Checks for failure in nearby nodes should be paired with PING/ACK
    async def failure_handling(self, failed_ip):
        leader = self.leader.get_leader() 
        if leader == self.my_ip:
            self.leader.failure_handling(failed_ip)
        elif failed_ip == leader:
            self.election(None)
        else:
            #inform leader
            node_fail_msg =  {self.nodefail_key: failed_ip}
            async with websockets.connect(f"ws://{leader}") as websocket:
                await websocket.send(json.dumps(node_fail_msg))


    # async def connect_to_node(self):
    #         async with websockets.connect(f"ws://{self.next_ip}") as websocket:
    #             await websocket.send(json.dumps({}))
    #             msg = await websocket.recv()
    #             print(f"Received message from {self.next_ip}: {msg}")

    async def handler(self,websocket,path):
        try:
            #Below line throwing error  
            # async with websockets.connect(f"ws://{self.my_ip}") as websocket:
            #     while True:
                    
                    msg = json.loads(await websocket.recv())
                    print('Message: ',msg)
                    if self.election_key in msg.keys():
                        await self.election(msg[self.election_key])
                    elif self.leader_elected_key in msg.keys():
                        await self.elected_leader(msg[self.leader_elected_key],msg[self.allnodes_key] )
                    elif self.successor_key in msg.keys():
                        await self.update_successor(msg[self.successor_key])
                    elif self.nodefail_key in msg.keys():
                        await self.failure_handling(msg[self.nodefail_key])
                    elif self.test_key in msg.keys():
                        await self.send_msg(msg[self.test_key])
                        print('Message sent: '+ msg)
        except Exception as e:
            print(f"\n\nException while listening to message : {e}\n")
            traceback.print_exc()

    async def listen(self):
        async with websockets.serve(self.handler, 'localhost', 8100):
            print("Server Running")
            await asyncio.Future()
        
