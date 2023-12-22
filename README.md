# Image Steganography
This project was submitted to University of Mumbai as a partial requirement for the fulfillment of Mini Project 2B (CSM501). It utilizes Least Significant Bit (LSB) method to encode a payload into an image.

## Features of `imgstegano.py`
- Allows you to encode / hide a text or a file of any type (even a zip file) into an image.
- If the text or file to be encoded it too large, it automatically resizes the image to fit the payload size.
- Also allows you to set a password on the encoded payload and encrypts it using AES.
- The decoder automatically identifies the type of the payload and whether it is encrypted and prompts the user accordingly.
- Very intuitive User Interface.

## How to run
- Install the packages in `requirements.txt` globally or in a virtual environment.
- Run the program using the command `python imgstegano.py`.

## How to use
- ### Encoding
	- Select the `Encode` tab on the top.
	- Choose the target image.
	- Select the type of payload (text / file),
	- Enter the payload.
	- Set a password (leave empty of not required).
	- Click on the Encode button.
- ### Decoding
	- Select the `Decode` tab on the top.
	- Choose the image with encoded payload.
	- Click on the Decode button. 

## Limitations
- The program is only tested with the following image types:
	- Color Scheme: 8 Bit RGB, RGBA, CMYK
	- Format: PNG, BMP
- Works well with small payload (< 64 KB).

## Screenshots
![TextOP](https://github.com/zohaib2002/Image-Steganography/assets/68106969/1b807f50-92b5-4e94-9a59-b977588abfb8)


## Credits for Test Images
- `venice.png` : [Sea Glass](https://www.facebook.com/photo.php?fbid=10152367139309042)
