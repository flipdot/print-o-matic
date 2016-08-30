#!/usr/bin/env python3
# Needs the following packages:
#   pip3 install reportlab PyPDF2

import os
import sys
import requests

import locale
import datetime
from dateutil.parser import parse

import re
import yaml
#from ast import literal_eval

from sys import platform
from io import BytesIO # circumvent reportlabs need to use files
from reportlab.pdfgen import canvas # generate PDFs
from reportlab.platypus import *
from reportlab.lib.styles import getSampleStyleSheet # line breaks
from reportlab.lib.pagesizes import * # custom document size
from PyPDF2 import PdfFileWriter, PdfFileReader # merge PDFs
import collections

config_dir = "config"
template_dir = "templates"
output_dir = "output"

# reportlab defaults
style = getSampleStyleSheet()['Normal']
style.wordWrap = 'LTR'
style.leading = 12

def usage():
    print("Usage:")
    print("fill-form.py CONFIG_FILE [VARIABLE1:VALUE1] [VARIABLE2:VALUE2] ...")
    print()
    print("Example:")
    print("fill-form.py geldzuwendung name=\"Max Mustermann\" street=\"Musterstraße 123\" city=\"12345 Musterstadt\" date=\"31.12.2020\" amount=\"42.23\"")


# Download file via http(s) to local filesystem
def download(url, target):
    r = requests.get(url)
    if r.status_code is not 200:
        print("Failed to download document located at:")
        print("  %s" % url)
        return False
    with open(target, 'bw') as f:
        f.write(r.content)
        return True


# Convert string to adequate file name
def str2fn(string):
    return string.lower().replace(" ", "-").replace(".", "")


# Fill out the form with the values according to the config file
def fill_out(name, template_file, config, values):
    # Page size
    if config.get("file").get("page_size"):
        # TODO Check page_size to be contained within reportlab.lib.pagesizes
        page_size = eval(config.get("file").get("page_size"))
    else:
        # Default
        page_size = A4
    if config.get("file").get("locale"):
        # Used for localised date and currency
        locale_str = config.get("file").get("locale")
        if platform == "win32":
            # Windows fucks up all the locales
            locale_str = re.sub(r'([a-z]+)_.*', r'\1', locale_str)
        locale.setlocale(locale.LC_TIME, locale_str)
        locale.setlocale(locale.LC_MONETARY, locale_str)
    else:
        print("Locale missing... (file.locale)\n")
        return False

    # Prepare overlay document
    b = BytesIO()
    c = canvas.Canvas(b)
    c.setFont(config.get("file").get("font_family"), config.get("file").get("font_size"))

    sorted_pages = collections.OrderedDict(sorted(config.get("pages").items()))
    for page_name, page in sorted_pages.items():
        # Print boxes
        if page.get("box"):
            for k, v in page.get("box").items():
                color = v.get("color")
                area = v.get("area")

                c.setFillColorRGB(color[0], color[1], color[2])
                c.rect(area[0][0], area[0][1], area[1][0], area[1][1], fill=1, stroke=0)
                # Default to black
                c.setFillColorRGB(0, 0, 0)

        # Print crosses / checkmarks
        if page.get("cross"):
            for k, v in page.get("cross").items():
                color = v.get("color")
                area = v.get("area")

                c.setFillColorRGB(color[0], color[1], color[2])
                c.line(area[0][0], area[0][1], area[0][0] + area[1][0], area[0][1] + area[1][1])
                c.line(area[0][0], area[0][1] + area[1][1], area[0][0] + area[1][0], area[0][1])
                # Default to black
                c.setFillColorRGB(0, 0, 0)

        # Print text
        yaml_name = []
        if page.get("text"):
            for k, v in page.get("text").items():
                # Get fixed/variable text
                if values.get(k) is not None:
                    label = values.get(k)
                elif v.get("label") is not None:
                    label = v.get("label")
                elif v.get("optional"):
                    continue
                elif v.get("function") is None:
                    print("No value found for \"%s\".\n" % k)
                    return False
                if v.get("function") is not None:
                    # Use prefixed functions from within yaml
                    function = eval("doc_%s" % v.get("function"))
                    args = v.get("arguments")
                    for ak in args:
                        val = args.get(ak)
                        if isinstance(val, str):
                            if val[0] is '$':
                                args[ak] = values.get(args.get(ak)[1:])
                    args["label"] = label
                    label = function(args)
                position = v.get("position")
                # DEBUG
                #print("%s = %s" % (k, label))

                # Get specified/default dimension
                if v.get("dimension") is not None:
                    dimension = v.get("dimension")
                else:
                    dimension = page_size

                # Simple string miss line breaks
                #c.drawString(position[0], position[1], label)

                # Paragraphs have them
                p = Paragraph(label, style)
                p.wrapOn(c, dimension[0], dimension[1])
                p.drawOn(c, position[0], position[1])

                # Add to file name
                if v.get("file_name"):
                    yaml_name.append(str2fn(label))
        c.showPage()

    c.save()
    b.seek(0)

    addition = PdfFileReader(b)
    template = PdfFileReader(open(template_file, 'br'))

    # Merge PDFs
    output = PdfFileWriter()
    for i in range(0,template.getNumPages()):
        page = template.getPage(i)
        if i < addition.getNumPages():
            page.mergePage(addition.getPage(i))
        output.addPage(page)

    # File addition
    # TODO: yaml is not parsed deterministically
    #       therefore data is not at the same place all the time
    #       and yaml_name should be sorted first
    #       if multiple values have 'file_name' set in yaml
    yaml_fn = "-".join(yaml_name)

    # Write merged output
    outfile = open("%s/%s-%s-%s.pdf" % (output_dir, name, yaml_fn, datetime.date.today().strftime('%d-%m-%Y')), 'bw')
    output.write(outfile)
    outfile.close()

    return True


def doc_today(args):
    return datetime.date.today().strftime(args.get("format"))


def doc_currency(args):
    amount = float(args.get("label"))
    return locale.currency(amount, grouping = args.get("grouping"))


def doc_sum(args):
    amounts = [float(args.get(x)) for x in args if x.startswith("amount") and args.get(x) is not None]
    return str(sum(amounts))


def doc_phonetic(args):
    num = float(args.get("value"))
    if int(num) == num:
        ret = phonetic_int(int(num))
        ret += "-euro"
    else:
        ret = phonetic_int(int(num))
        ret += "-euro-"
        fp = int((round(num, 2) - int(num)) * 100)
        ret += phonetic_int(fp)
        ret += "-cent"
    return ret


def phonetic_int(num):
    digits = ('null', 'ein', 'zwei', 'drei', 'vier', 'fünf', 'sechs', 'sieben', 'acht', 'neun')
    tenners = {
            2: 'zwanzig',
            3: 'dreißig',
            6: 'sechzig',
            7: 'siebzig',
            }
    positions = ('', 'zig', 'hundert', 'tausend')
    glue = 'und'
    delimiter = '-'
    lookup = {
            #1: 'eins', # not in currency
            10: 'zehn',
            11: 'elf',
            12: 'zwölf',
            13: 'dreizehn',
            14: 'vierzehn',
            15: 'fünfzehn',
            16: 'sechzehn',
            17: 'siebzehn',
            18: 'achtzehn',
            19: 'neunzehn',
            }
    s = str(num)
    l = len(s)
    m = l
    ret = ""
    if l is 1:
        # Only single digit
        if num in lookup:
            ret += lookup[num]
        else:
            ret += digits[num]
    else:
        # At least one hundred
        while l > 2:
            d = int(s[m-l])
            if d > 0:
                if ret is not "":
                    ret += delimiter
                ret += digits[d]
                ret += positions[l-1]
            l-=1
        # Lookups
        n21 = int("%s%s" % (s[-2], s[-1]))
        if n21 in lookup:
            ret2 = lookup[n21]
        else:
            # German reading flips tenners and oners
            ret2 = ""
            n1 = int(s[-1])
            n2 = int(s[-2])
            if n1 > 0 and n2 > 0:
                ret2 += digits[n1]
                ret2 += delimiter
                ret2 += glue
                ret2 += delimiter
            if n2 in tenners:
                ret2 += tenners[int(s[-2])]
            elif n2 > 0:
                ret2 += digits[int(s[-2])]
                ret2 += positions[1]
            elif n1 > 0:
                ret2 += digits[n1]
        if ret is "":
            ret += ret2
        elif  ret2 is "":
            ret = ret
        else:
            ret += delimiter
            ret += ret2
    return ret


def parse_args(strings):
    print(strings)
    values = {}
    for value in value_strings:
        m = re.search('([\w\d_-]+)=([^"]+)', value)
        if m is None:
            return False
        if len(m.groups()) < 2:
            return False
        values[m.group(1)] = m.group(2)
    print(value)
    print(m.groups())
    return values


def create_dir(dir):
    if not os.path.isdir(dir):
        os.makedirs(dir)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Need at least 2 parameters...\n")
        usage()
        sys.exit(1)

    config_name = sys.argv[1]
    config_file = "%s/%s.yml" % (config_dir, config_name)
    template_file = "%s/%s.pdf" % (template_dir, config_name)
    value_strings = sys.argv[2:]

    # Check and load config file
    if not os.path.isfile(config_file):
        print("Config file (%s) not found...\n" % config_file)
        usage()
        sys.exit(2)
    with open(config_file, 'r') as stream:
        config = yaml.load(stream)

    # Parse command line arguments
    values = parse_args(value_strings)
    if values is False:
        print("Error parsing arguments...\n")
        usage()
        sys.exit(3)

    # Get file and create folder
    url = config.get("file").get("source")
    create_dir(template_dir)
    if not os.path.isfile(template_file):
        if not download(url, template_file):
            print("Error downloading template file...\n  (%s)\n" % url)
            usage()
            sys.exit(4)
    create_dir(output_dir)

    if not fill_out(config_name, template_file, config, values):
        print("Error filling out document. Please make sure you have all the required parameters...\n")
        usage()
        sys.exit(5)
