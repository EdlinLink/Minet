import sys, socket, time, thread
from PyQt4 import QtGui, QtCore

from Msg import HANDSHAKE, handshake_toForm, SHEET, sheet_toForm
from Logic import cmd_valid, cmd_reply




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

		self.NameList = {}
		self.Username = ""
		self.BEAT_TIME = 10

		self.find_MY_PORT()

		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.connect((self.SERVER_HOST, self.SERVER_PORT))


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
			
		sheet.headAdd("Content-Length", len(sheet.Body))
		date = time.strftime("%H:%M:%S@%Y-%m-%d", time.localtime())
		sheet.headAdd("Date", date)
		return sheet


	def thread_for_handle(self):
		t = thread.start_new_thread(self.handle, (self.s,))

	def thread_for_beat(self):
		print "[95] !!!"
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
						print_csmessage(sheet.Body, sheet.Arg)	

			self.PROCESSING = False


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






class MainWin(QtGui.QWidget):
	def __init__(self, client):
		QtGui.QWidget.__init__(self)
		self.width = 250
		self.height = 600
		self.space = 50
		self.gap = 25
		self.pic = 50

		self.client = client

		self.setWindowTitle('Edlin MINET v1.0')
		self.setGeometry(0, 0, self.width, self.height) 

		self.iconlist = []

		self.client.thread_for_handle()
		self.client.thread_for_beat()
		
		time.sleep(0.1)
		self.update_tag = -1
		self.UpdateIcon()
		


		self.timer1=QtCore.QTimer()
		self.connect(self.timer1, QtCore.SIGNAL("timeout()"), self.UpdateIcon)
		self.timer1.start(1000)


	
	def UpdateIcon(self):

		if self.update_tag != self.client.Status["update"]:
			self.update_tag = self.client.Status["update"]
			count = 1
			for i in self.iconlist:
				i[0].close()
				i[1].close()

			self.iconlist = []
			print "[236]", self.client.NameList
			for i in self.client.NameList:
				if self.client.NameList[i][0]==True:
					print "[238]", i
					button = QtGui.QPushButton(self)
					icon = QtGui.QIcon("icon/"+i+".png")
					button.setIcon(icon)
					button.setGeometry(self.pic, self.pic*count, self.pic, self.pic)
					button.show()
					
					label = QtGui.QLabel(i, self)
					label.setGeometry(self.pic*2.5, self.pic*count, self.width, self.pic)
					label.show()

					button.clicked.connect(lambda: self.DialogBox( str(label.text()) ))
					#self.connect(button, QtCore.SIGNAL("clicked()"), self.DialogBox)
					
					self.iconlist.append([button,label,icon])
					count+=1
			

	def DialogBox(self, name):
		print "[252] conversation~~~~", name
		talk = QtGui.QMainWindow(self) 

		talk.setWindowTitle('talking with '+name)
		talk.setGeometry(0, 0, 590, 500) 

		read = QtGui.QTextEdit(talk)
		read.setReadOnly(True)
		read.setGeometry(10, 70, 570, 260)

		input = QtGui.QTextEdit(talk)
		input.setGeometry(10, 350, 480, 120)

		enter = QtGui.QPushButton("Enter", talk)
		enter.setGeometry(500, 397, 80, 80)

		file = QtGui.QPushButton("File", talk)
		file.setGeometry(500, 347, 80, 50)

		logo = QtGui.QPushButton(talk)
		icon = QtGui.QIcon("icon/"+name+".png")
		logo.setIcon(icon)
		logo.setGeometry(10, 10, self.pic, self.pic)

		label = QtGui.QLabel(name, talk)
		label.setGeometry(self.pic+20, 10, 590, self.pic)

		talk.show()

	def closeEvent(self, event):
		
		cmd = ["LEAVE"]
		sheet = self.client.make_sheet(cmd)
		self.client.s.send(sheet.toStr())

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

