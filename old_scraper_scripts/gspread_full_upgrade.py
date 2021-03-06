# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import urllib.request
import math
import pandas as pd
from gspread_pandas import Spread
import os

from pyvirtualdisplay import Display

from selenium import webdriver


# Indeed.ie Scraper
class IndeedScraper(object):
    def __init__(self, role):
        self.role = role
        #self.url = 'https://ie.indeed.com/jobs?as_and={}&radius=25&l=Dublin&fromage=7&limit=50&sort=date&start=0'.format(role)
        self.url = 'https://ie.indeed.com/jobs?as_and=&as_phr=&as_any={}&radius=25&l=Dublin&fromage=7&limit=50&sort=date&start=0'.format(role)

     # Makes the soup
    def getPageSource(self):
      hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
           'Accept-Encoding': 'none',
           'Accept-Language': 'en-US,en;q=0.8',
           'Connection': 'keep-alive'}
      req = urllib.request.Request(self.url, headers=hdr)
      page = urllib.request.urlopen(req)
      soup = BeautifulSoup(page, "html.parser")
      return(soup)
    
     #Finds number of pages given the term provided       
    def find_pages(self):
        pages = []
        html_page = urllib.request.urlopen(self.url)
        source = BeautifulSoup(html_page, "html.parser")
        base_url = 'https://ie.indeed.com'
        for a in source.find_all('div', class_= 'pagination'):
          for link in a.find_all('a', href=True):
            pages.append(base_url + link['href'])
        pages.insert(0, base_url + '/jobs?as_and={}&radius=25&l=Dublin&fromage=7&limit=50&sort=date&start=0'.format(self.role))
        pages.pop()
        return pages

    #Iterates through the pages
    def iterate_pages(self, pages):
      l_main = []
      cont = 1
      for i in pages:
        html_page = urllib.request.urlopen(i)
        source = BeautifulSoup(html_page, "html.parser")
        print("Scraping Page number: " + str(cont))
        results = indeed.find_info(source)
        cont +=1
        l_main.extend(results)
      return(l_main)

    # Scrapes each page to pull the Company, Role, URL and Date  
    def find_info(self, soup):
      l = []
      for info in soup.find_all("td",  {"id": "resultsCol"}):
        for div in info.find_all('div', {"data-tn-component": "organicJob"}):
          d = {}
          try:
            link = div.find('div', class_= 'title').find('a')
            role = link.get_text().strip()
            d["Company"] = div.find('span', class_= 'company').get_text().strip()
            d["Role"] = role
            d["URL"] = 'http://www.indeed.com' + link['href']
            d["Date"] = div.find('span', class_= 'date').get_text().strip()
            l.append(d)
          except:
            pass
      return l
    
    # Clean df to work with
    def results_to_df(self, l_main):
      df = pd.DataFrame(l_main)
      df = df[['Date', 'Company', 'Role', 'URL']]
      df=df.dropna()
      df.sort_values(by=['Date'], inplace=True, ascending=False)
      return df

    # Stores the results in a pandas DataFrame
    def store_results(self, l_main, s):
      df = pd.DataFrame(l_main)
      df = df[['Date', 'Company', 'Role', 'URL']]
      df=df.dropna()
      df.sort_values(by=['Date'], inplace=True, ascending=False)
      s.df_to_sheet(df, sheet='Indeed', start=(1,1), replace=True, index=False)


# Irish Jobs Scraper      
class IrishJobs(object):
  def __init__(self, role):
        self.role = role
        self.url = 'https://www.irishjobs.ie/ShowResults.aspx?Keywords={}&Location=102&Category=3&Recruiter=All&SortBy=MostRecent&PerPage=100'.format(role)
  
  # Makes the soup
  def getPageSource(self):
    hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
         'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
         'Accept-Encoding': 'none',
         'Accept-Language': 'en-US,en;q=0.8',
         'Connection': 'keep-alive'}
    req = urllib.request.Request(self.url, headers=hdr)
    page = urllib.request.urlopen(req)
    soup = BeautifulSoup(page, "html.parser")
    return(soup)
			
	# Finds the data according to the search term provided
  def find_data(self, soup):
    base_url = 'https://www.irishjobs.ie/'
    l_main = []
    for a in soup.find_all(attrs={"itemtype" : "https://schema.org/JobPosting"}):
      d = {}
      job_info = a.find('h2').find('a')
      try:
        d["Company"] = a.find('h3').find('a').get_text()  
      except:
        pass
      url = job_info['href']
      d["URL"] = (base_url + url)
      d["Role"] = (job_info.get_text())
      d["Date"] = a.find('li',class_='updated-time').get_text().replace('Updated','').strip()
      d["Date"] = pd.to_datetime(d["Date"], format='%d/%m/%Y')
      l_main.append(d)
    return l_main
  
  # Clean df to work with
  def results_to_df(self, l_main):
    df = pd.DataFrame(l_main)
    df = df[['Date', 'Company', 'Role', 'URL']]
    df=df.dropna()
    df.sort_values(by=['Date'], inplace=True, ascending=False)
    return df

  # Stores the results in a pandas DataFrame
  def store_results(self, l_main, s):
    df = pd.DataFrame(l_main)
    df = df[['Date', 'Company', 'Role', 'URL']]
    df=df.dropna()
    df.sort_values(by=['Date'], inplace=True, ascending=False)
    s.df_to_sheet(df, sheet='Irish_Jobs', start=(1,1), replace=True, index=False)

    
# Monster class
class Monster(object):
  def __init__(self, role):

    #Options for Codenvy box
    chrome_driver_path = '/usr/local/bin/chromedriver'
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    self.role = role
    self.url = 'https://www.monster.ie/jobs/search/?cy=ie&q={}&&rad=20&where=dublin&tm=7&stpage=1&page=10'.format(role)
    self.driver = webdriver.Chrome(chrome_driver_path, chrome_options=chrome_options)

    # Options for Local box
#    self.role = role
#    self.url = 'https://www.monster.ie/jobs/search/?cy=ie&q={}&&rad=20&where=dublin&tm=7&stpage=1&page=10'.format(role)
#    self.driver = webdriver.Chrome(executable_path='/usr/lib/chromium-browser/chromedriver')


  def getPageSource(self):
    self.driver.get(self.url)
    url_code = self.driver.page_source
    self.driver.close()
    soup = BeautifulSoup(url_code, "html.parser")
    return(soup)


# # Function to scrape all jobs per page
#   def find_data(self, soup):
#     l = []
#     for div in soup.find_all('div', class_ = 'flex-row'):
#         d = {}
#         try:
#             d["Company"] = div.find('div', class_='summary').find('div', class_='company').find('a').get_text()
#             d["Date"] = div.find('div', {'class':['meta', 'flex-col']}).find('time').get_text()
#             pholder = div.find('header', class_= 'card-header').find('h2').find('a')
#             d["URL"] = pholder['href']
#             d["Role"] = div.find('header', class_= 'card-header').find('h2').find('a').get_text().strip()
#             l.append(d)
#         except:
#             pass
#     return l


# Function to scrape all jobs per page
  def find_data(self, soup):
    l = []
    for div in soup.find_all("section",  {"class": ["card-content", "is-bold", "is-active", "featured-ad"]}):
        d = {}
        try:
            d["Company"] = div.find('div', class_='flex-row').find('div', class_='summary').find('div', class_='company').find('a').get_text()
            d["Date"] = div.find('div', class_='flex-row').find('div', {'class':['meta', 'flex-col']}).find('time').get_text()
            pholder = div.find('div', class_='flex-row').find('header', class_= 'card-header').find('h2').find('a')
            d["URL"] = pholder['href']
            d["Role"] = div.find('div', class_='flex-row').find('header', class_= 'card-header').find('h2').find('a').get_text().strip()
            l.append(d)
        except:
            pass
    return l

   
  # Clean df to work with
  def results_to_df(self, l):
    df = pd.DataFrame(l)
    df = df[['Date', 'Company', 'Role', 'URL']]
    df=df.dropna()
    df.sort_values(by=['Date'], inplace=True, ascending=False)
    return df

  # Stores the results in a pandas DataFrame
  def store_results(self, l, s):
    df = pd.DataFrame(l)
    df = df[['Date', 'Company', 'Role', 'URL']]
    df=df.dropna()
    df.sort_values(by=['Date'], inplace=True, ascending=False)
    s.df_to_sheet(df, sheet='Monster', start=(1,1), replace=True, index=False)


# Computer Jobs Scraper class
class Computer(object):
  def __init__(self, role):
        self.role = role
        self.url = 'https://www.computerjobs.ie/jobboard/cands/JobResults.asp?c=1&strKeywords={}&lstPostedDate=7&lstRegion=Central+Dublin&lstRegion=South+Dublin&lstRegion=North+Dublin&lstRegion=West+Dublin&pg=1'.format(role)
        
  def getPageSource(self, url):
    hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}
    req = urllib.request.Request(url, headers=hdr)
    html_page = urllib.request.urlopen(req)
    soup = BeautifulSoup(html_page, "html.parser")
    return(soup)

  def get_number_pages(self):
    soup = computer.getPageSource(self.url)
    num_results = soup.find("strong").contents
    makeitastring = ''.join(map(str, num_results))
    temp = (int(makeitastring)) / 10
    page_no = math.ceil(temp)
    return(page_no)

  def find_data(self, soup):
    l = []
    for b in soup.find_all('div', class_= 'jobInfo'):
      d = {}
      company = b.find('h2').find('a')
      d["Role"] = company['title'].split(':')[0]
      d["URL"] = 'https://www.computerjobs.ie' + company['href']
      company_name = b.find('ul', class_= 'jobDetails').find('li', class_= 'jobCompanyName').get_text()
      d["Company"] = company_name.split(':')[1].strip()
      date = b.find('ul', class_= 'jobDetails').find('li', class_= 'jobLiveDate').get_text()
      d["Date"] = date.split(':')[1].strip()
      l.append(d)
    return l
  
  def iterate_pages(self, no_pages):
    l_main = []
    for i in range(no_pages):
      page = self.url[:-1] + str(i+1)
      soup = computer.getPageSource(page)
      print("Scraping Page number: " + str(i+1))
      l_main.extend(computer.find_data(soup))
    return(l_main)

  # Clean df to work with
  def results_to_df(self, l_main):
    df = pd.DataFrame(l_main)
    df = df[['Date', 'Company', 'Role', 'URL']]
    df=df.dropna()
    df.sort_values(by=['Date'], inplace=True, ascending=False)
    return df
  
  # Stores the results in a pandas DataFrame
  def store_results(self, l_main, s):
    df = pd.DataFrame(l_main)
    df = df[['Date', 'Company', 'Role', 'URL']]
    df=df.dropna()
    df.sort_values(by=['Date'], inplace=True, ascending=False)
    s.df_to_sheet(df, sheet='Computer_Jobs', start=(1,1), replace=True, index=False)
    return df
  

    
if __name__ == '__main__':
  
  display = Display(visible=0, size=(1920, 1080)).start()

  os.system('clear')
  running = True
  
  while running:

    print('\n')
    print('###############################################################')
    print('         Job Scraper - Copyright Mariano Vazquez, 2019'         )
    print('###############################################################')
    print('\n')
    
    print('1) Indeed        4) Computer Jobs')
    print('2) IrishJobs     5) All of them')
    print('3) Monster       6) Quit')

    choice = str(input("\nMake your choice: "))
    
    if choice == '1':

      s = Spread('scraper', 'pandas')
      role = str(input("\nEnter role to search: "))
      print('')

      indeed = IndeedScraper(role)
      soup = indeed.getPageSource()

      pages = indeed.find_pages()
      #print('# Indeed Scraper >> {} pages found'.format(len(pages)))
      #max_pages = int(input('# Enter number of pages to scrape: '))
      #print('\n')

      results_list = indeed.iterate_pages(pages)
      #results_list = indeed.find_info(soup)
      indeed.store_results(results_list, s)
      os.system('clear')
    
    elif choice == '2':

      s = Spread('scraper', 'pandas')
      
      role = input('\nEnter role to search: ')
      print('\n>>> Irish Jobs Scraper >> Searching jobs, please wait..')

      irish_jobs = IrishJobs(role)
      soup = irish_jobs.getPageSource()

      results_list = irish_jobs.find_data(soup)
      irish_jobs.store_results(results_list, s)
      
      os.system('clear')
      
    elif choice == '3':
      
      s = Spread('scraper', 'pandas')
      role = input('\nEnter role to search: ')
      print('\nGrabbing all the jobs, Hang in there...')
      
      monster = Monster(role)
      soup = monster.getPageSource()
      results = monster.find_data(soup)

      monster.store_results(results, s)
      os.system('clear')
    
    elif choice == '4':
      
      s = Spread('scraper', 'pandas')

      role = input('\nEnter role to search: ')
      print('\n>>> Computer Jobs Scraper >> Searching jobs, please wait..')
      print('')
      
      computer = Computer(role)

      no_pages = computer.get_number_pages()
      results = computer.iterate_pages(no_pages)
      computer.store_results(results, s)
      os.system('clear')
      
    elif choice == '5':
      
      s = Spread('scraper', 'pandas')

      role = input('\nEnter role to search: ')
      os.system('clear')
      print('\n>>> Scraping ALL Sites for jobs, please wait..')
      print('\n>>> Indeed Jobs Scraper >> Searching jobs, please wait..')
      #print('')
      
      # Indeed Scraper
      s = Spread('scraper', 'pandas')


      indeed = IndeedScraper(role)
      soup = indeed.getPageSource()

      pages = indeed.find_pages()

      results_list = indeed.iterate_pages(pages)
      #results_list = indeed.find_info(soup)
      indeed.store_results(results_list, s)

      #pages = indeed.find_pages()
      #print('# Indeed Scraper >> {} pages found'.format(len(pages)))
      #max_pages = int(input('# Enter number of pages to scrape: '))
      #print('\n')

      #results_list = indeed.iterate_pages(pages, max_pages)
      #indeed_xls = indeed.results_to_df(results_list)
      
      os.system('clear')
      
      # Irish Jobs Scraper
      print('\n>>> Scraping ALL Sites for jobs, please wait..')
      print('\n>>> Irish Jobs Scraper >> Searching jobs, please wait..')
      irish_jobs = IrishJobs(role)
      
      soup = irish_jobs.getPageSource()
      results_list = irish_jobs.find_data(soup)
      irish_xls = irish_jobs.results_to_df(results_list)
      irish_jobs.store_results(irish_xls, s)

      os.system('clear')
      
      # Monster Scraper
      print('\n>>> Scraping ALL Sites for jobs, please wait..')
      print('\n>>> Monster Scraper >> Searching jobs, please wait..')
      
      monster = Monster(role)

      soup = monster.getPageSource()
      results = monster.find_data(soup)
      monster_xls = monster.results_to_df(results)
      monster.store_results(monster_xls, s)

      os.system('clear')
      
      # Computer Jobs Scraper
      print('\n>>> Scraping ALL Sites for jobs, please wait..')
      print('\n>>> Computer Jobs Scraper >> Searching jobs, please wait..')
      
      computer = Computer(role)
      
      no_pages = computer.get_number_pages()
      results = computer.iterate_pages(no_pages)

      computer_xls = computer.results_to_df(results)
      computer.store_results(computer_xls, s)
      
      os.system('clear')
    
    elif choice == '6':
      running = False
print('\nProgram ending... Bye!')