import time
import threading
import socket
import thread

mobile_conn = {}
rpid = '0'

if(rpid == '0'):
	host = '192.168.42.1' #ip of raspberry pi
elif (rpid == '1'):
	host = '192.168.52.1' #ip of raspberry pi
elif (rpid == '2'):
	host = '192.168.62.1' #ip of raspberry pi
port = 12345

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((host, port))
s.listen(5)

while True:
	mobile_conn, ipaddr = s.accept()			# mobile connection
	print ('Recieved connection from mobile with IP - ',addr)
	mobile_conn.send('Dear Mobile user, you are connected!')
	procid = convert_procid(str(ipaddr))
	mobile_list[procid] = mobile_conn
	try:
		thread.start_new_thread( mobile_recv, (mobile_conn,procid,) )
	except:
		print "Error: unable to start thread"

def convert_procid(term):
	term = term.strip('()')
	t = term.split(',')			#t[1] is port
	q = t[0].strip('\'')
	p = q+':'+t[1].strip()
	return p

def mobile_recv(ss, procid):  
	                 # thread corresponding to each mobile user
	while 1:
		try:
			data = ss.recv(1024)
		except:
			break
		if not data:
			break
		print(data)
		submit(procid,data)
	print("Disconnected...Removing Request...")
	controller_conn.send('6'+':'+ rpid + ':' + procid)	
	ss.close()
	thread.exit()

def submit(process_id, data):
	controller_conn.send('1:' + rpid+':' + process_id+':' + data)

def controller_recv(controller_conn):        # parallel thread to listen requests from cotroller
	while True:
		global mobile_conn
		ser_data= controller_conn.recv(1024)
		if ser_data == '':
			continue
		ser_data_parts = ser_data.split(':')
		process_id = ser_data_parts[2]+':'+ser_data_parts[3]
		
		if ser_data_parts[0] == '2':
			if ser_data_parts[4] == ser_data_parts[2]:
				z = (ser_data_parts[5].rstrip())
				fresult = processing(int(z))
				thread.start_new_thread( spl_return_req, (mobile_conn,controller_conn, z, fresult,int(ser_data_parts[4]), ) )
				
			else:
				z = (ser_data_parts[5].rstrip())
				fresult = processing(int(z))
				thread.start_new_thread( return_req, (controller_conn, process_id,z, fresult, int(ser_data_parts[4]), int(ser_data_parts[1]),) )
		
		elif ser_data_parts[0] == '4':
			mobile_conn[process_id].send(ser_data_parts[4].rstrip())

		else:
			print("Unknown Code!")

def processing():
	value = invert(int(load[process_id]))
	print value
	time.sleep(15)
	return value

def spl_return_req(connection1,connection2, load, value,rpid):						             # if the serving_rpi is same as the connection_rpi send the result directly to the mobile user
	connection1.send(value)
	z = '5:'+ rpid+':'+load
	connection2.send(z)

def return_req(connection, process_id,load,value,servrpid,connect_rpid):                                       # if not, then send req control type 5 to the controller with format 5:rpid(serving):mip:port:result
		z = '3:'+ connect_rpid +servrpid+':'+process_id+':'+value + ':' + load
		connection.send(z)


Host1 = '169.254.218.170'    # controller ip
Port1 = 20000              # The same port as used by the server
controller_conn = socket.socket()
controller_conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
	controller_conn.connect((Host1, Port1))
	print('Trying to connect to controller...')
	controller_conn.send(rpid)
	data = controller_conn.recv(1024)					# receives "you are conneted"
	print(data)
	thread.start_new_thread( controller_recv, (controller_conn,) )

except socket.timeout():
	print('timeout')