#!usr/bin/env python
#########################################################################
# Author:   Edlin (Lin Junhao)                                          #
# Date:     Nov.25, 2013                                                #
# Email:    edlinlink@qq.com                                            #   
#########################################################################


def handshake_toForm(msg):
	other = HANDSHAKE()
	try:
		other.Type, other.Hostname = msg.split(" ")
		other.Hostname, tmp = other.Hostname.split("\n")
		return other
	except:
		return other

def sheet_toForm(msg):
	print "[MSG--start]"
	print msg
	print "[MSG-end]"
	other = SHEET()
	allline = msg.split("\n");
	requestline = allline[0]

	requestline = requestline.split(" ")
	other.Version = "CS1.0"
	other.Cmd = requestline[1]
	if len(requestline) == 3:
		other.Arg = requestline[2]
	elif len(requestline) == 4:
		other.Arg = requestline[2]
		other.Arg2 = requestline[3]
		
	item = 1
	while(item < len(allline)):
		if allline[item] != "":
			print "[MSG]"+allline[item]+"[/MSG]"
			segname, value = allline[item].split(" ")
			other.headAdd(segname, value)
			item += 1
		else:
			'''
			item += 1
			#while(item < len(allline) and allline[item]!=""): #there will be an "" at the end
			while(item < len(allline) ): 
				other.Body = other.Body + allline[item]+"\n"
				item = item+1
			break
			'''

			for i in allline[item+1:-1]:
				other.Body = other.Body + i + "\n"
			if allline[-1]!="":
				other.Body = other.Body + allline[-1]
			break
#		item = item+1

	print "MSG==="
	print other.Body
	print "MSG+++"
	return other


class HANDSHAKE:
	def __init__(self):
		self.Type = ""
		self.Hostname = ""
	def toStr(self):
		return self.Type + " " + self.Hostname + "\n"


class SHEET:
	def __init__(self):
		self.Version = "CS1.0"
		self.Cmd = ""
		self.Arg = ""
		self.Arg2 = ""
		self.Headline = {}
		self.Body = ""
	def fill(self, cmd, arg="", arg2=""):
		self.Cmd = cmd
		self.Arg = arg
		self.Arg2 = arg2
	def fill_body(self, content):
		self.Body = content
	def toStr(self):

		if self.Arg == "":
			buf = self.Version + " " + self.Cmd + "\n"
		elif self.Arg2 == "":
			buf = self.Version + " " + self.Cmd + " " + self.Arg + "\n"
		else:
			buf = self.Version + " " + self.Cmd + " " + self.Arg + " " + self.Arg2 +  "\n"

		for item in self.Headline:
			buf = buf + item + " " + str(self.Headline[item]) + "\n"
		buf = buf + "\n"
		buf = buf + self.Body
		return buf
	def headAdd(self, h1, b1):
		self.Headline[h1] = b1


