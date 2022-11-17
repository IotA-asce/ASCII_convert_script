import os
import time
import sys
from PIL import Image, ImageDraw, ImageFont
import climage

import math

# chars = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "[
#         ::-1]  # ASCII values, can add if better gradient is found
# charArray = list(chars)
charArray = [' ', '`', '¨', '·', '¸', '.', '-', "'", ',', '¹', ':', '_', '¯', '~', '¬', '¦', ';', '¡', '!', '÷', '*',
             '*', 'ı', '|', '+', '<', '>', '/', '=', '»', '«', 'ì', 'í', 'ï', 'i', '^', 'º', 'r', 'L', 'ª', '®', 'ī',
             'ĩ', 'î', 'ĭ', 'l', '¿', 'J', '×', 'v', '?', 'c', 'į', ')', 'Ĺ', 'Ŀ', '(', 'Y', 'T', 'Ļ', 'Ľ', 'ĺ', '7',
             '¤', 't', 'ľ', 'ŀ', 'Ł', '}', '{', 'F', 'ċ', 'ļ', 's', 'ĸ', 'Ý', '[', 'x', 'ć', 'z', 'ç', '1', 'I', ']',
             'ł', 'j', 'Ĵ', 'C', 'y', 'V', '£', '5', '2', 'f', '3', 'ĉ', 'č', 'n', 'Ì', 'Í', 'İ', '¢', 'ĵ', 'U', 'X',
             'Ć', 'Z', 'Ċ', 'S', 'u', 'Ï', 'Þ', 'P', 'Į', 'Ç', 'K', 'A', 'o', 'ÿ', 'ý', 'a', 'e', '4', 'Ĭ', 'E', 'Î',
             'Č', 'Ĉ', 'Ī', 'Ĩ', 'Ú', 'Ù', 'ń', 'ņ', 'ŉ', 'k', 'Ü', 'Á', 'À', 'ù', 'ú', 'ü', '¥', 'ė', 'w', 'H', 'È',
             'É', 'Ä', 'Å', 'ö', 'Ė', 'ò', 'G', 'ó', 'Ķ', 'ä', 'Û', 'á', 'à', 'Ą', 'ë', 'é', 'è', 'h', 'ą', 'ę', 'Ë',
             'å', 'ñ', 'ň', 'Ę', 'O', 'Ă', '$', 'Â', 'û', 'Ĕ', 'Ā', 'Ě', 'Ê', 'Ã', 'Æ', 'R', 'ā', 'D', 'ē', 'ķ', 'õ',
             '½', 'Ē', 'p', 'ã', 'ô', 'ă', 'Ġ', 'â', 'ĕ', '9', '6', 'ê', 'ě', 'q', '¼', 'Ĳ', 'm', 'N', '%', '0', 'Ģ',
             'ħ', 'b', 'Ò', 'Ó', '#', 'ø', 'd', 'Ö', 'Ĥ', 'Ğ', '§', 'Ĝ', 'W', 'M', 'B', 'æ', 'Ð', 'Đ', 'Q', 'Ô', '©',
             'Ń', 'Ħ', '8', 'ĥ', 'Õ', 'g', 'Ď', 'Ņ', 'ĳ', 'đ', 'ß', 'þ', 'Ň', 'ð', '@', 'Ŋ', 'Ñ', '¾', 'ġ', 'Ø', 'ģ',
             'ď', 'ğ', '&', 'ĝ']


charLength = len(charArray)
interval = charLength / 256

# scaleFactor = 0.2                               # the scale of the output image after converting the original's,
# read first comment
oneCharWidth = 10
oneCharHeight = 18


def getChar(inputInt):
    return charArray[math.floor(inputInt * interval)]


oi_name = "FrameOut"  # output image file name prefix
ii_name = "Frame"  # input file name prefix

loaderState = False


def listFilesFromAssets():
    listOfImages = os.listdir("./assets/input/")
    index = 1

    print("Available choice -> \n")
    printDivider()
    for image in listOfImages:
        print("[%d] - %s" % (index, image))
        index += 1
    printDivider()
    index = int(input("Enter the choice : "))
    return listOfImages[index - 1]


def convertImage(input_name, scaleFactor=0.2, bgBrightness=30):
    im = Image.open("./assets/input/" + input_name)
    # text_file = open(".txt", "w")  # can obtain txt output, but frame rate is not constant

    fnt = ImageFont.truetype('C:\\Windows\\Fonts\\lucon.ttf', bgBrightness)  # trust me on this, modify if necessary

    width, height = im.size
    im = im.resize((int(scaleFactor * width), int(scaleFactor * height * (oneCharWidth / oneCharHeight))),
                   Image.NEAREST)
    width, height = im.size
    pix = im.load()

    outputImage = Image.new('RGB', (oneCharWidth * width, oneCharHeight * height),
                            color=(bgBrightness, bgBrightness, bgBrightness))  # (0,0,0) for polychromatic images
    d = ImageDraw.Draw(outputImage)

    loaderState = True
    for i in range(height):
        for j in range(width):
            loader(((i * width) + j), (height * width))
            r, g, b = pix[j, i]
            h = int(r / 3 + g / 3 + b / 3)
            pix[j, i] = (h, h, h)
            # text_file.write(getChar(h))
            d.text((j * oneCharWidth, i * oneCharHeight), getChar(h), font=fnt, fill=(r, g, b))

        # text_file.write('\n')
    output_name = "./assets/output/OUTPUT_" + "bgBrightness_" + str(bgBrightness) + "_factor_" + str(
        scaleFactor) + "_" + input_name
    outputImage.save(output_name)
    # count = count + 3                   # adjust to the number of frames per frame of the original video,
    # i took one frames for 3


def printDivider():
    print("\n_________________________________________________")


def loader(count, total):
    sys.stdout.write("\r" + "processing - " + str((count / total) * 100) + "\t%")
    # print()


def __main():
    imageName = listFilesFromAssets()

    print(imageName)
    printDivider()
    print("Factor of conversion (higher factor will lead to larger image size and greater render time))")
    factor = float(input("Factor input [0-1] - "))
    printDivider()
    print("BG color will be black if not modified")
    choice = input("If it is required to change the output [y/N] - ")
    print()
    if choice.capitalize() == "Y":
        bgBrightness = int(input("Enter brightness factor [range-range] - "))
        convertImage(imageName, factor, bgBrightness)
    else:
        convertImage(imageName, factor)
    # loader(15,100)


__main()
