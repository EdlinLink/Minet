#!/usr/bin/env python
#########################################################################
# Author:   Edlin (Lin Junhao)                                          #
# Date:     Nov.25, 2013                                                #
# Email:    edlinlink@qq.com                                            #   
#########################################################################


import socket, sys, thread, time
from Msg import HANDSHAKE, handshake_toForm, SHEET, sheet_toForm
from Logic import cmd_valid, cmd_reply

PROCESSING = True

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 51423

MY_HOST = "127.0.0.1"
MY_PORT = ""
ALL_HOST = ""

Status={}
Status["login"]= False

NameList = {}
Username = ""
BEAT_TIME = 10


def update_NameList(list_body):
	global NameList
	NameList = {}
	allline = list_body.split("\n")
	for item in allline:
		if item=="":
			break
		recd = item.split(" ")
		if(NameList.has_key(recd[0])):
			NameList[recd[0]][0] = True
			NameList[recd[0]][0] = recd[1]
			NameList[recd[0]][0] = recd[2]
		else:
			NameList[recd[0]] = [True, recd[1], recd[2], None, False]


def print_NameList():
	global NameList
	print "[",	  
	for i in NameList:
		if NameList[i][0]==True:
			print i + ".",
	print "]\n"

def print_csmessage(csmsg, fromname):
	print "["+fromname+" ~> msg]:" + csmsg
	

def make_sheet(cmd):
	global Username
	sheet = SHEET()
	if cmd[0]=="LOGIN":
		Username = cmd[1]
		sheet.fill(cmd[0], cmd[1])
		print "[64]"
		print MY_PORT
		sheet.headAdd("Port", str(MY_PORT))
	elif cmd[0]=="GETLIST":
		sheet.fill(cmd[0])
	elif cmd[0]=="LEAVE":
		sheet.fill(cmd[0], Username)
	elif cmd[0]=="MESSAGE":
		sheet.fill(cmd[0], Username)
		msg = cmd[1]
		if len(cmd)>2:
			for content in cmd[2:]:
				msg = msg+" "+content
		sheet.fill_body(msg)
	elif cmd[0]=="P2PMESSAGE":
		sheet.Version = "P2P1.0"
		sheet.fill(cmd[0], Username)
		msg = cmd[2]
		if len(cmd)>3:
			for content in cmd[3:]:
				msg = msg+" "+content
		sheet.fill_body(msg)
		
	sheet.headAdd("Content-Length", len(sheet.Body))
	date = time.strftime("%H:%M:%S@%Y-%m-%d", time.localtime())
	sheet.headAdd("Date", date)
	return sheet


def login_handle(clientsock):
	global Status
	sheet_str = clientsock.recv(1024)
	allsheet = sheet_str.split("CS1.0")

	for sheet_str in allsheet[1:]:
		sheet = sheet_toForm(sheet_str)
		
		if sheet.Cmd=="STATUS":
			if sheet.Arg=="1":
				print "# LOGIN SUCCEED!"
				Status["login"] = True
			else:
				print sheet.Body
				Status["login"] = False

def beat_handle(clientsock):
	global Status, Username

	cur_time = time.time()
	while Status["login"]:
		if time.time() - cur_time > BEAT_TIME:
			cur_time = time.time()
			sheet = SHEET()
			sheet.fill("BEAT", Username)
			clientsock.send(sheet.toStr())
		else:
			time.sleep(1)


def handle(clientsock):
	global Statue, Username, PROCESSING

	while 1:
		sheet_str = clientsock.recv(1024)
		allsheet = sheet_str.split("CS1.0")

		for sheet_str in allsheet[1:]:
			sheet = sheet_toForm(sheet_str)
			
			# STATUS ------------------------------------------------
			if sheet.Cmd=="STATUS":
				if sheet.Arg=="1":
					print "# LOGIN SUCCEED!"
					Status["login"] = True
				else:
					print sheet.Body
					Status["login"] = False

			# LIST --------------------------------------------------
			if sheet.Cmd=="LIST":
				update_NameList(sheet.Body)
				print "# current LIST:"
				print_NameList()

			# LEAVE -------------------------------------------------
			if sheet.Cmd=="LEAVE":
				if Username==sheet.Arg:
					Status["login"] = False

			# UPDATE ------------------------------------------------
			if sheet.Cmd=="UPDATE":
				if sheet.Arg2 == "1":
					sheet = make_sheet(["GETLIST"])
					clientsock.send(sheet.toStr())
				else:
					NameList[sheet.Arg][0] = False
					NameList[sheet.Arg][3] = None
					NameList[sheet.Arg][4] = False

			# CSMESSAGE ----------------------------------------------
			if sheet.Cmd=="CSMESSAGE":
				if sheet.Arg!=Username:
					print_csmessage(sheet.Body, sheet.Arg)	

		PROCESSING = False


def main():

	find_MY_PORT()

	global Username, NameList, PROCESSING
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((SERVER_HOST, SERVER_PORT))

	# handshake ----------------------------------------------------
	handshake = HANDSHAKE()
	handshake.Type = "MINET"
	handshake.Hostname = SERVER_HOST
	s.send(handshake.toStr())
	handshake_str = s.recv(1024)
	handshake = handshake_toForm(handshake_str)
	# --------------------------------------------------------------

	if handshake.Type != "MIRO" or handshake.Hostname != SERVER_HOST:
		print "@@@ connection NOT from Miro!"
	else:
		print "# please enter 'LOGIN Username':"

		# Thy to login ------------------------------
		while not Status["login"]:
			print "$",
			cmd_input = raw_input()
			cmd = cmd_input.split(" ")

			if cmd_valid(cmd) and cmd[0]=="LOGIN":
				sheet = make_sheet(cmd)
				s.send(sheet.toStr())
				login_handle(s)
			elif cmd_valid(cmd) and cmd[0]=="LEAVE":
				break
			else:
				print "# command ERROR!"
		# -------------------------------------------
				

		# have login and wait for command -----------
		if Status["login"]:
			t = thread.start_new_thread(handle, (s,))
			t_beat = thread.start_new_thread(beat_handle, (s,))
			t_p2p = thread.start_new_thread(p2p_recv_station, ())

		while Status["login"]:
			if PROCESSING:
				time.sleep(0.1)
			else:
				print "["+Username+"]$",
				cmd_input = raw_input()
				cmd = cmd_input.split(" ")
				if cmd_valid(cmd):
					sheet = make_sheet(cmd)
					if sheet.Version=="CS1.0":
						s.send(sheet.toStr())
						PROCESSING = True
					elif sheet.Version=="P2P1.0":
						if NameList.has_key(cmd[1]) and NameList[cmd[1]][0]==True:
							p2p_send_station(sheet.toStr(), cmd[1])
						else:
							print "# your friend maybe OFFLINE. please GETLIST to check."
						# send to another thread to handle the p2p communication
				else:
					print "# command ERROR!"
		# -------------------------------------------	

	s.close()


def p2p_recv_station():
	p2p = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	p2p.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	p2p.bind((ALL_HOST, int(MY_PORT)))
	p2p.listen(10)

	while 1:
		p2psock, p2paddr = p2p.accept()
		t_p2p_recv = thread.start_new_thread(p2p_recv, (p2psock, p2paddr))
	p2p.close()


def p2p_recv(clientsock, clientaddr):

	# handshake ----------------------------------------------------
	handshake_str = clientsock.recv(1024)
	handshake = handshake_toForm(handshake_str)


	if handshake.Type != "MINET" :
		clientsock.close()
		#print "@@@ connection NOT come from Minet!"
	else:

		handshake = HANDSHAKE()
		handshake.Type = "MINET"
		handshake.Hostname = MY_HOST
		clientsock.send(handshake.toStr())
	# --------------------------------------------------------------
		
		while 1:
			sheet_str = clientsock.recv(1024)
			if not sheet_str: break

			sheet = sheet_toForm(sheet_str)
			msg = sheet.Body
			print "["+sheet.Arg+" ~> msg]" + msg
			
			if NameList[sheet.Arg][0] == False:
				break

		clientsock.close()
	
# may have bug: s is reset by other sender, have a try to check the result.

def p2p_send_station(sheet_str, name):

	if NameList[name][4]==False:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((NameList[name][1], int(NameList[name][2])))
		NameList[name][3] = s

		handshake = HANDSHAKE()
		handshake.Type = "MINET"
		handshake.Hostname = MY_HOST
		s.send(handshake.toStr())

		handshake_reply_str = s.recv(1024)
		handshake_reply = handshake_toForm(handshake_reply_str)
		if handshake_reply.Type=="MINET":
			NameList[name][4] = True

	if NameList[name][4]:
		s = NameList[name][3]
		s.send(sheet_str)

def find_MY_PORT():
	global MY_PORT
	s = socket.socket()
	for myport in range(51000, 60000):
		localhost = '127.0.0.1'
		try:
			s.connect((localhost, myport))
			s.close()
			continue;	
		except socket.error, e:
			MY_PORT = str(myport)
			break;

main()
