import time
import threading
import socket
import thread
import urllib2
import math
import sys
from affine_cipher import *
# multiple things at once for one mobile user

mobile_list = {}

file = open("IP.txt", "r")
rpid = file.readline()
Cloudlet_IP = file.readline()
Cloudlet_Port = 12345

Controller_IP = "169.254.218.170"
Controller_Port = 20000

EXP = math.exp(1)

req_start_time = 0.0

def get_control(arr):
	return arr[0]

def get_conn_rpid(arr):
	return arr[1]

def get_process_id(arr):
	return arr[2] + ':' + arr[3]

def get_serv_rpid(arr):
	return arr[4]

def get_data(arr):
	return arr[5].rstrip()

def get_result(arr):
	return arr[5].rstrip()

def get_processing_time(arr):
	return arr[7].rstrip()

def convert_process_id(term):
	term = term.strip('()')
	t = term.split(',')	
	q = t[0].strip('\'')
	p = q+':'+t[1].strip()
	return p

def process_user_fn(req1, req2):
	x = float(req1)
	f = req2
	return int(eval(f)*10000)/10000.0

def process_intersection(function,req): #function is the f we want to find its root and x0 and x1 are two random starting points
	x_n = -5
	x_n1 = 1000
	while True:
		x_n2 = x_n1-(function(x_n1, req)/((function(x_n1, req)-function(x_n, req))/(x_n1-x_n)))
		if abs(x_n2 - x_n1)<0.00001 :
			return round(x_n2, 2)
		x_n=x_n1
		x_n1=x_n2

def intersection_function(x, req):
	return eval(req)

def process_exp(req):						# this function calculates the last 4 digits and 9 decimal places of
	z = req
	res = 1								# the mathematical function e^(1000000^(load)).
	for x in xrange(1, int(z)+1):
		for x in xrange(1, 1000001):
			res *= EXP
			res = res % 10000
	return res

def spl_return_req(mobile_conn, controller_conn, load, rpid):										# connection variables are to mobile and controller respectively	
	req =  load.split("~")
	print "Processing Task..."																		# if the serving_rpi is same as the connection_rpi send the result directly to the mobile user
	start = time.clock()
	if req[0] == "1":
		value = process_user_fn(req[1], req[2])																# Returning results
	elif req[0] == "2":
		value = process_intersection(intersection_function, req[2])																	# Returning results
	elif req[0] == "3":
		value = process_exp(req[1])																	# Returning results
	else:
		value = "Error"																	# Returning results
	end = time.clock()																			
	print "Processing Finished..."
	#Latency Calculations...
	global req_start_time
	processing_time = int((end - start)*10000)/10000.0
	req_end_time = time.clock()
	total_latency = int((req_end_time - req_start_time)*10000)/10000.0
	print "Processing Time = " + str(processing_time) + " seconds"
	# print "Total Latency = " + str(total_latency) + " seconds"
	mobile_conn.send("--------------------------------------------------------\n")
	mobile_conn.send("Result = " + str(value) +"\n")
	mobile_conn.send("Your request was served at RPI - "+str(rpid))			
	mobile_conn.send("Processing Time = " + str(processing_time) + " seconds\n")
	# mobile_conn.send("Total Latency = " + str(total_latency) + " seconds\n")
	mobile_conn.send("--------------------------------------------------------\n")
	z = '5:'+ rpid + ':' + load
	z_e = main_message(z,"E")
	controller_conn.send(z_e)

def return_req(controller_conn, process_id, load, serv_rpid, connect_rpid):
	req =  load.split("~")
	print "Processing Task..."																		# if the serving_rpi is same as the connection_rpi send the result directly to the mobile user
	start = time.clock()
	if req[0] == "1":
		value = process_user_fn(req[1], req[2])																# Returning results
	if req[0] == "2":
		value = process_intersection(intersection_function, req[2])																	# Returning results
	if req[0] == "3":
		value = process_exp(req[1])																	# Returning results
	end = time.clock()																			
	print "Processing Finished..."
	processing_time = int((end - start)*10000)/10000.0
	z = '3:'+ connect_rpid + ':' + process_id + ':' + str(load) + ':' + str(value) + ':' + serv_rpid + ':' + str(processing_time)
	z_e = main_message(z,"E")
	controller_conn.send(z_e)

def controller_recv(controller_conn):        # parallel thread to listen requests from Controller
	while True:
		try:
			req = controller_conn.recv(1024)
		except:
			print "Controller is Shut Down...Exiting..."
			sys.exit(0)
		if req == '':
			continue
		decryption = main_message(req,"D")
		req_split = decryption.split(':') 
		#print decryption
		control = get_control(req_split)
		if control == '2':
			print get_data(req_split)
			if get_conn_rpid(req_split) == get_serv_rpid(req_split):
				thread.start_new_thread( spl_return_req, (mobile_list[get_process_id(req_split)], controller_conn, get_data(req_split), get_serv_rpid(req_split), ))
			else:	
				thread.start_new_thread( return_req, (controller_conn, get_process_id(req_split), get_data(req_split), get_serv_rpid(req_split), get_conn_rpid(req_split),) )
		elif control == '4':
			# Latency Calculations...
			# here the processing time is to be from  the serving RPI , 4 is only for the connection RPI.
			# so use the get_processing_time() to get the one received in req_split[]
			req_end_time = time.clock()
			global req_start_time
			processing_time = get_processing_time(req_split)
			total_latency = int((req_end_time - req_start_time)*10000)/10000.0
			print "Processing Time = " + str(processing_time) + " seconds"
			# print "Total Latency = " + str(total_latency) + " seconds"
			mobile_list[get_process_id(req_split)].send("--------------------------------------------------------\n")
			mobile_list[get_process_id(req_split)].send("Result = " + get_result(req_split) +"\n")		# Returning results
			mobile_list[get_process_id(req_split)].send("Your request was served at RPI - " + str(get_serv_rpid(req_split)) + "\n")			
			mobile_list[get_process_id(req_split)].send("Processing Time = " + str(processing_time) + " seconds\n")
			# mobile_list[get_process_id(req_split)].send("Total Latency = " + str(total_latency) + " seconds\n")
			mobile_list[get_process_id(req_split)].send("--------------------------------------------------------\n")
		else:
			print("Unknown Code!")

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((Cloudlet_IP, Cloudlet_Port))
s.listen(5)

controller_conn = socket.socket()
controller_conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
	print "Trying to connect to Controller..."
	controller_conn.connect((Controller_IP, Controller_Port))
except:
	print "Unable to Connect...Run Cloudlet again"
	sys.exit(1)
try:
	controller_conn.send(rpid)
	data = controller_conn.recv(1024)
	print(data)
except:
	print "Lost Connection with Controller...Run Cloudlet again"
	sys.exit(2)
try:
	thread.start_new_thread( controller_recv, (controller_conn,) )
except:
	print "Error: Unable to start thread"
	sys.exit(3)

def introduction():
	z = "\n--------------------------------------------------------\nChoose a Feature:\n1. Evaluate your function (f(x)) at a value of x\n2. Find a root of your equation\n3. Find e^(1000000*x)modulo 10000\n--------------------------------------------------------\n"
	return z

def mobile_recv(mobile_conn, process_id):
	mobile_conn.send(introduction())
	while 1:
		try:
			data = mobile_conn.recv(1024).rstrip()
		except:
			break
		if not data:
			break
		req = ""
		if data.rstrip() == "1":
			z = "\nFormat:\nmath.e**x -> e^x\nmath.pow(x, y) -> x^y\nmath.log(x) -> ln(x)\nmath.log(x, y) -> log(x)base-y\n"
			mobile_conn.send(z)
			z = "Enter your Function in python syntax (only x as variable):\n"
			mobile_conn.send(z)
			try:
				data1 = mobile_conn.recv(1024).strip()
			except:
				mobile_conn.send("Try Again.\n")
				mobile_conn.send(introduction())
				break
			z = "Enter x:\n"
			mobile_conn.send(z)
			try:
				data2 = mobile_conn.recv(1024).strip()
			except:
				mobile_conn.send("Try Again.\n")
				mobile_conn.send(introduction())
				break
			req = "1~" + data2+"~"+data1
		elif data == "2":
			z = "\nFormat:\nmath.e**x -> e^x\nmath.pow(x, y) -> x^y\nmath.log(x) -> ln(x)\nmath.log(x, y) -> log(x)base-y\n"
			mobile_conn.send(z)
			z = "Enter your Function in python syntax (only x as variable):\n"
			mobile_conn.send(z)
			try:
				data = mobile_conn.recv(1024).strip()
			except:
				mobile_conn.send("Try Again.\n")
				mobile_conn.send(introduction())
				break
			req = "2~" + str(len(data)/10) + "~" + data
		elif data == "3":
			z = "Enter Integer x:\n"
			mobile_conn.send(z)
			try:
				data = mobile_conn.recv(1024).strip()
			except:
				mobile_conn.send("Try Again.\n")
				mobile_conn.send(introduction())
				break
			req = "3~" + data
		else:
			mobile_conn.send("Invalid Request Type...Try Again.\n")
			mobile_conn.send(introduction())
			break
		print "Full Request is " + req
		z = '1:' + rpid+':' + process_id+':' + req
		controller_conn.send(main_message(z,"E"))
		mobile_conn.send(introduction())
	print "Disconnected..."
	print "Removing Request..."
	z = '6'+':'+ rpid + ':' + process_id
	controller_conn.send(main_message(z,"E"))
	mobile_conn.close()
	thread.exit()

while True:
	mobile_conn, ipaddr = s.accept()			# mobile connection
	process_id = convert_process_id(str(ipaddr))
	print 'Recieved connection from mobile with IP - ' + process_id
	mobile_conn.send('Dear Mobile user, You are Connected\n')
	mobile_list[process_id] = mobile_conn
	try:
		thread.start_new_thread( mobile_recv, (mobile_conn, process_id,) )
	except:
		print "Error: Unable to start thread"
		mobile_conn.send("Mobile User, try to Connect Again...")
		continue