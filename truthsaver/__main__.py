#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Entry point for running the program."""

import argparse
import atexit

import truthsaver

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--update_only',
                      help='Only update the times list, skip'
                      ' downloading.',
                      action='store_true')
  parser.add_argument('--download_only',
                      help='Only download saved times, no update.',
                      action='store_true')
  parser.add_argument('--try_all',
                      help='Try to download all videos which are,'
                      ' not in a good status.',
                      action='store_true')
  parser.add_argument('--times_path',
                      help='Path to ".json" or ".pkl" file containing a record'
                      ' of saved time entries',
                      type=str)
  parser.add_argument('--new_downloads_path', type=str,
                      help='Path to textfile containing all newly downloaded'
                      ' videos.')
  parser.add_argument('--video_dir', help='Directory for were to save'
                      ' downloaded videos.', type=str)
  parser.add_argument('--low_quality', help='Download lowest quality videos.',
                      action='store_true')

  args = parser.parse_args()

  truth = truthsaver.TruthSaver(
      record_path=args.times_path,
      video_root=args.video_dir,
      new_times_path=args.new_downloads_path,
      update_only=args.update_only,
      try_all=args.try_all,
      low_quality=args.low_quality)

  if not args.download_only:
    truth.update_download_list()
  if not args.update_only:
    atexit.register(truth.save)
    truth.download_videos()

if __name__ == '__main__':
  main()
