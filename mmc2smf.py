#! /usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import sys
import libmmc.mmcreader as mmcreader
import libmmc.smfwriter as smfwriter

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', nargs='?')
    parser.add_argument('-F', '--format', choices=[0, 1], type=int, default=0, help='specify output SMF format')
    args = parser.parse_args()
    inb = None
    if args.input is None:
        inb = sys.stdin.buffer.read()
    else:
        with open(args.input, 'rb') as fh:
            inb = fh.read()
    song = mmcreader.parse_mmc(inb)
    blob = smfwriter.song_to_smf(song, args.format)
    sys.stdout.buffer.write(blob)
