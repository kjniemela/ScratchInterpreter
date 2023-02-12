from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
##from PIL import Image
import subprocess
import os.path

inkscape_path = "C:/Program Files/Inkscape/inkscape.exe"

def svg_to_png(path, name):

    drawing = svg2rlg(path)

    # args = [
    #     inkscape_path,
    #     "--without-gui",
    #     "-f", path,
    #     "--export-area-page",
    #     "-w", str(drawing.width*2),
    #     "-h", str(drawing.height*2),
    #     "--export-png=" + name+".png"
    # ]
    # subprocess.run(args)

    renderPM.drawToFile(drawing, name+".png", fmt='PNG')

    return name+".png"
    
##    drawing = svg2rlg(path)
##    renderPM.drawToFile(d, name+".png", fmt="PNG", configPIL={'transparent':white}, bg=colors.HexColor('#FFFFFF', False, True))

##    img = Image.open(name+".png")
##    img = img.convert("RGBA")
##    datas = img.getdata()
##
##    newData = []
##    for item in datas:
##        if item[0] == 255 and item[1] == 255 and item[2] == 255:
##            newData.append((255, 255, 255, 0))
##        else:
##            newData.append(item)
##
##    img.putdata(newData)
##    img.save(name+".png", "PNG")


