import time
import threading
import socket
import thread
import urllib2

mobile_list = {}

file = open("IP.txt", "r")
rpid = file.readline()
host = file.readline()
port = 12345

def factorial(num):
	sum = 1
	for x in xrange(1,num):
		sum *=(x+1)
	return sum

def processing(load):
	print "Processing Load..."
	time.sleep(15)
	value = factorial(int(load))
	print value
	return value

def spl_return_req(connection1,value,t0):
	fresult = processing(int(z))
	connection1.send(value)
	t1 = time.time() - t0
	print "Time taken to process:  " + str(t1)+ " ms"
	connection1.send(t1)

def convert_procid(term):
	term = term.strip('()')
	t = term.split(',')	
	q = t[0].strip('\'')
	p = q+':'+t[1].strip()
	return p

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((host, port))
s.listen(10)

def mobile_recv(ss, procid):
	while 1:
		try:
			data = ss.recv(1024)
		except:
			break
		if not data:
			break
		t0 = time.time()
		thread.start_new_thread( spl_return_req, (ss,data,t0, ) )
	print("Disconnected...Removing Request...")
	ss.close()
	thread.exit()

while True:
	mobile_conn, ipaddr = s.accept()			# mobile connection
	procid = convert_procid(str(ipaddr))
	print ('Recieved connection from mobile with IP - ', procid)
	mobile_conn.send('Dear Mobile user, you are connected!')
	mobile_list[procid] = mobile_conn
	try:
		thread.start_new_thread( mobile_recv, (mobile_conn,procid,) )
	except:
		print "Error: unable to start thread"
