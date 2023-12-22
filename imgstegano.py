import tkinter as tk
from tkinter import ttk, filedialog
import tkinter.simpledialog as sd
import tkinter.messagebox as mb
from PIL import Image, ImageTk
import cv2
import numpy as np
import os
import math
from aes_encryption import AESCipher

integrityCheckString = 'abcde'
# This is used to check the integrity of the file after it is decrypted
# Used to identify if the password entered was correct / incorrect


def dataToBinary(data):
    'Converts string, bytes, NumPy array of Integers to Binary or list of bytes represented using strings'
    if type(data) == str:
        p = ''.join([format(ord(i), '08b')for i in data])
    elif type(data) == bytes or type(data) == np.ndarray:
        p = [format(i, '08b')for i in data]
    return p


def stuffBits(binaryData):
    'Adds a 0 after every 6 consecutive 1s (Bit Stuffing). And adds delimiter at the end of binary string data'
    bitCount = 0
    bitLength = len(binaryData)
    bitIndex = 0

    while (bitIndex < bitLength - 1):
        if binaryData[bitIndex] == '1':
            bitCount += 1

        if binaryData[bitIndex] == '0':
            bitCount = 0

        if bitCount == 6:
            bitCount = 0
            bitIndex += 1
            binaryData = binaryData[:bitIndex] + '0' + binaryData[bitIndex:]
            bitLength += 1

        bitIndex += 1

    binaryData += '01111111'
    return binaryData


def unstuffBits(binaryData):
    'Unstuffs bits from the biinary string and removes the delimiter'
    binaryData = binaryData[:-8]

    bitCount = 0
    bitLength = len(binaryData)
    bitIndex = 0

    while (bitIndex < bitLength - 1):
        if binaryData[bitIndex] == '1':
            bitCount += 1

        if binaryData[bitIndex] == '0':
            bitCount = 0

        if bitCount == 6:
            bitCount = 0
            binaryData = binaryData[:bitIndex+1] + binaryData[bitIndex+2:]
            bitLength -= 1

        bitIndex += 1

    return binaryData


def encode(fileMode, encodeImageFilePath, encodeData, encodedOutputPath, encodeCompress, dynamicRescaling, encodePassword):
    'Function implements LSB method to encode data into images'
    global integrityCheckString

    # Generate the Header
    binaryHeader = '000000'

    if encodeCompress:
        binaryHeader += '1'
    else:
        binaryHeader += '0'

    if encodePassword:
        binaryHeader += '1'
    else:
        binaryHeader += '0'


    binaryData = ''


    if fileMode:
        # Add filename to the header
        binaryHeader += dataToBinary(os.path.basename(encodeData))

        with open(encodeData, 'rb') as file:
            content = file.read()

            # Encryption on bytes read
            if encodePassword:

                # If password is provided (ecryption is to be applied)
                encodedByteList = []
                for byte in content:
                    # append is faster in python list than in numpy arrays (or += in strings)
                    encodedByteList.append(chr(int(byte)))

                encodedbyteString = integrityCheckString + ''.join(encodedByteList)

                cipher = AESCipher(encodePassword)
                encryptedbyteString = cipher.encrypt(encodedbyteString)

                binaryData = dataToBinary(encryptedbyteString)

            else:
                # No encryption
                byteStringList = dataToBinary(content)
                binaryData = ''.join(byteStringList)



    else:
        
        if encodePassword:
            # Encryption on text
            cipher = AESCipher(encodePassword)
            encodeData = integrityCheckString + encodeData
            encodeData = cipher.encrypt(encodeData)
        
        binaryData = dataToBinary(encodeData)


    
    # Stuffing hedaer and data seperately. Each will have a seperate delimiter
    binaryHeader = stuffBits(binaryHeader)
    binaryData = stuffBits(binaryData)   
    binaryData = binaryHeader + binaryData


    '''
    We did not go with numpy array of boolean values for binaryData since append is very slow in numpy
    and also since we are not doing any operations on the list.
    We did not go with list of True / False values as it will not have a significant increase in performance
    and will make the program much harder to read and interpret.
    '''
    
    
    image = cv2.imread(encodeImageFilePath)
    
    # Dyanmic Rescaling to store data
    dataLength = len(binaryData)
    imageBitLength = image.shape[0] * image.shape[1] * 3


    if dataLength >= imageBitLength:
        if dynamicRescaling:
            scalingFactor = math.sqrt(dataLength/imageBitLength)

            height = math.ceil(image.shape[0] * scalingFactor)
            width = math.ceil(image.shape[1] * scalingFactor)

            dim = (width, height)

            image = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
        else:
            mb.showinfo('Dynamic Rescaling', 'The data to be encoded is too large. Enable Dynamic Rescaling to scale the image to fit the data.')
            return -1

    
    dataIndex = 0

    # Modifying the Least Significant Bit of each component of each pixel to store bits of Binary Data
    for row in image:
        for pixel in row:

            if dataIndex >= dataLength:
                break
            if dataIndex < dataLength:
                pixel[0] = int(pixel[0] & 0b11111110) + int(binaryData[dataIndex])
                dataIndex += 1
            if dataIndex < dataLength:
                pixel[1] = int(pixel[1] & 0b11111110) + int(binaryData[dataIndex])
                dataIndex += 1
            if dataIndex < dataLength:
                pixel[2] = int(pixel[2] & 0b11111110) + int(binaryData[dataIndex])
                dataIndex += 1

    cv2.imwrite(encodedOutputPath, image)
    
    mb.showinfo('Encoding complete', f'Output generated: {encodedOutputPath}')



def decode(decodeImageFilePath, decodeDestination=''):
    global integrityCheckString

    compressed = False
    protected = False

    delimsFound = 0
    bitCount = 0
    
    binaryHeader = ''
    binaryData = ''

    readBitsList = []

    image = cv2.imread(decodeImageFilePath)


    # Reading the Least Significant Bit of each component of each pixel
    for row in image:

        # The reading stops when both the delimiters (header and data) are found
        if delimsFound == 2:
            break

        for pixel in row:
            b = pixel[0] & 1
            g = pixel[1] & 1
            r = pixel[2] & 1

            readBitsList.append(b)

            if b:
                bitCount += 1

                if bitCount == 7:
                    delimsFound += 1

                    # When the first delimiter is found, the data read is stored in binaryHeader
                    if delimsFound == 1:
                        binaryHeader = ''.join(map(str, readBitsList))
                        readBitsList = []

                    if delimsFound == 2:
                        break

            else:
                bitCount = 0


            readBitsList.append(g)

            if g:
                bitCount += 1

                if bitCount == 7:
                    delimsFound += 1

                    if delimsFound == 1:
                        binaryHeader = ''.join(map(str, readBitsList))
                        readBitsList = []

                    if delimsFound == 2:
                        break

            else:
                bitCount = 0

            
            readBitsList.append(r)

            if r:
                bitCount += 1

                if bitCount == 7:
                    delimsFound += 1

                    if delimsFound == 1:
                        binaryHeader = ''.join(map(str, readBitsList))
                        readBitsList = []

                    if delimsFound == 2:
                        break

            else:
                bitCount = 0
            
            
            
    binaryData = ''.join(map(str, readBitsList))
    binaryHeader = unstuffBits(binaryHeader)

    # Header is read to get the options
    if binaryHeader[6] == '1':
        compressed = True
    if binaryHeader[7] == '1':
        protected = True

    binaryHeader = binaryHeader[8:]

    byteHeader = [binaryHeader[i: i + 8] for i in range(0, len(binaryHeader), 8)]

    # Filename is extracted from the header
    fileName = ""
    for x in byteHeader:
        fileName += chr(int(x, 2))

    binaryData = unstuffBits(binaryData)

    byteStringList = [binaryData[i: i + 8] for i in range(0, len(binaryData), 8)]

    if fileName:
        # File Mode (encoded data is a file)
        byteData = []

        if protected:
            # If data is password protected (to be decrypted)
            encryptedDataList = []
            for byte in byteStringList:
                encryptedDataList.append(chr(int(byte, 2)))

            encryptedDataString = ''.join(encryptedDataList)

            password = sd.askstring("Password", "Enter Password")
            cipher = AESCipher(password)

            try:
                decryptedDataString = cipher.decrypt(encryptedDataString)
            except UnicodeDecodeError:
                mb.showerror("Error", "Incorrect Password!")
                return -1
            
            # try except blocks do not introduce a new scope

            if decryptedDataString[0:5] != integrityCheckString:
                mb.showerror("Error", "Incorrect Password!")
                return -1
            
            else:
                decryptedDataString = decryptedDataString[5:]
                for char in decryptedDataString:
                    byteData.append(ord(char))


        else:
            # No decryption
            for byte in byteStringList:
                byteData.append(int(byte, 2))

        byteData = bytearray(byteData)

        fullPath = os.path.join(decodeDestination, fileName)
        with open( fullPath , 'wb') as file:
            file.write(byteData)

        mb.showinfo('Decoding Complete', 'Output generated at: ' + fullPath)


    else:
        # Text Mode (encoded data is a message)
        if protected:
            # Password protected (decryption)
            encryptedDataList = []
            for x in byteStringList:
                encryptedDataList.append(chr(int(x, 2)))
            encryptedData = ''.join(encryptedDataList)

            password = sd.askstring("Password", "Enter Password")
            cipher = AESCipher(password)

            try:
                decryptedData = cipher.decrypt(encryptedData)
            except UnicodeDecodeError:
                mb.showerror("Error", "Incorrect Password!")
                return -1

            if decryptedData[0:5] != integrityCheckString:
                mb.showerror("Error", "Incorrect Password!")
                return -1
            
            else:
                decryptedData = decryptedData[5:]
                decodedTextBox.insert('1.0', decryptedData)


        else:
            # No password protection
            dataList = []
            for x in byteStringList:
                dataList.append(chr(int(x, 2)))
            data = ''.join(dataList)
            decodedTextBox.insert('1.0', data)


        decodedTextBox.pack(pady=5, padx=10)




'''
/////////////////////
GUI Code ///////////
///////////////////
'''




window = tk.Tk()
window.geometry("600x800")
window_height = 800

window.title("Image Encoder/Decoder")

# Global variables to store File Paths
encodeImageFilePath = ''
decodeImageFilePath = ''
encodeData = ''
decodeDestination = ''



def chooseImageEncode():
    'Handles chosing image to be encoded'
    
    global encodeImageFilePath

    filetypes = [("PNG files", "*.png"), ("All files", "*.*")]
    encodeImageFilePath = filedialog.askopenfilename(filetypes=filetypes)

    if encodeImageFilePath:
        # Scales the image to have 40% of window height
        image = Image.open(encodeImageFilePath)

        width, height = image.size
        maxHeight = int(window_height * 0.4)
        if height > maxHeight:
            width = int(width * (maxHeight / height))
            height = maxHeight

        image = image.resize((width, height))

        imageEncode = ImageTk.PhotoImage(image)
        imageBoxEncode.configure(image=imageEncode)
        imageBoxEncode.image = imageEncode # Setting a reference
        chooseImageButtonEncode.configure(text="Choose another image")


def chooseEncodeFile():
    'Handles chossing a file to be encoded in the selected image'

    global encodeData
    
    filetypes = [("All files", "*.*")]
    encodeData = filedialog.askopenfilename(filetypes=filetypes)

    if encodeData:
        fileLabel.configure(text=encodeData)


def outputDestinationChange():
    'Handles change in destination of output files generated after decoding'

    global decodeDestination
    
    decodeDestination = filedialog.askdirectory()

    if decodeDestination:
        destinationLabel.configure(text=f'Output File Destination: {decodeDestination}')


def chooseImageDecode():
    'Handles choosing the image to be decoded'

    global decodeImageFilePath
    
    filetypes = [("PNG files", "*.png"), ("All files", "*.*")]
    decodeImageFilePath = filedialog.askopenfilename(filetypes=filetypes)

    if decodeImageFilePath:
        # Scales the image to fit in 40% of window height
        image = Image.open(decodeImageFilePath)

        width, height = image.size
        maxHeight = int(window_height * 0.4)
        if height > maxHeight:
            width = int(width * (maxHeight / height))
            height = maxHeight

        image = image.resize((width, height))

        imageDecode = ImageTk.PhotoImage(image)
        imageBoxDecode.configure(image=imageDecode)
        imageBoxEncode.image = imageDecode # Setting a reference
        chooseImageButtonDecode.configure(text="Choose another image")


def onEncode():
    'Validates input and calls the encode method when the user clicks on the Encode button'

    global encodeImageFilePath, encodeData
  
    # Encode Parameters
    fileMode = False

    if not encodeImageFilePath:
        mb.showinfo('Select an Image', 'Select an image to encode data into')

    if encodeSubtabs.tab(encodeSubtabs.select(), 'text') == 'File':
        fileMode = True
        if not encodeData:
            mb.showinfo('No File Selected', 'Please select a file to encode in the image')
            return -1
    else:
        encodeData = textBox.get('1.0', 'end-1c')
        if not encodeData:
            mb.showinfo('Empty Message', 'Please enter a message to encode')

    encodedOutputPath = outputEntry.get()
    encodeCompress = compressionVar.get()
    dynamicRescaling = rescalingVar.get()

    encodePassword = passwordEntry.get()

    # Hide the Encode button and display "Encoding..." label
    encodeButton.pack_forget()
    encodingLabel.pack(pady=10)

    encode(fileMode, encodeImageFilePath, encodeData, encodedOutputPath, encodeCompress, dynamicRescaling, encodePassword)

    # Unhide the Encode button
    encodeButton.pack(pady=10)
    encodingLabel.pack_forget()

    
def onDecode():
    'Calls the decode method when the user clicks on Decode button'

    global decodeImageFilePath, decodeDestination

    if not decodeImageFilePath:
        mb.showinfo('Select an Image', 'Select an image to decode')
        return -1
    
    decodedTextBox.pack_forget()

    # Hide the Decode button and display "Decoding..." label
    decodeButton.pack_forget()
    decodingLabel.pack(pady=10)

    decode(decodeImageFilePath, decodeDestination)
   
    # Make the Decode button visible again
    decodingLabel.pack_forget()
    decodeButton.pack(pady=5)


# Create tabbed group with 2 tabs
tabs = ttk.Notebook(window)
tabs.pack(fill='both', expand=True)
tabs.enable_traversal()

# Create encode tab
encodeTab = ttk.Frame(tabs)
tabs.add(encodeTab, text="Encode")

imageBoxEncode = tk.Label(encodeTab)
imageBoxEncode.pack()

# Create choose image button and image box
chooseImageButtonEncode = tk.Button(encodeTab, text="Choose an Image", command=chooseImageEncode)
chooseImageButtonEncode.pack(pady=10)

# Create tabbed group with 2 tabs (File and Text)
encodeSubtabs = ttk.Notebook(encodeTab, height=100)
encodeSubtabs.pack()

# Create Text tab
textTab = ttk.Frame(encodeSubtabs)
encodeSubtabs.add(textTab, text="Text")

textBox = tk.Text(textTab)
textBox.pack(pady=10, padx=20)

# Create File tab
fileTab = ttk.Frame(encodeSubtabs)
encodeSubtabs.add(fileTab, text="File")

fileLabel = tk.Label(fileTab, text="No file chosen")
fileLabel.pack(pady=10)

browseButton = tk.Button(fileTab, text="Browse", command=chooseEncodeFile)
browseButton.pack(pady=10)

# Create password entry box
passwordFrame = tk.Frame(encodeTab)
passwordFrame.pack(side=tk.TOP, padx=5, pady=5)

passwordLabel = tk.Label(passwordFrame, text="Password:")
passwordLabel.pack(side=tk.LEFT)

passwordEntry = tk.Entry(passwordFrame, width=30)
passwordEntry.pack(side=tk.LEFT)


# Create output path entry
outputFrame = tk.Frame(encodeTab)
outputFrame.pack(side=tk.TOP, padx=5, pady=5)

outputLabel = tk.Label(outputFrame, text="Output:")
outputLabel.pack(side=tk.LEFT)

outputEntry = tk.Entry(outputFrame, width=30)
outputEntry.insert(0, 'out.png')
outputEntry.pack(side=tk.LEFT)

# Create compression and dynamic rescaling checkboxes

compressionVar = tk.BooleanVar()
compressionCheck = tk.Checkbutton(encodeTab, text="Compression", variable=compressionVar)
compressionCheck.pack(pady=10)

rescalingVar = tk.BooleanVar()
dynamicCheck = tk.Checkbutton(encodeTab, text="Dynamic Rescaling", variable=rescalingVar)
dynamicCheck.pack()

# Create encode button
encodeButton = tk.Button(encodeTab, text="Encode", command=onEncode)
encodeButton.pack(pady=10)

# Create Encoding Label
encodingLabel = tk.Label(encodeTab, text="Encoding...")

# Create decode tab
decodeTab = ttk.Frame(tabs)
tabs.add(decodeTab, text="Decode")

imageBoxDecode = tk.Label(decodeTab)
imageBoxDecode.pack()

# Create choose image button for decoding
chooseImageButtonDecode = tk.Button(decodeTab, text="Choose an Image", command=chooseImageDecode)
chooseImageButtonDecode.pack(pady=10)

decodedTextBox = tk.Text(decodeTab, height=5)

# Create decode destination path widget
destinationFrame = tk.Frame(decodeTab)
destinationFrame.pack(side=tk.TOP, padx=5, pady=5)

destinationLabel = tk.Label(destinationFrame, text="Output File Destination: Current Directory")
destinationLabel.pack(side=tk.LEFT)

changeButton = tk.Button(destinationFrame, text="Browse", command=outputDestinationChange)
changeButton.pack(side=tk.LEFT)

# Create decode button
decodeButton = tk.Button(decodeTab, text="Decode", command=onDecode)
decodeButton.pack(pady=10)

# Create Decoding Label
decodingLabel = tk.Label(decodeTab, text="Decoding...")



# Start main loop
window.mainloop()

