# -*- coding:utf-8 -*-
import sys, socket, time, thread
from PyQt4 import QtGui, QtCore
from os.path import getsize
import os

from Msg import HANDSHAKE, handshake_toForm, SHEET, sheet_toForm
from Logic import cmd_valid, cmd_reply, get_code, find_idle_port, btou




class Client():
	def __init__(self):
		self.PROCESSING = True

		self.SERVER_HOST = "127.0.0.1"
		self.SERVER_PORT = 51423

		self.MY_HOST = "127.0.0.1"
		self.MY_PORT = ""
		self.ALL_HOST = ""

		self.Status={}
		self.Status["login"]= False
		self.Status["update"]= 0
		self.Status["openwin"] = {}

		self.NameList = {}
		self.Username = ""
		self.BEAT_TIME = 10

		self.find_MY_PORT()
		self.thread_for_p2p()	

		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.connect((self.SERVER_HOST, self.SERVER_PORT))

		self.Buffer = []
		self.fileLock = thread.allocate_lock()
		self.fileLock2 = thread.allocate_lock()

		self.SendCode = {}
		self.RecvCode = {}
		self.ReplyCode = {}

	def find_MY_PORT(self):
		s = socket.socket()
		localhost = '127.0.0.1'
		for myport in range(51000, 60000):
			try:
				s.bind((localhost, myport))
				s.close()
				self.MY_PORT = str(myport)
				break;
			except socket.error, e:
				continue;	

	def login_handle(self, clientsock):
		sheet_str = clientsock.recv(1024)
		allsheet = sheet_str.split("CS1.0")

		for sheet_str in allsheet[1:]:
			sheet = sheet_toForm(sheet_str)
		
		if sheet.Cmd=="STATUS":
			if sheet.Arg=="1":
				self.Status["login"] = True
			else:
				self.Status["login"] = False

	def make_sheet(self, cmd):
		sheet = SHEET()
		if cmd[0]=="LOGIN":
			self.Username = cmd[1]
			sheet.fill(cmd[0], cmd[1])
			sheet.headAdd("Port", str(self.MY_PORT))
		elif cmd[0]=="GETLIST":
			sheet.fill(cmd[0])
		elif cmd[0]=="LEAVE":
			sheet.fill(cmd[0], self.Username)
		elif cmd[0]=="MESSAGE":
			sheet.fill(cmd[0], self.Username)
			msg = cmd[1]
			if len(cmd)>2:
				for content in cmd[2:]:
					msg = msg+" "+content
			sheet.fill_body(msg)
		elif cmd[0]=="P2PMESSAGE":
			sheet.Version = "P2P1.0"
			sheet.fill(cmd[0], self.Username)
			msg = cmd[2]
			if len(cmd)>3:
				for content in cmd[3:]:
					msg = msg+" "+content
			sheet.fill_body(msg)
		elif cmd[0]=="P2PFILE":
			sheet.Version = "P2P1.0"
			sheet.fill(cmd[0], self.Username, cmd[2])
			sheet.headAdd("Query", "1")
			code = get_code()
			self.SendCode[cmd[2]] = code
			sheet.headAdd("SendCode", code)
		elif cmd[0]=="P2PFILEACCEPT":
			sheet.Version = "P2P1.0"
			sheet.fill(cmd[0], self.Username, cmd[2])
			
			try:
				print "[109]", self.RecvCode
				print "[110]", cmd[2]
				print "[111]"
				sheet.headAdd("RecvCode", self.RecvCode[cmd[2]])

			except:
				sheet.headAdd("RecvCode", "00000000000000000000000000000000") # reply an wrong code

			code = get_code()
			self.ReplyCode[cmd[2]] = code
			sheet.headAdd("ReplyCode", code)

			fileport = find_idle_port()
			sheet.headAdd("FILEPORT", fileport)

			# new a thread to recv file
			file_thread = thread.start_new_thread(self.file_recv, (fileport, cmd[2],))


		sheet.headAdd("Content-Length", len(sheet.Body))
		date = time.strftime("%H:%M:%S@%Y-%m-%d", time.localtime())
		sheet.headAdd("Date", date)
		return sheet


	def file_recv(self, fileport, filepath):

		print "[136] file recv~~~"
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind((self.ALL_HOST, int(fileport)))
		sock.listen(1)

		filesock, fileaddr = sock.accept()
		path = filepath.split("/")
		path = path[-1]

		try:
			os.mkdir("./download/"+self.Username)
		except:
			i=0

		f = open("./download/"+self.Username+"/"+path, "wb")
		while 1:
			sheet_str = filesock.recv(1024)
			if not sheet_str: break

			print "[156]", sheet_str
			sheet = sheet_toForm(sheet_str)

			if sheet.Cmd=="P2PFILESEND":
				print "[100-1]"
				if sheet.Headline["CheckCode"]==self.ReplyCode[filepath]:
					print "[100-2]"
					msg = sheet.Body
					f.write(msg)

		f.close()
		sock.close()

		
		self.fileLock.acquire()	
		input = open("./buffer/"+self.Username+"/"+sheet.Arg, "a")
		input.write("["+sheet.Arg+"] " + " <finish receiving file: " + sheet.Arg2 + ">\n")
		input.close()
		self.fileLock.release()
		

	def thread_for_p2p(self):	
		print "[93] thread for p2p!"
		t_p2p = thread.start_new_thread(self.p2p_recv_station, ())

	def thread_for_handle(self):
		t = thread.start_new_thread(self.handle, (self.s,))

	def thread_for_beat(self):
		t_beat = thread.start_new_thread(self.beat_handle, (self.s,))
				
	def handle(self, clientsock):

		while 1:
			sheet_str = clientsock.recv(1024)
			allsheet = sheet_str.split("CS1.0")

			for sheet_str in allsheet[1:]:
				sheet = sheet_toForm(sheet_str)
				
				# STATUS ------------------------------------------------
				if sheet.Cmd=="STATUS":
					if sheet.Arg=="1":
						print "# LOGIN SUCCEED!"
						self.Status["login"] = True
					else:
						print sheet.Body
						self.Status["login"] = False

				# LIST --------------------------------------------------
				if sheet.Cmd=="LIST":
					self.update_NameList(sheet.Body)
					print "# current LIST:"
					self.print_NameList()

				# LEAVE -------------------------------------------------
				if sheet.Cmd=="LEAVE":
					if self.Username==sheet.Arg:
						self.Status["login"] = False

				# UPDATE ------------------------------------------------
				if sheet.Cmd=="UPDATE":
					if sheet.Arg2 == "1":
						sheet = self.make_sheet(["GETLIST"])
						clientsock.send(sheet.toStr())
					else:
						self.NameList[sheet.Arg][0] = False
						self.NameList[sheet.Arg][3] = None
						self.NameList[sheet.Arg][4] = False

					self.Status["update"]+=1
					self.Status["update"]%=10000


				# CSMESSAGE ----------------------------------------------
				if sheet.Cmd=="CSMESSAGE":
					if sheet.Arg!=self.Username:
						self.print_csmessage(sheet.Body, sheet.Arg)	

			self.PROCESSING = False

	def print_csmessage(self, csmsg, fromname):
		print "["+fromname+" ~> csmsg]:" + csmsg

		self.fileLock.acquire()	
		try:
			os.mkdir("./buffer/"+self.Username)
		except:
			i = 0 #do nothing

		input = open("./buffer/"+self.Username+"/"+fromname, "a")
		input.write("["+fromname+"] " + csmsg + "\n")
		input.close()
		self.fileLock.release()


	def update_NameList(self, list_body):
		#self.NameList = {}
		allline = list_body.split("\n")
		for item in allline:
			if item=="":
				break
			recd = item.split(" ")
			if(self.NameList.has_key(recd[0])):
				self.NameList[recd[0]][0] = True
				self.NameList[recd[0]][1] = recd[1]
				self.NameList[recd[0]][2] = recd[2]
			else:
				self.NameList[recd[0]] = [True, recd[1], recd[2], None, False]

	def print_NameList(self):
		print "[",    
		for i in self.NameList:
			if self.NameList[i][0]==True:
				print i + ".",
		print "]\n"


	def beat_handle(self, clientsock):
		global Status, Username
		cur_time = time.time()
		while self.Status["login"]:
			if time.time() - cur_time > self.BEAT_TIME:
				print "[173] beat_handle"
				cur_time = time.time()
				sheet = SHEET()
				sheet.fill("BEAT", self.Username)
				clientsock.send(sheet.toStr())
			else:
				time.sleep(1)


	def p2p_recv_station(self):
		p2p = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		p2p.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		p2p.bind((self.ALL_HOST, int(self.MY_PORT)))
		print "[193] I bind it~~~~~~~~~"
		p2p.listen(10)

		while 1:
			p2psock, p2paddr = p2p.accept()
			t_p2p_recv = thread.start_new_thread(self.p2p_recv, (p2psock, p2paddr))
		p2p.close()


	def p2p_recv(self, clientsock, clientaddr):

		# handshake ----------------------------------------------------
		handshake_str = clientsock.recv(1024)
		handshake = handshake_toForm(handshake_str)


		if handshake.Type != "MINET" :
			clientsock.close()
			#print "@@@ connection NOT come from Minet!"
		else:

			handshake = HANDSHAKE()
			handshake.Type = "MINET"
			handshake.Hostname = self.MY_HOST
			clientsock.send(handshake.toStr())
		# --------------------------------------------------------------
			
			while 1:
				sheet_str = clientsock.recv(1024)
				if not sheet_str: break

				print "[320]"
				print sheet_str
				print "[321]"
				sheet = sheet_toForm(sheet_str)
				msg = sheet.Body

				if sheet.Cmd=="P2PMESSAGE":
					self.fileLock.acquire()	
					input = open("./buffer/"+self.Username+"/"+sheet.Arg, "a")
					print "["+sheet.Arg+" ~> msg]" + msg
					input.write("["+sheet.Arg+"] " + msg + "\n")
					input.close()
					self.fileLock.release()
				elif sheet.Cmd=="P2PFILE":
					if sheet.Headline.has_key("Query") and sheet.Headline["Query"]=="1":
						self.RecvCode[sheet.Arg2] = sheet.Headline["SendCode"]
						print "[322] Recv file", sheet.toStr()
						input = open("./system/"+self.Username+"/"+"P2PFILE", "a")
						print "["+sheet.Arg+" ~> file]" + "<"+ sheet.Arg2 +">"
						input.write(sheet.Arg + " " + sheet.Arg2 + "\n")
						input.close()


						self.fileLock.acquire()	
						input = open("./buffer/"+self.Username+"/"+sheet.Arg, "a")
						input.write("["+sheet.Arg+"] " + " <try to send file: " + sheet.Arg2 + ">\n")
						input.close()
						self.fileLock.release()
				elif sheet.Cmd=="P2PFILEACCEPT":
					
					if self.SendCode.has_key(sheet.Arg2) and sheet.Headline["RecvCode"] == self.SendCode[sheet.Arg2]:
						file_send_thread = thread.start_new_thread(self.file_send, (self.NameList[sheet.Arg][1], sheet.Headline["FILEPORT"], sheet.Headline["ReplyCode"], sheet.Arg, sheet.Arg2, ))


				if self.NameList[sheet.Arg][0] == False:
					break

			clientsock.close()



	def file_send(self, ip, port, checkcode, toname, filepath):
			
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect((ip, int(port)))

		f = open(filepath, "rb")
		sheet = SHEET()
		sheet.fill("P2PFILESEND", self.Username, filepath)
		sheet.headAdd("CheckCode", checkcode)
		s = f.read(800)
		while s:
			sheet.fill_body(s)
			sock.send(sheet.toStr())
			print "[330] file send", sheet.toStr()
			s = f.read(800)
			time.sleep(0.1)
			

		f.close()
		sock.close()

		
		print "[386]---------------------"
		self.fileLock.acquire()	
		input = open("./buffer/"+self.Username+"/"+toname, "a")
		input.write("["+self.Username+"] " + " <finish sending file: " + filepath + ">\n")
		input.close()
		self.fileLock.release()


class MainWin(QtGui.QWidget):
	def __init__(self, client):
		QtGui.QWidget.__init__(self)
		self.width = 250
		self.height = 600
		self.space = 50
		self.gap = 25
		self.pic = 50

		self.client = client

		self.setWindowTitle(self.client.Username)
		self.setGeometry(0, 0, self.width, self.height) 

		self.myicon = []
		self.iconlist = []
		self.light = []

		self.client.thread_for_handle()
		self.client.thread_for_beat()
		
		time.sleep(0.1)
		self.update_tag = -1
		self.MyIcon()
		self.UpdateIcon()
		

		self.timer1=QtCore.QTimer()
		self.connect(self.timer1, QtCore.SIGNAL("timeout()"), self.UpdateIcon)
		self.timer1.start(1000)

		try:
			os.mkdir("./buffer/"+self.client.Username)
		except:
			i=0	#do nothing

		try:
			os.mkdir("./system/"+self.client.Username)
		except:
			print "# mkdir system file fail #"

	def MyIcon(self):
		button = QtGui.QPushButton(self)
		icon = QtGui.QIcon("icon/"+self.client.Username+".png")
		button.setIcon(icon)
		button.setGeometry(self.pic, self.pic, self.pic*1.5, self.pic*1.5)
		button.show()
		
		label = QtGui.QLabel(self.client.Username, self)
		label.setGeometry(self.pic*2.5, self.pic, self.width, self.pic*1.5)
		label.show()

		self.myicon = [button,label, icon]
		
		
		self.connect(button, QtCore.SIGNAL("clicked()"), lambda : self.DialogBox(self.client.Username) )
	

	def UpdateIcon(self):
		print "[339] <UpdateIcon> "
		if self.update_tag != self.client.Status["update"]:
			self.update_tag = self.client.Status["update"]
			count = 2.5
			for i in self.iconlist:
				i[0].close()
				i[1].close()

			self.iconlist = []
			print "[236]", self.client.NameList
			for i in self.client.NameList:
				if self.client.NameList[i][0]==True and i!=self.client.Username:
					button = QtGui.QPushButton(self)
					icon = QtGui.QIcon("icon/"+i+".png")
					button.setIcon(icon)
					button.setGeometry(self.pic, self.pic*count, self.pic, self.pic)
					button.show()
					
					label = QtGui.QLabel(i, self)
					label.setGeometry(self.pic*2.5, self.pic*count, self.width, self.pic)
					label.show()

					self.iconlist.append([button,label, icon, count])
					name = str(label.text())
					
					self.connect(button, QtCore.SIGNAL("clicked()"), lambda name=name: self.DialogBox(name) )
					
					count+=1

		self.check_msg_buffer()

	def check_msg_buffer(self):
		print "[372] <check_msg_buffer>"
		addr = "./buffer/"+self.client.Username+"/"

		for i in self.light:
			i.close()

		self.light = []
		for i in self.iconlist: 

			buffer_path = addr + str(i[1].text())
			try:
				buffer_size = getsize(buffer_path)
				if buffer_size!=0:
					print "[380] !!!!!!!!!!!! has msg"	
					red = QtGui.QLabel(self)
					red.setGeometry(self.pic-15, self.pic*i[3]+15, 10, 10)
					red.setPixmap(QtGui.QPixmap("./picture/red.png"))
					red.show()
					self.light.append(red)
			except:
				continue

				

	def DialogBox(self, name):
		print "[295] <DialogBoc>", name
		
		talk = TalkWin(self.client, name)
		talk.show()


	def closeEvent(self, event):
		
		cmd = ["LEAVE"]
		sheet = self.client.make_sheet(cmd)
		self.client.s.send(sheet.toStr())

		event.accept()




class TalkWin(QtGui.QWidget):
	def __init__(self, client, name):
		QtGui.QWidget.__init__(self)

		self.pic = 50
		self.name = name

		self.client = client
		self.client.Status["openwin"][name] = True

		self.isBcast = (self.name==self.client.Username)
		
		self.setWindowTitle('talking with '+self.name)
		if self.isBcast:
			self.setWindowTitle(self.name +" BROADCAST")
		self.setGeometry(0, 0, 590, 500) 

		self.read = QtGui.QTextEdit(self)
		self.read.setReadOnly(True)
		#content = self.get_buffer_content(self.name)
		#self.read.setText(content)
		self.read.setGeometry(10, 70, 570, 260)

		self.input = QtGui.QTextEdit(self)
		self.input.setGeometry(10, 350, 480, 120)

		self.enter = QtGui.QPushButton("Enter", self)
		self.enter.setGeometry(500, 397, 80, 80)
		self.enter.setShortcut('Ctrl+Return')

		self.file = QtGui.QPushButton("File", self)
		self.file.setGeometry(500, 347, 80, 50)

		self.logo = QtGui.QPushButton(self)
		self.icon = QtGui.QIcon("icon/"+self.name+".png")
		self.logo.setIcon(self.icon)
		self.logo.setGeometry(10, 10, self.pic, self.pic)

		label = QtGui.QLabel(self.name, self)
		label.setGeometry(self.pic+20, 10, 590, self.pic)


		self.enter.clicked.connect(lambda: self.send_msg( self.name, str(self.input.toPlainText()), self.read, self.input, self.isBcast) )
		self.file.clicked.connect(lambda: self.open_file_dialog(self.name))


		self.timer2=QtCore.QTimer()
		self.connect(self.timer2, QtCore.SIGNAL("timeout()"), self.get_buffer_content)
		self.timer2.start(1000)


	def open_file_dialog(self, name):
	
		fileDialog = QtGui.QFileDialog()
		fileDialog.setFileMode(1) 
		filename = fileDialog.getOpenFileName()

		filename = btou(str(filename))
		
		self.p2pfile(name, filename)
		

	def p2pfile(self, name, filename):
		
		print "[456]", filename
		cmd = ["P2PFILE", name, filename]
		sheet = self.client.make_sheet(cmd)

		if sheet.Version=="P2P1.0":
			if self.client.NameList.has_key(cmd[1]) and self.client.NameList[cmd[1]][0]==True:
				self.p2p_send_station(sheet.toStr(), cmd[1])                                                                    
			else:
				print "# your friend maybe OFFLINE. please check."


	def get_buffer_content(self):
		print "[500] get_buffer_content" 
		try:
			content_size = getsize("./buffer/"+self.client.Username+"/"+self.name)
			if content_size!=0:

				content = self.read.toPlainText()
				
				self.client.fileLock.acquire()
				file = open("./buffer/"+self.client.Username+"/"+self.name, "r")
				contents = file.readlines()
				file.close()
				file = open("./buffer/"+self.client.Username+"/"+self.name, "w")
				file.close()
				self.client.fileLock.release()
				

				for i in contents:
					content+=i

				self.read.setText(content)
				self.read.moveCursor(MoveEnd, True)
				self.read.show()
				print "[513] SHOW"
		except:
			i = 0 #do nothing
			#return ""

		try:
			print "[530]-1"
			content_size = getsize("./system/"+self.client.Username+"/"+"P2PFILE")
			print "[530]-2"
			if content_size!=0:
				
				print "[530]-3"
				file = open("./system/"+self.client.Username+"/P2PFILE", "r")
				contents = file.readlines()
				file.close()
				file = open("./system/"+self.client.Username+"/P2PFILE", "w")
				file.close()
				
				print "[530]-4"

				for i in contents:
					print "[542]-5", i
					i = i.split("\n")
					fromname, filename = i[0].split(" ")
					reply = QtGui.QMessageBox.question(self, 'Accept or Reject', "Do you accept file <"+filename+"> from '"+fromname+"'?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

					if reply == QtGui.QMessageBox.Yes:
						self.p2pfileaccept(fromname, filename)
					
		except:
			i = 0 #do nothing

	def p2pfileaccept(self, name, filename):

		cmd = ["P2PFILEACCEPT", name, filename]
		sheet = self.client.make_sheet(cmd)

		if sheet.Version=="P2P1.0":
			if self.client.NameList.has_key(cmd[1]) and self.client.NameList[cmd[1]][0]==True:
				self.p2p_send_station(sheet.toStr(), cmd[1])                                                                    
			else:
				print "# your friend maybe OFFLINE. please check."

	def send_msg(self, name, msg, read, input, isbcast):

		if isbcast:
			cmd_input = "MESSAGE "+str(msg)
			cmd = cmd_input.split(" ")
			sheet = self.client.make_sheet(cmd)
			self.client.s.send(sheet.toStr())

			content = read.toPlainText()+"\n"
			content+=("["+self.client.Username+"] " + msg + "\n")
			read.setText("<BroadCast>"+content)
			input.setText("")
		else:
			cmd = ["P2PMESSAGE", name, msg]
			sheet = self.client.make_sheet(cmd)

			if sheet.Version=="P2P1.0":
				if self.client.NameList.has_key(cmd[1]) and self.client.NameList[cmd[1]][0]==True:
					self.p2p_send_station(sheet.toStr(), cmd[1])                                                                    
				else:
					print "# your friend maybe OFFLINE. please check."

			content = read.toPlainText()+"\n"
			content+=("["+self.client.Username+"] " + msg + "\n")
			read.setText(content)
			input.setText("")


	def p2p_send_station(self, sheet_str, name):

		if self.client.NameList[name][4]==False:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((self.client.NameList[name][1], int(self.client.NameList[name][2])))
			self.client.NameList[name][3] = s

			handshake = HANDSHAKE()
			handshake.Type = "MINET"
			handshake.Hostname = self.client.MY_HOST
			s.send(handshake.toStr())

			handshake_reply_str = s.recv(1024)
			handshake_reply = handshake_toForm(handshake_reply_str)
			if handshake_reply.Type=="MINET":
				self.client.NameList[name][4] = True

		if self.client.NameList[name][4]:
			s = self.client.NameList[name][3]
			s.send(sheet_str)


	def closeEvent(self, event):
				
		del self.client.Status["openwin"][self.name]
		self.timer2.stop()
		event.accept()



class LoginDialog(QtGui.QDialog):
	def __init__(self, client, parent=None):
		QtGui.QDialog.__init__(self, parent)
		self.width = 250
		self.height = 320
		self.space = 50
		self.gap = 25
		self.client = client

		self.setWindowTitle('Edlin MINET v1.0')
		self.setGeometry(0, 0, self.width, self.height) 


		self.nameEdit = QtGui.QLineEdit("Username", self)
		self.nameEdit.setGeometry(self.space, self.height/2, self.width-2*self.space, self.gap)
		
		self.passEdit = QtGui.QLineEdit(self)
		self.passEdit.setGeometry(self.space, self.height/2+self.gap, self.width-2*self.space, self.gap)
		self.passEdit.setEchoMode(QtGui.QLineEdit.Password)

		self.loginBtn = QtGui.QPushButton("LOGIN", self)
		self.loginBtn.setGeometry(self.space*1.5, self.height/2+3*self.gap, self.width-3*self.space, self.gap)


		self.connect(self.loginBtn, QtCore.SIGNAL('clicked()'), self.ClickLogin)


	def ClickLogin(self):
		cmd = "LOGIN"+" "+str(self.nameEdit.text())
		cmd = cmd.split(" ")

		if cmd_valid(cmd):
			sheet = self.client.make_sheet(cmd)

			self.client.s.send(sheet.toStr())
			self.client.login_handle(self.client.s)

			if self.client.Status['login']: 
				self.client.Username = str(self.nameEdit.text())
 				self.accept()
 			else:
 				QtGui.QMessageBox.critical(self, 'Error', 'User is online')
		else: 
			QtGui.QMessageBox.critical(self, 'Error', 'User name or password error')


	def ReturnClient(self):
		return self.client




def login(client):
	# handshake ----------------------------------------------------
	handshake = HANDSHAKE()
	handshake.Type = "MINET"
	handshake.Hostname = client.SERVER_HOST
	client.s.send(handshake.toStr())
	handshake_str = client.s.recv(1024)
	handshake = handshake_toForm(handshake_str)
	# --------------------------------------------------------------

	if handshake.Type == "MIRO" and handshake.Hostname == client.SERVER_HOST:
		dialog = LoginDialog(client) 
		if dialog.exec_(): 
			client = dialog.ReturnClient()
			return True, client 
	return False, client 






if __name__ == '__main__': 
	app = QtGui.QApplication(sys.argv) 
	client = Client()

	flag, client = login(client)
	if flag: 
		win = MainWin(client) 
		win.show() 
		sys.exit(app.exec_()) 

