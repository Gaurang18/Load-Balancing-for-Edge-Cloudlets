import socket
import thread
import math
from ControllerControls import * 
from affine_cipher import *

n = 5
task_dict = {}
connection_dict = {}
res_index_dict = {}
serving_queue = {}

M = 0.0
S = 0.15
mean = math.e**(M+(S*S)/2)				# math.lognormal mean
norm_mean = 1.0
base_latency = 0.15
show_enc = True

def normalize(x):
	return ((x/mean)*(norm_mean-base_latency)) + base_latency

def add_req(conn_rpid, process_id, serv_rpid, data):
	index = process_id
	task_dict[index] = int(conn_rpid)
	p = int(data)
	serv_rpid = serv_rpid.rstrip()
	if serving_queue[int(serv_rpid)] == 0:
		res_index_dict[int(serv_rpid)] += p
	else:
		res_index_dict[int(serv_rpid)] += (p + math.log(serving_queue[int(serv_rpid)]))
	serving_queue[int(serv_rpid)] += 1
	print "\nres_index_dict:"
	print res_index_dict
	print "-----------------------------------------------------------------------------"

def receive(c, rpi):
	while 1:
		try:
			data = c.recv(1024)
		except:
			break
		if not data:
			break
		#data = main_message(data,"D")
		decision(data)
	c.close()
	connection_dict.pop(int(rpi),None)
	res_index_dict.pop(int(rpi),None)
	print "closed connection with RPI - "+str(rpi)
	print "Exiting thread..."
	print"-----------------------------------------------------"
	thread.exit()

def decision(data_recv):
	data_recv = main_message(data_recv,"D")
	arr = data_recv.split(':')
	control = get_control(arr)
	num_rpid = len(connection_dict)
	
	if control == '1':
		min_load_rpid = min(res_index_dict, key = res_index_dict.get)
		min_load = res_index_dict[int(min_load_rpid)]
		conn_rpid_load = res_index_dict[int(get_conn_rpid(arr))]
		assigned_rpid = ""
		if min_load == conn_rpid_load:
			assigned_rpid = get_conn_rpid(arr)
			print "Min load is same as Conn rpi...assigned is connrpi as " + assigned_rpid
		else:
			assigned_rpid = str(min_load_rpid)
			print "Min load is NOT same as Conn rpi...assigned is minimum rpi as " + assigned_rpid
		#print "Actually assigned is " + assigned_rpid
		add_req(get_conn_rpid(arr), get_process_id(arr), assigned_rpid, get_load(arr).split("~")[1])
		mes = '2:'+ get_conn_rpid(arr) +':'+ get_process_id(arr) + ':' + assigned_rpid + ':' + get_load(arr)
		Encrypted = main_message(mes,"E")
		global show_enc
		if(show_enc):
			show_enc = False
			print("Encrypted Message : ", Encrypted)
		connection_dict[int(assigned_rpid)].send(Encrypted)	

	elif control == '3':
		if serving_queue[int(get_serving_rpid(arr))] != 1:
			res_index_dict[int(get_serving_rpid(arr))] = res_index_dict[int(get_serving_rpid(arr))] - math.log(serving_queue[int(get_serving_rpid(arr))]) + math.log(serving_queue[int(get_serving_rpid(arr))] - 1)
		serving_queue[int(get_serving_rpid(arr))] -= 1										
		res_index_dict[int(get_serving_rpid(arr))] -= int(get_load(arr).split("~")[1])
		if serving_queue[int(get_conn_rpid(arr))] == 0:
			res_index_dict[int(get_conn_rpid(arr))] = 0
		#print(connection_dict[int(get_conn_rpid(arr))])
		mes = '4::' + get_process_id(arr) + ':' + get_serving_rpid(arr) + ':' + get_result(arr) + ':' + get_load(arr) + ':' + get_processing_time(arr)
		mes_e = main_message(mes,"E")
		connection_dict[int(get_conn_rpid(arr))].send(mes_e)
		print "\nres_index_dict:"
		print res_index_dict
		print "-----------------------------------------------------------------------------"
	
	elif control == '5':
		if serving_queue[int(get_conn_rpid(arr))] != 1:
			res_index_dict[int(get_conn_rpid(arr))] = res_index_dict[int(get_conn_rpid(arr))] - math.log(serving_queue[int(get_conn_rpid(arr))]) + math.log(serving_queue[int(get_conn_rpid(arr))] - 1)
		serving_queue[int(get_conn_rpid(arr))] -= 1														
		res_index_dict[int(get_conn_rpid(arr))] -= int(get_return_load(arr).split("~")[1])
		if serving_queue[int(get_conn_rpid(arr))] == 0:
			res_index_dict[int(get_conn_rpid(arr))] = 0

		print "\nres_index_dict:"
		print res_index_dict
		print "-----------------------------------------------------------------------------"

	elif control == '6':
		star = ""		
		found = False
		for key, value in task_dict.iteritems():
			if key.startswith(get_process_id(arr)):
				found = True
				star = key
				break
		if star in task_dict:
			task_dict.pop(star)
		else:
			print "Key not found...Cannot Remove."

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
host = '169.254.218.170'
port = 20000
s.bind((host, port))
s.listen(n)
print "Awaiting Connection from Cloudlets..."

while True:
	c, rpi_addr = s.accept()
	print 'Got connection from RPI with IP - '+str(rpi_addr)
	c.send('This Cloudlet is connected to the Controller')
	data = (c.recv(1024)).rstrip()
	rpi = int(data)
	print "Rpi id is - " + str(rpi)
	connection_dict[rpi] = c
	res_index_dict[rpi] = 0
	serving_queue[rpi] = 0
	try:
		thread.start_new_thread( receive, (c,rpi,) )
	except:
		print ("Error: unable to start thread")