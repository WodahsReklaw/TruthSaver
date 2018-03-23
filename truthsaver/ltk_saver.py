from bs4 import BeautifulSoup
import requests

EXAMPLE_PAGE = 'http://rankings.the-elite.net/perfect-dark/ltk/stage/defection'


#Returns String of HTML data from URL
def GetSoupFromURL(url):
  page = requests.get(url)
  try:
    page.raise_for_status()
  except:
    print("Error loading page: " + url)
    raise
  soup = BeautifulSoup(page.text, "html.parser")
  return soup


#Gets the html tables found and returns a list
def GetAllTableContent(one_table, times_list=None):
  if times_list is None:
    times_list = []
  tr_list = one_table.find_all('tr')
  for tr in tr_list:
    if tr.find(class_='video-link'):
      player_name = tr.find(class_='user').text
      time = tr.find(class_='time').text
      time_page = tr.find(class_='time').get('href')
      times_list.append({'name':player_name, 'time':time, 'page':time_page})
  return times_list


def main():
  soup = GetSoupFromURL(EXAMPLE_PAGE)
  table_list = soup.find_all('table')
  times_list = []
  for table in table_list:
    times_list = GetAllTableContent(table, times_list)
  for time in times_list:
    print(time)


if __name__ == "__main__":
  main()
