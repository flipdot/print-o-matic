#!/usr/bin/env python3
# Needs the following packages:
#   pip3 install reportlab PyPDF2

import os
import sys
import requests

import locale
import datetime
from dateutil.parser import parse

from io import BytesIO # circumvent reportlabs need to use files
from reportlab.pdfgen import canvas # generate PDFs
from PyPDF2 import PdfFileWriter, PdfFileReader # merge PDFs

url = "https://flipdot.org/blog/uploads/Spendenbescheinigung_Blankoformular_-_nutzbar_bis04_11_2020.pdf"
fn = "blanko.pdf"
outdir = "pdf"
pre = "spendenbescheinigung"
h = 1169
coords = dict(
        name = (50, 677),
        street = (50, 665),
        city = (50, 653),
        value = (50, 602),
        phonetic = (180, 602),
        blank1 = (430, 600),
        blank2 = (55, 18),
        date = (434, 602),
        today = (82, 155),
        )
font_family = "Helvetica"
font_size = 10

# Used for German date
locale.setlocale(locale.LC_TIME, 'de_DE')

def usage():
    print("Usage:")
    print("spende.py NAME STREET PLZ+CITY CENTS [DATE]")
    print()
    print("Example:")
    print("spende.py \"Max Mustermann\" \"Musterstraße 123\" \"12345 Musterstadt\" \"4223\" \"2020-12-31\"")
    print("                                                                   ^ 42,23 EURO")

# Get document
def download():
    r = requests.get(url)
    if r.status_code is not 200:
        print("Failed to download document located at:")
        print("  %s" % url)
    with open(fn, 'bw') as f:
        f.write(r.content)

def str2fn(string):
    return string.lower().replace(" ", "-").replace(".", "")

def fill_out(name, street, city, value, date):
    value = int(value) / 100
    if value == int(value):
        value = int(value)

    # Generate additions
    p = BytesIO()
    c = canvas.Canvas(p)
    c.setFont(font_family, font_size)

    # Paint over date of gratuity in template
    c.setFillColorRGB(1, 1, 1)
    c.rect(coords['blank1'][0], coords['blank1'][1], coords['blank2'][0], coords['blank2'][1], fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)

    # Add text
    c.drawString(coords['name'][0], coords['name'][1], name)
    c.drawString(coords['street'][0], coords['street'][1], street)
    c.drawString(coords['city'][0], coords['city'][1], city)
    c.drawString(coords['value'][0], coords['value'][1], str(value).replace(".", ","))
    c.drawString(coords['phonetic'][0], coords['phonetic'][1], phonetic(value))
    c.drawString(coords['today'][0], coords['today'][1], datetime.date.today().strftime('%d. %B %Y'))
    c.drawString(coords['date'][0], coords['date'][1], parse(date).strftime('%d.%m.%Y'))

    c.save()
    p.seek(0)

    addition = PdfFileReader(p)
    template = PdfFileReader(open(fn, 'br'))

    # Merge PDFs
    output = PdfFileWriter()
    page = template.getPage(0)
    page.mergePage(addition.getPage(0))
    output.addPage(page)

    # Write merged output
    outfile = open("%s/%s-%s-%s.pdf" % (outdir, pre, str2fn(name), parse(date).strftime('%d-%m-%Y')), 'bw')
    output.write(outfile)
    outfile.close()

def phonetic(num):
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

# Main
if not os.path.isfile(fn):
    download()

if not os.path.isdir(outdir):
    os.makedirs(outdir)

if len(sys.argv) < 6:
    print("Missing parameters...")
    print("")
    usage()
    sys.exit(1)

name = sys.argv[1]
street = sys.argv[2]
city = sys.argv[3]
value = sys.argv[4]
date = sys.argv[5]

fill_out(name, street, city, value, date)

