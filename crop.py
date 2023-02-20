from PIL import Image, ImageDraw, ImageFont
import os.path, sys
import pandas as pd

im_loc = "../../"
dirs = os.listdir(im_loc)
eans = pd.read_excel("ean_codes.xlsx")

def crop():
    for item in dirs:
        f, e = item.split('.')
        if ((e == 'png') & (int(f) in list(eans["EAN"]))):
            im = Image.open(im_loc + '/' + item)
            w, h = im.size
            
            # crop image
            imCrop = im.crop((0, h-181, w, h))

            # Create a new image with whitespace above the original image
            new_im = Image.new('RGB', (w, 181+50), (255, 255, 255))

            # Paste the original image onto the new image
            new_im.paste(imCrop, (0, 50))

            # add text to the image
            draw = ImageDraw.Draw(new_im)
            text = eans[eans["EAN"] == int(f)]["Text"].values[0]
            font = ImageFont.truetype("Squartiqa4F.ttf", 22) # Change font and size as needed
            textwidth, textheight = draw.textsize(text, font)
            draw.text(((w - textwidth) / 2, 10), text, font=font, fill=(0, 0, 0))
            
            new_im.save(f'cropped_eans/{f}.png', "PNG", quality=100)

crop()
