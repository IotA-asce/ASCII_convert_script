this is not yet a complete project

images, frames need to be seperated from the video and then processed by the python script and joined together by any third party software as of now.

to seperate the frames i've used VLC media players tools

the python script uses the pillow library to process the images, an additional feature to auto detect the number of frames in any sub directory (to be processed) is yet to be implemeted
    the number of image input is to be set manually as of now

the frames are joined using Windows video editor, yes you read it right, 'Windows video editor'. (working on a python script to automate the same)

I tried to complete the project in java in my first attempt but was unable to maintain performance


Algorithm ->
    the grayscale of individual pixel data is analysed for the brightness and a char value is assigned to it, ' ' for rbg(0, 0, 0) and '$' for rbg(255, 255, 255)
    since all the pixels are mapped and converted to their char counterpart which taked up a lot more pixel as compared to a single pixel, the original image is to be scaled down to obtain legible ASCII counterpart
    the font color is set according to the rgb of the pixel

            ----IotA