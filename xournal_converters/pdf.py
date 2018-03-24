#!/usr/bin/env python
from argparse import ArgumentParser
from xml.etree.cElementTree import ElementTree
from reportlab.pdfgen import canvas
from reportlab.lib.colors import toColor
from reportlab.pdfbase._fontdata import standardFonts
from reportlab.lib.utils import ImageReader
from base64 import b64decode
from PyPDF2 import PdfFileReader, PdfFileWriter
from io import BytesIO
import gzip, sys, os.path, click


def main():
    # fetch path
    parser = ArgumentParser()
    parser.add_argument('src')
    args = parser.parse_args()

    # extract xml in zip archive
    with gzip.open(args.src, 'rb') as fp:
        xml = ElementTree(file=fp)

    # render PDF
    dest = BytesIO()
    c = canvas.Canvas(dest, bottomup=0)
    warnings = []
    pdf_background_filename = None
    pdf_background_pages = {}
    for pageno, page in enumerate(xml.getroot().iter('page')):
        # set page size
        c.setPageSize((float(page.attrib['width']), float(
            page.attrib['height'])))

        # fill with background color
        background = page.find('background')
        if background.attrib['type'] == 'solid':
            background_color = background.attrib['color']
            if background.attrib['style'] == 'plain':
                c.setFillColor(background_color)
                c.rect(
                    0,
                    0,
                    float(page.attrib['width']),
                    float(page.attrib['height']),
                    stroke=0,
                    fill=1)
            else:
                warnings.append(
                    "Do not know how to handle background style '%s'" %
                    background.attrib['style'])
        elif background.attrib['type'] == 'pdf':
            if 'domain' in background.attrib:
                # determine filename according to Xournal rules
                domain = background.attrib['domain']
                if domain == 'absolute':
                    pdf_background_filename = background.attrib['filename']
                elif domain == 'attach':
                    pdf_background_filename = "%s.%s" % (
                        args.src, background.attrib['filename'])
                else:
                    warnings.append(
                        "Do not know how to handle PDF background domain '%s'"
                        % domain)

            # add page number mapping
            pdf_background_pages[pageno] = int(background.attrib['pageno']) - 1
        else:
            warnings.append("Do not know how to handle background type '%s'" %
                            background.attrib['type'])

        # render layers
        for layer in page.iter('layer'):
            for item in layer:
                # render stroke?
                if item.tag == 'stroke':
                    # configure pen
                    if item.attrib["tool"] not in ["pen", "highlighter"]:
                        warnings.append(
                            "Do not know how to handle stroke tool '%s'" %
                            item.attrib['tool'])
                    color = toColor(item.attrib["color"])
                    if item.attrib["tool"] == "highlighter":
                        color.alpha = 0.5
                    c.setStrokeColor(color)
                    c.setLineWidth(float(item.attrib["width"]))
                    c.setLineCap(1)  # round cap

                    # draw path
                    coords = item.text.split()
                    p = c.beginPath()
                    p.moveTo(float(coords[0]), float(coords[1]))
                    for i in range(0, len(coords), 2):
                        fn = p.moveTo if i == 0 else p.lineTo
                        fn(float(coords[i]), float(coords[i + 1]))
                    c.drawPath(p)

                # render text?
                elif item.tag == 'text':
                    font = item.attrib["font"]
                    if font not in standardFonts:
                        warnings.append(
                            "Unknown font '%s', falling back to Helvetica." %
                            font)
                        font = "Helvetica"
                    font_size = float(item.attrib["size"])
                    c.setFont(font, font_size)
                    c.setFillColor(item.attrib["color"])
                    dy = 0
                    for line in item.text.split("\n"):
                        c.drawString(item.attrib["x"],
                                     dy + float(item.attrib["y"]) + font_size,
                                     line)
                        dy += float(item.attrib["size"])

                # render image?
                elif item.tag == 'image':
                    # png image base 64 encoded
                    png_data = b64decode(item.text)
                    #png = Image.open(BytesIO(png_data))
                    png = ImageReader(BytesIO(png_data))
                    x = float(item.attrib["left"])
                    y = float(item.attrib["top"])
                    width = float(item.attrib["right"]) - float(
                        item.attrib["left"])
                    height = float(item.attrib["bottom"]) - float(
                        item.attrib["top"])
                    c.saveState()
                    c.translate(x, y + height / 2)
                    c.scale(1, -1)
                    c.drawImage(
                        png, 0, -height / 2, width, height, anchor='nw')
                    c.restoreState()

                # !?
                else:
                    warnings.append("Unknown item '%s'" % item.tag)

        c.showPage()

    # save PDF in the BytesIO object (`dest`)
    c.save()

    # PDF file not found? Attempt to guess better if Xournal filename is of the form 'filename.pdf.xoj'.
    if pdf_background_filename and not os.path.exists(pdf_background_filename):
        if args.src.endswith('.pdf.xoj'):
            warnings.append(
                "File not found '%s', attempting to use '%s' instead." %
                (pdf_background_filename, args.src[:-4]))
            pdf_background_filename = args.src[:-4]

    pdf_writer = None
    if pdf_background_filename:
        if not os.path.exists(pdf_background_filename):
            warnings.append("File not found '%s'." % pdf_background_filename)
        else:
            # open PDF background
            dest.seek(0)
            pdf_journal = PdfFileReader(dest)
            pdf_background = PdfFileReader(open(pdf_background_filename, 'rb'))

            # merge journal and background
            pdf_writer = PdfFileWriter()
            for pageno, _ in enumerate(xml.getroot().iter('page')):
                # page has PDF background?
                if pageno in pdf_background_pages:
                    pdf_pageno = pdf_background_pages[pageno]

                    page = pdf_background.getPage(pdf_pageno)
                    page.mergePage(pdf_journal.getPage(pageno))
                else:
                    page = pdf_journal.getPage(pageno)
                pdf_writer.addPage(page)

    # print warnings
    if warnings:
        sys.stderr.write("WARNINGS:\n")
        for line in warnings:
            sys.stderr.write(" -" + line + "\n")

    # print PDF
    stdout = click.get_binary_stream('stdout')
    if pdf_writer:
        pdf_writer.write(stdout)
    else:
        stdout.write(dest.getvalue())


if __name__ == '__main__':
    main()
