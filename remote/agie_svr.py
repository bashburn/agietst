#!/usr/bin/python
#imports
import sys
import logging
import json
from qpid.messaging import *

#global vars
logging.basicConfig(filename="/tmp/agie.log", level=logging.INFO)
DEBUG = 0
broker_local = "localhost:5672"
addr_control = "agie_inbound/agie_inbound_control"
addr_data_src = "agie_inbound_d/agie_inbound_data"
net1_q = "agie_data_net1"
net2_q = "agie_data_net2"
last_intf = 'eth4'
eth4Queue = None
eth5Queue = None
eth4Sender = None
eth5Sender = None
qpid_opt = "; {create:always, node:{x-declare:{auto-delete:true, alternate-exchange: 'agie_alt'}}}"
net1_con = '"' + net1_q + qpid_opt + '"'
intf_table = []
title = ['status', 'intf_name', 'intf_ip', 'broker', 'queue']
intf_table = []

#functions
def intf_up(msg_list,intf_table, session):
	#need to add opening connection to remote broker on up as well.
	tmp_tbl_up = intf_table
	print 'add starting on %s' % (tmp_tbl_up)
	tmp_entry = dict(zip(title,msg_list))
	print 'tmp_entry: %s' % (tmp_entry)
	intf_tmp = tmp_entry.get('intf_name')
	if tmp_tbl_up != None:
		exist = [ iface for iface in tmp_tbl_up if iface.get('intf_name') == intf_tmp ]
	else:
		exist = None
	if exist:
		print "Interface already exists."
		if DEBUG == 1:
			print 'returning', intf_table
		return intf_table
	else:
		if tmp_entry['intf_name'] == "eth4":
			global eth4Queue
			global eth4Sender
			eth4Queue = session.receiver("agie_data_net1; {create:always, node:{x-declare:{auto-delete:true, alternate-exchange: 'agie_alt'}}}")
			eth4Sender = session.sender("agie_data_net1; {create:always, node:{x-declare:{auto-delete:true, alternate-exchange: 'agie_alt'}}}")
			if tmp_tbl_up != None:
				tmp_tbl_up.append(tmp_entry)
			else:
				tmp_tbl_up=[tmp_entry]
		elif tmp_entry['intf_name'] == "eth5":
			global eth5Queue
			global eth5Sender
			eth5Queue = session.receiver("agie_data_net2; {create:always, node:{x-declare:{auto-delete:true, alternate-exchange: 'agie_alt'}}}")
			eth5Sender = session.sender("agie_data_net2; {create:always, node:{x-declare:{auto-delete:true, alternate-exchange: 'agie_alt'}}}")
			if tmp_tbl_up != None:
				tmp_tbl_up.append(tmp_entry)
			else:
				tmp_tbl_up=[tmp_entry]
		else:
			print "major major issue"
		print 'Added inteface on ', msg_list[1]
		if DEBUG == 1:
			print tmp_tbl_up
		return tmp_tbl_up


def intf_down(msg_list, intf_table, eth4Queue, eth5Queue):
	tmp_tbl = intf_table
	tmp_entry = dict(zip(title,msg_list))
	intf_to_rm = tmp_entry['intf_name']	
	if intf_to_rm == 'eth4':
		eth4Queue.close()
		eth4Sender.close()
	elif intf_to_rm == 'eth5':
		eth5Queue.close()
		eth5Sender.close()
	else:
		print "queue close error"
	print 'Deteched down network.  Removing interface:', intf_to_rm
	up = [ iface for iface in tmp_tbl if iface.get('intf_name') != intf_to_rm ]
	print 'Inteface removed ', intf_to_rm
	tmp_tbl = up
	if DEBUG == 1:
		print 'returning ', tmp_tbl
	return tmp_tbl

def data_msg_mover(intf_table, sender_local, receiver_d, last_intf, eth4Sender, eth5Sender):
	received = None
	intf_names_up = [] #purposely not moving messages if all networks are down.  Technically we could move local messages still but I am not at this time.   
	if DEBUG == 1:
		print 'last_intf:', last_intf
	if intf_table == []:
		print 'No available networks'
		return last_intf
	try: 
		message = receiver_d.fetch(timeout=3)
		received = message.content	
		subject = message.subject
		count = len(intf_table)
		count1 = len(intf_table)
		for count in intf_table:
			intf_names_up.append(count['intf_name'])
		print 'Networks available to accept messages:', intf_names_up
		print "moving message:", message
		print 'last is %s and count is %i' % (last_intf, count1)
		if subject == 'app1':
			message.subject = 'app1'
			print 'moving', message.subject, message.content
			sender_app1.send(message)	
		elif subject == 'app2':
			message.subject = 'app2'
			sender_local.send(message)
		elif last_intf == 'eth4' and count1 == 2:
			eth5Sender.send(message)
			last_intf = 'eth5'
		elif last_intf == 'eth5' and count1 == 2:
			eth4Sender.send(message)
			last_intf = 'eth4'
		elif intf_names_up[0] == 'eth4' and count1 == 1:
			eth4Sender.send(message)
			last_intf = 'eth4'
		elif intf_names_up[0] == 'eth5' and count1 == 1:
			eth5Sender.send(message)
			last_intf = 'eth5'
		else:
			print 'major error in data_msg_mover'
		session.acknowledge()
	except Empty:
		print 'No message'
	except MessagingError,m:
		print m
	if received:
		print 'moved', received
	return last_intf

def broker_conn():
# create connection to local broker
	lb_connection = Connection(broker_local)
	try:
		lb_connection.open()
		session = lb_connection.session()
		receiver = session.receiver("agie_inbound_control")
		return receiver
	except MessagingError,m:
		print m

def intf_change(intf_table):
	if DEBUG == 1:
		print 'initial intf_table', intf_table
	#BUG hole here.   If magic starts first intf_table will stay []
	try:
		message = receiver.fetch(timeout=1)
		received = message.content 
		msg_list = received.split(',')
		if msg_list[0] == 'up':
			intf_table = intf_up(msg_list, intf_table, session)
			print 'Up event received:', intf_table
			session.acknowledge()
			return intf_table
		elif msg_list[0] == 'down':
			intf_table = intf_down(msg_list, intf_table, eth4Queue, eth5Queue)
			print 'Down event received:', intf_table
			session.acknowledge()	
			return intf_table
		else:  
			print "freakout"
	except Empty:
		print 'no change'
		return intf_table
	except MessagingError,m:
		print m
	else:
		print received 


#main()
lb_connection = Connection(broker_local) # initiate connection to localhost broker
try:
	lb_connection.open() #open connection via the lb_connection object
	session = lb_connection.session() #create session under the lb_connection
	receiver = session.receiver("agie_inbound_control") # create base receiver for the AGIE control queue
	sender_local = session.sender('amq.direct') #create base sender to the local broker via the direct exchange
	sender_app1 = session.sender('app1') #create sender that sends to app1 queue via amq.direct
	receiver_d = session.receiver("agie_inbound_data") # create base receiver that gets messages from AGIE data queue
except MessagingError,m:
	print m

while True:
	print 'Checking for control message actions'
	intf_table = intf_change(intf_table) #runs through the network interface detection and management code
	print 'Checking for data message actions'
	last_intf = data_msg_mover(intf_table, sender_local, receiver_d, last_intf, eth4Sender, eth5Sender) #moves messages between queues
	#need to add the pusher that moves messages from the interface outbound queues to the remote brokers. 
