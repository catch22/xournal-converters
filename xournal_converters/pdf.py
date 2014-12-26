#!/usr/bin/env python
from argparse import ArgumentParser
from xml.etree.cElementTree import ElementTree
from reportlab.pdfgen import canvas
from reportlab.lib.colors import toColor, Color
from reportlab.pdfbase._fontdata import standardFonts
from reportlab.lib.utils import ImageReader
from StringIO import StringIO
from base64 import b64decode
import gzip, sys


def main():
  # fetch path
  parser = ArgumentParser()
  parser.add_argument('src')
  args = parser.parse_args()

  # extract xml in zip archive
  with gzip.open(args.src, 'rb') as fp:
    xml = ElementTree(file=fp)

  # render PDF
  dest = StringIO()
  c = canvas.Canvas(dest, bottomup=0)
  errors = []
  for page in xml.getroot().iter('page'):
    # set page size
    c.setPageSize((float(page.attrib['width']), float(page.attrib['height'])))

    # fill with background color
    background = page.find('background')
    if background.attrib['type'] == 'solid':
      background_color = background.attrib['color']
      if background.attrib['style'] != 'plain':
        errors.append("Do not know how to handle background style '%s'" % background.attrib['style'])
      else:
        c.setFillColor(background_color)
        c.rect(0, 0, float(page.attrib['width']), float(page.attrib['height']), stroke=0, fill=1)
    else:
      errors.append("Do not know how to handle background type '%s'" % background.attrib['type'])

    # render layers
    for layer in page.iter('layer'):
      for item in layer:
        # render stroke?
        if item.tag == 'stroke':
          # configure pen
          if item.attrib["tool"] not in ["pen", "highlighter"]:
            errors.append("Do not know how to handle stroke tool '%s'" % item.attrib['tool'])
          color = toColor(item.attrib["color"])
          if item.attrib["tool"] == "highlighter":
            color.alpha = 0.5
          c.setStrokeColor(color)
          c.setLineWidth(float(item.attrib["width"]))

          # draw path
          coords = item.text.split()
          p = c.beginPath()
          p.moveTo(float(coords[0]), float(coords[1]))
          for i in range(0, len(coords), 2):
            fn = p.moveTo if i == 0 else p.lineTo
            fn(float(coords[i]), float(coords[i+1]))
          c.drawPath(p)

        # render text?
        elif item.tag == 'text':
          dy = 0
          for line in item.text.split("\n"):
            font = item.attrib["font"]
            if font not in standardFonts:
              errors.append("Unknown font '%s', falling back to Helvetica." % font)
              font = "Helvetica"
            c.setFont(font, float(item.attrib["size"]))

            c.setFillColor(item.attrib["color"])
            c.drawString(item.attrib["x"], dy + float(item.attrib["y"]), line)
            dy += float(item.attrib["size"])

        # render image?
        elif item.tag == 'image':
          # png image base 64 encoded
          png_data = b64decode(item.text)
          #png = Image.open(StringIO(png_data))
          png = ImageReader(StringIO(png_data))
          x = float(item.attrib["left"])
          y = float(item.attrib["top"])
          width = float(item.attrib["right"]) - float(item.attrib["left"])
          height = float(item.attrib["bottom"]) - float(item.attrib["top"])
          c.saveState()
          c.translate(x, y + height/2)
          c.scale(1, -1)
          c.drawImage(png, 0, -height/2, width, height, anchor='nw')
          c.restoreState()

        # !?
        else:
          errors.append("Unknown item '%s'" % item.tag)

    c.showPage()

  c.save()

  if errors:
      print errors
      sys.exit(-1)

  print dest.getvalue()


if __name__ == '__main__':
  main()
