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
This has been covered in great detail on [my blog](https://h0mbre.github.io/Image_Based_C2_PoC/)

## Usage
Please consult [my blog post on Dali](https://h0mbre.github.io/Image_Based_C2_PoC/) before trying to use it. All testing was performed with 2560x1440 `PNG` files.

### What You Will Need
- Please consult the Imgur API documentation and read the Terms of Service for API applications
- Obtain a Client-ID by registering your application
- Obtain a Bearer token by creating an authenticated account and tying it to your API client
- Configure MySQL to accept credentialed logins (just because you can access MySQL as root on Kali doesn't mean it's been configured!)

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
