#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Saves all videos found on rankings.the-elite.net"""

import collections
import os
import pickle

import requests
from pytube import YouTube
# TODO(dc): Add python2.x support with older BS
from bs4 import BeautifulSoup

# Base URL for the rankings
BASE_URL = 'https://rankings.the-elite.net/'
AJAX_ENDPOINT = 'ajax/stage/'

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
        vid_name = (self.player + ' ' + self.stage
                    + ' ' +  self.mode + ' ' + sec_to_ge_time(self.time))
        return os.path.join(self.player, vid_name)



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

    def __init__(self, filepath=None, video_root=DEFAULT_PATH):
        """Initalizes self.local_path and self.saved_entries."""

        self.local_path = filepath
        self.videos_dir_root = video_root

        if not self.local_path:
            self.saved_entries = {}
        else:
            try:
                self.saved_entries = self.get_saved_list()
            except (IOError, pickle.UnpicklingError) as e:
                print('Error loading file. Starting with an empty list.')
                self.saved_entries = {}

    def get_saved_list(self, filepath=None):
        """Given full path return times_list saved as a pickle file"""

        if filepath:
            self.local_path = filepath

        try:
            binfile = open(self.local_path, 'rb')
        except IOError as e:
            print('IOError: for file %s' % self.local_path)
            raise e
        try:
            times_dict = pickle.load(binfile)
        except pickle.UnpicklingError as e:
            print('UnpicklingError: pickle file %s failed to open.'
                  % self.local_path)
            raise e
        binfile.close()
        # TODO(dc): Change print statements to logging
        print('File %s properly loaded!' % self.local_path)
        print('Fetched file is of size: ' + str(len(times_dict)))
        return times_dict

    #saves the list
    def save_entries(self, filepath=None):
        """Save the currnet self.saved_entries to a pickle file."""

        if filepath:
            self.local_path = filepath
        elif not self.local_path:
            self.local_path = './default.pkl'
        try:
            binfile = open(self.local_path,'wb')
        except IOError:
            print('Error writing download list.')
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
        #     Time(Player_Name, FirstN+LastN, Player_ID,
        #          Time_ID, Time_sec, vid_comment_status*)
        # Comment vid_comment_status 0 = None, 1 = Comment, 2 = Video
        for mode, player_times in zip(MODES[game][:3], stage_data):

            # The player_times array is not sliced by player this does that
            sliced_times = [player_times[i:i + 6] for i in range(
                0, len(player_times), 6)]

            for t in sliced_times:
                if t[5] == 2:
                    time_id = t[3]
                    time_url = BASE_URL + '~' + t[1] + '/time/' + str(time_id)
                    entry = TimeEntry(url=time_url, time_id=time_id,
                                      player=t[0], mode=mode, stage=stage[1],
                                      time=t[4], status=0)
                    times[entry.url] = entry
        return times

    def get_ltk_level_data(self, stage):
        """Returns up-to-date (D)LTK times with videos for a stage."""

        if stage[0] < 21:
            game = GAMES[0]
        else:
            game = GAMES[1]

        url = BASE_URL + game + '/ltk/stage/' + stage[1]
        page = requests.get(url)

        try:
            page.raise_for_status()
        except:
            print("Error loading page: " + url)
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
                    time = ge_time_to_sec(time_tag.text)
                    entry = TimeEntry(url=time_url, time_id=time_id,
                                      player=player, mode=mode, stage=stage[1],
                                      time=time, status=0)
                    ltk_times[entry.url] = entry
        return ltk_times

    def get_regular_level_data(self, stage):
        """Returns dictonary of up to date regular times for a stage."""

        url = BASE_URL + 'ajax/stage/' + stage[1]
        # TODO(dc): Log page access.
        response = requests.get(url)
        try:
            response.raise_for_status()
            stage_data = response.json()
        except ValueError:
            # TODO(dc): Add a clean exit.
            # TODO(dc): Add logging.
            raise

        return self.stage_data_to_times(stage, stage_data)

    def get_all_time_entries(self):
        """Returns dictonry of all up to date GE/PD times with videos."""

        time_entries = {}

        for game in GAMES:
            for stage in STAGES[game]:
                # Regular mode data first
                time_entries.update(self.get_regular_level_data(stage))
                # LTK Times
                time_entries.update(self.get_ltk_level_data(stage))
        return time_entries

    def get_yt_link(self, time_entry):
        """Returns youtube link if there is one, raises execptions if not."""

        response = requests.get(time_entry.url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        for tag in soup.find_all('a', href=True):
            if 'YouTube' in tag.text:
                return tag['href']
            elif ('Download video' in tag.text
                  and 'youtu' in tag['href']):
                return tag['href']
            elif 'Twitch' in tag.text:
                raise ValueError('Cannot download twitch video: %s'
                                 % tag['href'])
            elif 'Download video' in tag.text:
                raise ValueError('Manually download video %s'
                                 % tag['href'])

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
        yt_handle = YouTube(yt_link)
        if not os.path.isdir(vid_dirname):
            os.mkdir(vid_dirname)
        yt_handle.set_filename(vid_basename)
        # This will download the highest quality video
        hq_vid = sorted(yt_handle.videos, key=lambda x: x.resolution)[-1]
        hq_vid.download(vid_dirname)
        print('Downloaded video: %s' % time_entry.vid_path())

    def download_videos(self, dl_status=0):
        """Saves all videos with status equal to dl_status."""

        for time_entry in self.saved_entries.values():
            if time_entry.status != dl_status:
                continue
            try:
                yt_link = self.get_yt_link(time_entry)
            except ValueError as e:
                # TODO(dc): Log exception instead of print
                print(e)
                self.saved_entries[time_entry.url] = (
                    time_entry._replace(status=-1))
                continue
            try:
                self.download_yt_video(yt_link)
            except (pytube.exception.PytubeError,
                    pytube.exception.DoesNotExist,
                    pytube.exception.AgeRestricted) as e:
                print(e)
                print('Error downloading the video %s' % yt_link)
                self.saved_entries[time_entry.url] = (
                    time_entry._replace(status=-2))
                continue
            else:
                self.saved_entries[time_entry.url] = (
                    time_entry._replace(status=1))
