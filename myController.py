import socket
import thread

res_index_dict = {0:0, 1:0, 2:0}						#the dictionary for net loads of each rpi
print res_index_dict
servingtable = [[] for _ in range(3)]
task_dict = {}
connection_dict = {}
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
host = '169.254.218.170' 			#ip of controller
port = 20000
s.bind((host, port))
s.listen(5)

while True:
	c, rpi_addr = s.accept()
	print ('Got connection from RPI with IP - '+str(rpi_addr))
	c.send('Dear cloudlet, you are connected to controller.')
	data = c.recv(1024)
	rpi = int(data)
	print "Rpi id is - " + str(rpi)
	connection_dict[rpi] = c

	try:
		thread.start_new_thread( receive, (c,rpi,) )
	except:
		print ("Error: unable to start thread")

def receive(c, rpi):
	while 1:
		try:
			data = c.recv(1024)
		except:
			break
		if not data:
			break
		decision(data)
	c.close()
	print "closed connection with RPI - "+str(rpi)
	print "Exiting thread..."
	print"-----------------------------------------------------"
	thread.exit()

def decision(data_recv):

	arr = data_recv.split(':')
	control = arr[0]

	if control == '1':										
		load0 = res_index_dict[0]
		load1 = res_index_dict[1]
		load2 = res_index_dict[2]
		conn_rpi = res_index_dict[int(arr[1])]
		min_load = min(load0, load1, load2)

		if min_load == conn_rpi:
			add_req(arr[1], arr[2], arr[3], arr[1], arr[4])
			connection_dict[int(arr[1])].send('2:'+arr[1]+':'+arr[2]+':'+arr[3]+':'+arr[1]+':'+arr[4])

		elif min_load == load0:
			add_req(arr[1], arr[2], arr[3], '0', arr[4])
			connection_dict[0].send('2:'+arr[1]+':'+arr[2]+':'+arr[3]+':0:'+arr[4])

		elif min_load == load1:
			add_req(arr[1], arr[2], arr[3], '1', arr[4])
			connection_dict[1].send('2:'+arr[1]+':'+arr[2]+':'+arr[3]+':1:'+arr[4])	
		
		elif min_load== load2:
			add_req(arr[1], arr[2], arr[3], '2', arr[4])
			connection_dict[2].send('2:'+arr[1]+':'+arr[2]+':'+arr[3]+':2:'+arr[4])

	elif control == '3':													#3 - if load of a request changes		3:rpi:ip:port:new_load
		found = False
		res_index_dict[int(arr[2])] -= int(arr[6])
		connection_dict[int(arr[1])].send('4:'+ arr[1] + ':' + arr[2]+':'+arr[3]+':'+arr[5])
		# for key, value in task_dict.iteritems():
		# 	if key.startswith(arr[2]+':'+arr[3]):
		# 		found = True
		# 		sorpi = value
		# 		break
		# if found:
		# 	connection_dict[int(sorpi)].send('4:'+ arr[2]+':'+arr[3]+':'+arr[4])
		# else:
		# 	print "No such request present."

	elif control == '5':													
		res_index_dict[int(arr[1])] -= int(arr[2])

	elif control == '6':		
		found = False
		for key, value in task_dict.iteritems():
			if key.startswith(arr[2]+':'+arr[3]):
				found = True
				star = key
				break
		task_dict.pop(star)				

def add_req(rpi, ip, port, srpi, data):
	serpi = int(srpi)
	index = ip+':'+port +':'+ srpi
	task_dict[index] = int(rpi)
	res_index_dict[int(srpi)] += int(data)
	print "\nres_index_dict:"
	print res_index_dict
	print "-----------------------------------------------------------------------------"
