#!/usr/bin/env python3
# -*-  coding: utf-8 -*-
"""Saves all videos found on rankings.the-elite.net"""

import collections
import datetime
import logging
import os
import pickle
import time

import requests
import pytube
# TODO(dc): Add python2.x support with older BS
from bs4 import BeautifulSoup


def datetime_ts():
  dt = datetime.datetime.now()
  return dt.isoformat().split('.')[0].replace(':', '-')

# set up logging to file - see previous section for more details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%m-%d %H:%M',
    filename='/tmp/truth_saver_%s.log' % datetime_ts(),
    filemode='w')


# Base URL for the rankings
BASE_URL = 'https://rankings.the-elite.net'
AJAX_ENDPOINT = '/ajax/stage/'

# Number of max atttempts to resolve url
MAX_TRIES = 5

# Standard download path
DEFAULT_PATH = './vids/'

# File which records which videos have been downloaded
DOWNLOAD_RECORD = './downloadData.pkl'

GAMES = ["goldeneye", "perfect-dark"]

# Dictonary of Goldeneye and Perfect-Dark levels
STAGES = {
    "goldeneye":[
        (1, 'dam'), (2, 'facility'), (3, 'runway'), (4, 'surface1'),
        (5, 'bunker1'), (6, 'silo'), (7, 'frigate'), (8, 'surface2'),
        (9, 'bunker2'), (10, 'statue'), (11, 'archives'), (12, 'streets'),
        (13, 'depot'), (14, 'train'), (15, 'jungle'), (16, 'control'),
        (17, 'caverns'), (18, 'cradle'), (19, 'aztec'), (20, 'egypt')
    ],
    "perfect-dark":[
        (21, 'defection'), (22, 'investigation'), (23, 'extraction'),
        (24, 'villa'), (25, 'chicago'), (26, 'g5'), (27, 'infiltration'),
        (28, 'rescue'), (29, 'escape'), (30, 'air-base'), (31, 'af1'),
        (32, 'crash-site'), (33, 'pelagic'), (34, 'deep-sea'), (35, 'ci'),
        (36, 'attack-ship'), (37, 'skedar-ruins'), (38, 'mbr'),
        (39, 'maian-sos'), (40, 'war')
    ]
}

STAGE_PREFIX_DCT = {
    'control': 'ge', 'ci': 'pd', 'g5': 'pd',
    'villa': 'pd', 'facility': 'ge',
    'bunker2': 'ge', 'bunker1': 'ge',
    'caverns': 'ge', 'infiltration': 'pd',
    'mbr': 'pd', 'extraction': 'pd',
    'pelagic': 'pd', 'egypt': 'ge',
    'investigation': 'pd', 'archives': 'ge',
    'depot': 'ge', 'war': 'pd',
    'defection': 'pd', 'streets': 'ge',
    'rescue': 'pd', 'dam': 'ge',
    'air-base': 'pd', 'skedar-ruins': 'pd',
    'train': 'ge', 'statue': 'ge', 'cradle': 'ge',
    'maian-sos': 'pd', 'silo': 'ge',
    'surface2': 'ge', 'surface1': 'ge',
    'frigate': 'ge', 'attack-ship': 'pd',
    'runway': 'ge', 'chicago': 'pd', 'escape': 'pd',
    'aztec': 'ge', 'jungle': 'ge',
    'deep-sea': 'pd', 'crash-site': 'pd', 'af1': 'pd'
}

#MODES
MODES = {
    "goldeneye": [
        'Agent', 'SA', '00A', 'LTK', 'DLTK'
    ],
    "perfect-dark":[
        'Agent', 'SA', 'PA', 'LTK', 'DLTK'
    ]
}


# TIME_ENTRY
class TimeEntry(collections.namedtuple('TimeEntry',
                                       ['url', 'time_id', 'player',
                                        'mode', 'stage', 'time', 'status'])):
  """TimeEntry is a container for all information needed for a ge time."""

  def vid_path(self):
    """Returns a local path for where videos should be downloaded."""
    player_name = self.player.replace(' ', '_')
    vid_name = ('%s.%s.%s.%04d.%s' %
                (STAGE_PREFIX_DCT[self.stage],
                 self.stage, self.mode,
                 int(self.time),
                 player_name))
    return os.path.join(player_name, vid_name)


def ge_time_to_sec(time_str):
  """Converts time MM:SS to int seconds."""
  t_l = time_str.split(':')
  if len(t_l) == 2:
    return 60*int(t_l[0]) + int(t_l[1])
  elif len(t_l) == 3:
    return 3600*int(t_l[0]) + 60*int(t_l[1]) + int(t_l[2])
  else:
    raise ValueError('Time String %s is not in expected format!'
                     % time_str)


def sec_to_ge_time(time_sec):
  """Converts time from number of seconds to H:MM:SS."""
  if int(time_sec / 3600) == 0:
    return '%d:%02d' % (int(time_sec / 60), time_sec%60)
  else:
    return '%d:%02d:%0d' % (int(time_sec / 3600),
                            int(time_sec % 3600)/60,
                            int(time_sec % 60))

def request_with_retry(url):
  """Requests with retry, upon failure it has exponetial backoff."""
  tries = 0
  while tries < MAX_TRIES:
    try:
      response = requests.get(url)
      response.raise_for_status()
    except ValueError:
      time.sleep(2*2**tries)
      tries += 1
      continue
    else:
      break
  return response

def pytubeRetry(url):
  tries = 0
  while tries < MAX_TRIES:
    try:
      yt_handle = pytube.YouTube(url)
    except IOError:
      time.sleep(2*2**tries)
      tries += 1
      continue
    else:
      return yt_handle
  raise IOError('Unable to load %s into pytube.YouTube' % url)


class TruthSaver(object):
  """Manages the saved entries of times to download, and downloading them.

  For the main ranks it fetches the JSON available at an ajax endpoint per
  stage, and converts it into a TimeEntry. For LTK each stage has to be
  opened up and parsed with Beautifulsoup converting the data on the page
  into a TimeEntry.

  self.saved_entries is a dictonary of TimeEntrys with the keys equal to
  TimeEntry.url which is gaurnteed to be unqiue.

  self.local_path is the path where player folders live and in the player
  folders where the times are downloaded.
  """
  NEW_URL = 0
  DOWNLOADED = 1
  BAD_LINK = -1
  BAD_VIDEO = -2

  def __init__(self, filepath=None, video_root=None,
               update_only=False, try_all=False, low_quality=False):
    """Initalizes self.local_path and self.saved_entries."""

    self.local_path = filepath
    self.videos_dir_root = video_root
    self.update_only = update_only
    self.try_all = try_all
    self.low_quality = low_quality

    if not self.videos_dir_root:
      self.videos_dir_root = DEFAULT_PATH
    if not os.path.isdir(self.videos_dir_root):
      os.mkdir(self.videos_dir_root)

    if not self.local_path:
      self.saved_entries = {}
    else:
      try:
        self.saved_entries = self.get_saved_list()
      except (IOError, pickle.UnpicklingError):
        logging.error('Error loading file. Starting with an empty list.')
        self.saved_entries = {}

  def get_saved_list(self, filepath=None):
    """Given full path return times_list saved as a pickle file"""

    if filepath:
      self.local_path = filepath

    try:
      binfile = open(self.local_path, 'rb')
    except IOError as e:
      logging.error('IOError: for file %s', self.local_path)
      raise e
    try:
      times_dict = pickle.load(binfile)
    except pickle.UnpicklingError as e:
      logging.error('UnpicklingError: pickle file %s failed to open.',
                    self.local_path)
      raise e
    finally:
      binfile.close()
    # TODO(dc): Change print statements to logging
    logging.info('File %s properly loaded!', self.local_path)
    logging.info('Fetched file is of size: %d', len(times_dict))
    return times_dict

  #saves the list
  def save_entries(self, filepath=None):
    """Save the currnet self.saved_entries to a pickle file."""

    if filepath:
      self.local_path = filepath
    elif not self.local_path:
      self.local_path = ('./truth_saver_%s.pkl' % datetime_ts())
    try:
      binfile = open(self.local_path, 'wb')
    except IOError:
      logging.error('Error writing download list, %s',
                    self.local_path)
      raise
    pickle.dump(self.saved_entries, binfile)
    binfile.close()
    return

  def stage_data_to_times(self, stage, stage_data):
    """Returns a dictonary of regular times with videos for a stage."""

    times = {}

    if stage[0] < 21:
      game = GAMES[0]
    else:
      game = GAMES[1]

    # Level data is ordered as follows,
    #   Mode (agent, sa, 00a)
    #   Time(Player_Name, FirstN+LastN, Player_ID,
    #      Time_ID, Time_sec, vid_comment_status*)
    # Comment vid_comment_status 0 = None, 1 = Comment, 2 = Video
    for mode, player_times in zip(MODES[game][:3], stage_data):
      # The player_times array is not sliced by player this does that
      sliced_times = [
          player_times[i:i + 6] for i in range(0, len(player_times), 6)]
      for t in sliced_times:
        if t[5] == 2:
          time_id = t[3]
          time_url = BASE_URL + '/~' + t[1] + '/time/' + str(time_id)
          entry = TimeEntry(url=time_url, time_id=time_id,
                            player=t[0], mode=mode, stage=stage[1],
                            time=t[4], status=self.NEW_URL)
          times[entry.url] = entry
    return times

  def get_ltk_level_data(self, stage):
    """Returns up-to-date (D)LTK times with videos for a stage."""

    if stage[0] < 21:
      game = GAMES[0]
    else:
      game = GAMES[1]

    url = BASE_URL + '/' + game + '/ltk/stage/' + stage[1]
    page = request_with_retry(url)

    try:
      page.raise_for_status()
    except:
      logging.error("Error loading page: %s", url)
      raise

    ltk_times = {}
    game = url.split('/')[-4]

    # Parse the HTML level page for all the player times with videos
    soup = BeautifulSoup(page.text, "html.parser")
    for table, mode in zip(soup.find_all('table'), MODES[game][3:]):
      for tr in table.find_all('tr'):
        if tr.find(class_='video-link'):
          player = tr.find(class_='user').text
          time_tag = tr.find(class_='time')
          time_url = BASE_URL + time_tag['href']
          time_id = int(time_url.split('/')[-1])
          time_sec = ge_time_to_sec(time_tag.text)
          entry = TimeEntry(url=time_url, time_id=time_id,
                            player=player, mode=mode, stage=stage[1],
                            time=time_sec, status=self.NEW_URL)
          ltk_times[entry.url] = entry
    return ltk_times

  def get_regular_level_data(self, stage):
    """Returns dictonary of up to date regular times for a stage."""

    url = BASE_URL + AJAX_ENDPOINT + str(stage[0])
    logging.info('Loading AJAX page %s', url)
    response = request_with_retry(url)
    try:
      response.raise_for_status()
      stage_data = response.json()
    except ValueError as e:
      logging.error('Could not fetch data %s', str(e))
      raise
    return self.stage_data_to_times(stage, stage_data)

  def get_all_time_entries(self):
    """Returns dictonry of all up to date GE/PD times with videos."""

    time_entries = {}
    print('Loading Stage Data...')
    for game in GAMES:
      for stage in STAGES[game]:
        print('%02d/40 ... %s       '
              % (stage[0], stage[1]), end='\r')
        # Regular mode data first
        time_entries.update(self.get_regular_level_data(stage))
        # LTK Times
        time_entries.update(self.get_ltk_level_data(stage))
    print('')
    return time_entries

  @classmethod
  def get_yt_link(cls, time_entry):
    """Returns youtube link if there is one, raises execptions if not."""

    response = request_with_retry(time_entry.url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    for tag in soup.find_all('p'):
      for link in tag.find_all('a', href=True):
        if 'YouTube' in link.text:
          return link['href']
        elif ('Download video' in link.text
              and 'youtu' in link['href']):
          return link['href']

        if 'Twitch' in link.text:
          raise ValueError(
              'Cannot download %s it is a twitch video %s'
              % (os.path.basename(time_entry.vid_path()),
                 link['href']))
        elif 'Download video' in link.text:
          raise ValueError(
              'Manually download %s, at %s'
              % (os.path.basename(time_entry.vid_path()),
                 link['href']))

    raise ValueError('Expected video link for time %s, found nothing.'
                     % os.path.basename(time_entry.vid_path()))

  def update_download_list(self):
    """Updates the saved_entries with new times."""

    current_entries = self.get_all_time_entries()

    for cur_entry_k, cur_entry_v in current_entries.items():
      if cur_entry_k not in self.saved_entries:
        self.saved_entries[cur_entry_k] = cur_entry_v
    self.save_entries()

  def download_yt_video(self, yt_link, time_entry):
    """Downloads highest quality yt video given the link, and TimeEntry."""

    player_dirname, vid_basename = os.path.split(time_entry.vid_path())
    vid_dirname = os.path.join(self.videos_dir_root, player_dirname)
    yt_handle = pytubeRetry(yt_link)

    if not os.path.isdir(vid_dirname):
      os.mkdir(vid_dirname)
    yt_handle.set_filename(vid_basename)
    # This will download the highest quality video
    hq_vid = sorted(yt_handle.videos, key=lambda x: x.resolution,
                    reverse=(not self.low_quality))[0]
    try:
      hq_vid.download(vid_dirname)
    except IOError as e:
      logging.error('IOError downloading %s/%s',
                    vid_dirname, vid_basename)
      logging.error(str(e))
      logging.error('Skipping entry for now retry later')
      raise IOError
    logging.info('Downloaded video: %s', time_entry.vid_path())

  def download_videos(self):
    """Saves all new videos and retries error videos if try_all is true."""

    n_entries = sum(e.status != self.DOWNLOADED
                    for e in self.saved_entries.values())
    if not self.try_all:
      n_entries = sum(e.status == self.NEW_URL
                      for e in self.saved_entries.values())
    n = 1
    print('Checking / Downloading: %s Videos ' % n_entries)
    for time_entry in self.saved_entries.values():
      bar_len = int(25*n/n_entries)
      bar = '+'*bar_len + ' '*(25 - bar_len)
      print('[ %s / %s ] |%s| ' % (n, n_entries, bar), end='\r')
      if time_entry.status == self.DOWNLOADED:
        continue
      if time_entry.status != self.NEW_URL and not self.try_all:
        continue
      try:
        yt_link = self.get_yt_link(time_entry)
      except ValueError as e:
        logging.error(e)
        self.saved_entries[time_entry.url] = (time_entry._replace(
            status=self.BAD_LINK))
        continue
      try:
        logging.info('Downloading video %s', yt_link)
        self.download_yt_video(yt_link, time_entry)
      except (pytube.exceptions.PytubeError,
              pytube.exceptions.DoesNotExist,
              pytube.exceptions.AgeRestricted,
              AttributeError) as e:
        logging.error(str(e))
        logging.error('Error downloading the video %s', yt_link)
        self.saved_entries[time_entry.url] = (
            time_entry._replace(status=self.BAD_VIDEO))
        continue
      except IOError:
        continue
      else:
        self.saved_entries[time_entry.url] = (
            time_entry._replace(status=self.DOWNLOADED))
        n += 1
    print('[ %s / %s ] |%s| ' % (n, n_entries, '+'*25))
    print('Finished downloading all videos.')
