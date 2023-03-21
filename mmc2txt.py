#! /usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import sys
import libmmc.mmcreader as mmcreader
import libmmc.yamlwriter as yamlwriter

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', nargs='?')
    args = parser.parse_args()
    inb = None
    if args.input is None:
        inb = sys.stdin.buffer.read()
    else:
        with open(args.input, 'rb') as fh:
            inb = fh.read()
    song = mmcreader.parse_mmc(inb)
    yamlwriter.song_to_yaml(sys.stdout, 0, song)
