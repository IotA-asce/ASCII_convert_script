from PIL import Image, ImageDraw, ImageFont

import os
import sys
import time
import math

baseArr = [' ', '!', '*', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5',
           '6', '7', '8', '9', ':', ';', '<', '=', '>', '?', '@', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
           'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '[', ']', '^', '_', '`',
           'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
           'w', 'x', 'y', 'z', '{', '|', '}', '~', '¡', '¢', '£', '¤', '¥', '¦', '§', '¨', '©', 'ª', '«', '¬', '®', '¯',
           '·', '¸', '¹', 'º', '»', '¼', '½', '¾', '¿', 'À', 'Á', 'Â', 'Ã', 'Ä', 'Å', 'Æ', 'Ç', 'È', 'É', 'Ê', 'Ë', 'Ì',
           'Í', 'Î', 'Ï', 'Ð', 'Ñ', 'Ò', 'Ó', 'Ô', 'Õ', 'Ö', '×', 'Ø', 'Ù', 'Ú', 'Û', 'Ü', 'Ý', 'Þ', 'ß', 'à', 'á', 'â',
           'ã', 'ä', 'å', 'æ', 'ç', 'è', 'é', 'ê', 'ë', 'ì', 'í', 'î', 'ï', 'ð', 'ñ', 'ò', 'ó', 'ô', 'õ', 'ö', '÷', 'ø',
           'ù', 'ú', 'û', 'ü', 'ý', 'þ', 'ÿ', 'Ā', 'ā', 'Ă', 'ă', 'Ą', 'ą', 'Ć', 'ć', 'Ĉ', 'ĉ', 'Ċ', 'ċ', 'Č', 'č', 'Ď',
           'ď', 'Đ', 'đ', 'Ē', 'ē', 'Ĕ', 'ĕ', 'Ė', 'ė', 'Ę', 'ę', 'Ě', 'ě', 'Ĝ', 'ĝ', 'Ğ', 'ğ', 'Ġ', 'ġ', 'Ģ', 'ģ', 'Ĥ',
           'ĥ', 'Ħ', 'ħ', 'Ĩ', 'ĩ', 'Ī', 'ī', 'Ĭ', 'ĭ', 'Į', 'į', 'İ', 'ı', 'Ĳ', 'ĳ', 'Ĵ', 'ĵ', 'Ķ', 'ķ', 'ĸ', 'Ĺ', 'ĺ',
           'Ļ', 'ļ', 'Ľ', 'ľ', 'Ŀ', 'ŀ', 'Ł', 'ł', 'Ń', 'ń', 'Ņ', 'ņ', 'Ň', 'ň', 'ŉ', 'Ŋ']

percentageArr = []


def compute_percentage(image):
    width, height = image.size
    pixels = image.load()
    red, green, blue = 0, 0, 0
    totalPixel = width * height
    totalBlack = 0
    totalWhite = 0

    for i in range(height):
        for j in range(width):
            red, green, blue = pixels[j, i]
            if compute_average(red, green, blue) > 100:
                totalWhite += 1
            else:
                totalBlack += 1

    return totalWhite / totalPixel


def construct_percentage_arr():
    image_arr = []
    count = 0
    for i in baseArr:
        font = ImageFont.truetype('C:\\Windows\\Fonts\\lucon.ttf', 250)

        output_image = Image.new('RGB', (200, 250), color=(0, 0, 0))  # (0,0,0) for polychromatic images
        draw_image = ImageDraw.Draw(output_image)

        draw_image.text((25, 5), i, font=font, fill=(255, 255, 255))
        # output_image.save(f"./test/image_{count}_.jpg")
        count += 1

        image_arr.append(output_image)

    for image in image_arr:
        percentageArr.append(compute_percentage(image))

    # print(percentageArr)

    sorted_char_array = [x for _, x in sorted(zip(percentageArr, baseArr))]

    # percentage_arr = percentageArr.sort()
    print(sorted_char_array)
    print(percentageArr)

    # output_image.save("./test/image{}.jpg".format(i))


def compute_average(r, g, b):
    return math.floor((r + g + b) / 3)


# def construct_array() -> None:
#     print(len(baseArr))


# construct_array()
construct_percentage_arr()
