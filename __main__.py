#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Entry point for running the program."""

import argparse
import atexit

from . import TruthSaver

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--update_only',
                        help='Only update the times list, skip'
                        ' downloading.',
                        action='store_true')
    parser.add_arguemnt('--try_all',
                        help='Try to download all videos which are,'
                        ' not in a good status.',
                        action='store_true')
    parser.add_argument('--times_path',
                        help='Path to pkl file containing a record'
                        ' of saved time entries',
                        type=str)
    parser.add_argument('--video_dir',
                        help='Directory for were to save downloaded'
                        ' videos.',
                        type=str)

    args = parser.args()

    truth = TruthSaver(args.time_path, args.video_dir,
                       args.update_only, args.try_all)

    truth.update_download_list()
    if not args.update_only:
        atexit.register.save_entries()
        truth.download_videos()

if __name__ == '__main__':
    main()
