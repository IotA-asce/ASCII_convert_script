from PIL import Image, ImageDraw, ImageFont

import math

chars = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "[::-1]        # ASCII values, can add if better gradient is found
# chars = "#Wo- "[::-1]
charArray = list(chars)
charLength = len(charArray)
interval = charLength/256

scaleFactor = 0.2                               # the scale of the output image after converting the original's, read first comment
oneCharWidth = 10                               
oneCharHeight = 18

def getChar(inputInt):
    return charArray[math.floor(inputInt*interval)]

oi_name = "FrameOut"            # output image file name prefix
ii_name = "Frame"               # input file name prefix
count = 1

                                # set the number of frames to be extracted manually or add the dir list count method to automate
for i in range(0,2092):         # dont look at this, probably could have done better using mod or just dividing length
    if (count < 10):
        input_name = ii_name + "0000" + str(count) + ".png"
        output_name = oi_name + "0000" + str(count) + ".jpg"
    elif(count >= 10 and count < 100):
        input_name = ii_name + "000" + str(count) + ".png"
        output_name = oi_name + "000" + str(count) + ".jpg"
    elif(count >= 100 and count < 1000):
        input_name = ii_name + "00" + str(count) + ".png"
        output_name = oi_name + "00" + str(count) + ".jpg"
    elif(count >= 1000 and count < 10000):
        input_name = ii_name + "0" + str(count) + ".png"
        output_name = oi_name + "0" + str(count) + ".jpg"
    elif(count >= 10000 and count < 100000):
        input_name = ii_name + "" + str(count) + ".png"
        output_name = oi_name + "" + str(count) + ".jpg"

    text_file = open("100.txt", "w")        # can obtain txt output, but frame rate is not constant

    im = Image.open(input_name)

    fnt = ImageFont.truetype('C:\\Windows\\Fonts\\lucon.ttf', 15)   #trust me on this, modify if necessary

    width, height = im.size
    im = im.resize((int(scaleFactor*width), int(scaleFactor*height*(oneCharWidth/oneCharHeight))), Image.NEAREST)
    width, height = im.size
    pix = im.load()

    outputImage = Image.new('RGB', (oneCharWidth * width, oneCharHeight * height), color = (10, 10, 10))    # (0,0,0) for polychromatic images
    d = ImageDraw.Draw(outputImage)

    for i in range(height):
        for j in range(width):
            r, g, b = pix[j, i]
            h = int(r/3 + g/3 + b/3)
            pix[j, i] = (h, h, h)
            text_file.write(getChar(h))
            d.text((j*oneCharWidth, i*oneCharHeight), getChar(h), font = fnt, fill = (r, g, b))

        text_file.write('\n')

    outputImage.save(output_name)
    count = count + 3                   # adjust to the number of frames per frame of the original video, i took one frames for 3
