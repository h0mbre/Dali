## Dali
Dali is the server-side half of an image-based C2 channel which utilizes Imgur to host images and task agents. From Dali you can:
- Create stego'd images with commands
- Create albums for agent responses
- Create agent entities for tracking
- Create/issue tasking for agents
- Retrieve responses from agents

## Status/Utility
Dali was created as a proof-of-concept and is **bring your own implant (BYOI)**. For my testing purposes, I created a crude `agent.py` script to simulate a proper implant in the wild. You will need to hardcode the URL of your uploaded tasking images in order to use the script to respond to tasking. 

Dali has not been rigorously tested for bugs, I'm sure they exist! Issue a pull-request if you want or just ping me on Twitter.

## Stego Method
This has been covered in great detail on [my blog](https://h0mbre.github.io/Image_Based_C2_PoC/). Shortly, it uses the differences in the least significant bit of each red-pixel value to create 8-digit binary numbers that are harcoded to a dictionary which holds key-value pairs for Base64 encoding/decoding.

## Usage
Please consult [my blog post on Dali](https://h0mbre.github.io/Image_Based_C2_PoC/) before trying to use it. All testing was performed with 2560x1440 `PNG` files.

### What You Will Need
- Please consult the Imgur API documentation and read the Terms of Service for API applications
- Obtain a Client-ID by registering your application
- Obtain a Bearer token by creating an authenticated account and tying it to your API client
- Configure MySQL to accept credentialed logins (just because you can access MySQL as root on Kali doesn't mean it's been configured!)

### Main Menu
Here is the main-menu and the available options. The CLI behaves similarly to Metasploit, which I took inspiration from.

[![asciicast](https://asciinema.org/a/jQbdCGdCzZzDkIUNdNVjJ9YNw.svg)](https://asciinema.org/a/jQbdCGdCzZzDkIUNdNVjJ9YNw)

### Album Module
Since unauthenticated `PNG` files can only be `1MB`, if you anticipate a long repsonse from the agent, such as a `ps -aux` or a `netstat -ano`, use an authenticated album. Otherwise, the image will be cropped and the response snipped if it is too long. 
```
Options:        Example Value:
- Auth-Type     Unauth or Auth
- Title         Test Album
- Client-ID     <Client-ID for your API Application>
- Bearer-Token  <Auth token associated with your API Application>
```
  
[![asciicast](https://asciinema.org/a/YmyjgMgTPbOVHgKrvEuTGYM9b.svg)](https://asciinema.org/a/YmyjgMgTPbOVHgKrvEuTGYM9b)

### Image Module
This module will create a stego'd image with a hidden command, response album, and token of some sort for the agent to respond. The agent will get the command, run it, store the output in a response image, post the response image in the response album using the token.

Again, response is driven by size of the response image. `Short` enables unauthenticated responses from the agent, `Long` enables authenticated responses. `No` response can be used for things like sending reverse shells. 
```
Options:        Example Value:
- Command       uname -a
- Response      Short
- Base-Image    example.png
- New-Filename  output.png
- Client-ID     <Client-ID for your API Application>
- Bearer-Token  <Auth token associated with your API Application>
- Album-ID      1
```

[![asciicast](https://asciinema.org/a/hBNQIm7TpZjf1mSNAY5H76cje.svg)](https://asciinema.org/a/hBNQIm7TpZjf1mSNAY5H76cje)

### Agent Module
This module will create an agent for tasking. All this module is intended to do is organize taskings and tie images to certain agents. In a real framework, this would compile and create an implant. Theoretically, the agent would be using a combination of title-words and tags to find the tasking image, so that's what we set here. 
```
Options:      Example Value:
- Title       test title
- Tags        test,dali,cool
```

[![asciicast](https://asciinema.org/a/xrdfzsnqmCh1e63fJkIi8SKuU.svg)](https://asciinema.org/a/xrdfzsnqmCh1e63fJkIi8SKuU)

### Tasking Module
This module actually initializes tasking by tying an agent to an image and then uploading the image to the public Imgur gallery using an auth token. This module will update the tasked-agent's status to `TASKED` and will create a MySQL entry reflecting that the tasking is `PENDING`.
```
Options:          Example Value:
- Tasking-Image   1
- Title           Test Title
- Tags            test,dali,cool
- Agent           1
- Bearer-Token    <Auth token associated with your API Application>
```

[![asciicast](https://asciinema.org/a/JOQTAqAZJVcdsxheitwDw82K8.svg)](https://asciinema.org/a/JOQTAqAZJVcdsxheitwDw82K8)

### Response Module
The `List Responses` command will show available responses from agents. `Get Response <Agent-ID>` command will retrieve the actual response payload from the agent.

Once a response is received, this module also deletes the tasking image in the Imgur Gallery and updates the agent and tasking entries appropriately in MySQL. 

[![asciicast](https://asciinema.org/a/Q5v6vsJWQsMtqRPOii4xpVCmp.svg)](https://asciinema.org/a/Q5v6vsJWQsMtqRPOii4xpVCmp)

### List/Delete Modules:
These modules are available so that you if you need some information for a module, you can exit that module, visit this module, retrieve the information and then enter back into your previous module to complete your work. The commands are pretty self explanatory and snippets of its use have been included in the asciinema videos above. 

Delete will actually clear MySQL data so as far as Dali is concerned, that entity no longer exists. 

## House-Keeping
