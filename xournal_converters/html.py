#!/usr/bin/env python
from __future__ import print_function, unicode_literals
from argparse import ArgumentParser
from xml.etree.cElementTree import ElementTree
from io import StringIO
import gzip, cgi


def main():
    # fetch path
    parser = ArgumentParser()
    parser.add_argument('path')
    args = parser.parse_args()

    # extract xml in zip archive
    with gzip.open(args.path, 'rb') as fp:
        xml = ElementTree(file=fp)

    # convert to HTML
    def coords(stroke):
        coords = stroke.text.split()
        coords = ' '.join('L ' + coords[i] + ' ' + coords[i + 1]
                          for i in range(0, len(coords), 2))
        return 'M' + coords[1:]

    errors = []

    dest = StringIO()
    for page in xml.getroot().iter('page'):
        # determine background info
        background = page.find('background')
        if background.attrib['type'] == 'solid':
            if background.attrib['style'] != 'plain':
                errors.append("Do not know how to handle background style '%s'"
                              % background.attrib['style'])
            background_color = background.attrib['color']
            background_css = "background-color: %s;" % background_color
        else:
            errors.append("Do not know how to handle background type '%s'" %
                          background.attrib['type'])
            background_css = ""

        # start new page
        dest.write('<p>\n')
        dest.write(
            '<svg width="%spt" height="%spt" style="border: 1px solid black; %s" viewBox="0 0 %s %s">\n'
            % (page.attrib['width'], page.attrib['height'], background_css,
               page.attrib['width'], page.attrib['height']))
        for layer in page.iter('layer'):
            dest.write('<g>\n')
            for item in layer:
                if item.tag == 'stroke':
                    if item.attrib["tool"] not in ["pen", "highlighter"]:
                        errors.append(
                            "Do not know how to handle stroke tool '%s'" %
                            item.attrib['tool'])
                    dest.write(
                        '<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" '
                        % (coords(item), item.attrib["color"],
                           item.attrib["width"]))
                    if item.attrib["tool"] == "highlighter":
                        dest.write('stroke-opacity="0.5" ')
                    dest.write('/>\n')
                elif item.tag == 'text':
                    dy = 0
                    font_size = float(item.attrib["size"])
                    for line in item.text.split("\n"):
                        dest.write(
                            '<text font-family="%s" font-size="%s" x="%s" y="%s" fill="%s">%s</text>\n'
                            % (item.attrib["font"], font_size,
                               item.attrib["x"],
                               dy + float(item.attrib["y"]) + font_size,
                               item.attrib["color"], cgi.escape(line)))

                        dy += float(item.attrib["size"])
                elif item.tag == 'image':
                    dest.write(
                        '<image x="%s" y="%s" width="%s" height="%s" xlink:href="data:image/png;base64,%s" />\n'
                        % (item.attrib["left"], item.attrib["top"],
                           float(item.attrib["right"]) -
                           float(item.attrib["left"]),
                           float(item.attrib["bottom"]) -
                           float(item.attrib["top"]), cgi.escape(item.text)))
                else:
                    errors.append("Unknown item '%s'" % item.tag)
            dest.write('</g>\n')
        dest.write('</svg>\n')
        dest.write('</p>\n')

    # render document with errors prefixed
    print('<html>')
    print('<body>')

    if errors:
        print('<p>')
        print('<ul style="color: red">')
        for e in errors:
            print('<li>', e, '</li>')
        print('</ul>')
        print('</p>')

    print(dest.getvalue())

    print('</body>')
    print('</html>')


if __name__ == '__main__':
    main()
