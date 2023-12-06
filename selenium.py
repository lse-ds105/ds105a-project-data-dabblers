from selenium import webdriver
from selenium.webdriver.safari.service import Service  # If using Safari specifically
from selenium.webdriver.chrome.options import Options  # If you need specific browser options
from bs4 import BeautifulSoup  # For parsing HTML
import time  # For sleep


subreddits = ['https://www.reddit.com/r/tech/top/?t=month']

class ScrapeReddit():
    def __init__(self):
        # start headless if you want later on.
        options = Options()
        self.driver = webdriver.Safari(service=Service(executable_path='/usr/bin/safaridriver'), options=options)
       
        self.postids = []
    
    def lazy_scroll(self):
        current_height = self.driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
        while True:
            self.driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
            time.sleep(2)
            new_height = self.driver.execute_script('return document.body.scrollHeight')   
            if new_height == current_height:      # this means we have reached the end of the page!
                html = self.driver.page_source
                break
            current_height = new_height
        return html

    def get_posts(self):
        for link in subreddits:
            self.driver.get(link)
            self.driver.maximize_window()
            time.sleep(5)
            html = self.lazy_scroll()
            # html = self.driver.page_source
            parser = BeautifulSoup(html, 'html.parser')
            post_links = parser.find_all('a', {'slot': 'full-post-link'})
            print(len(post_links))
            count = 1

            for post_link in post_links:
                # generate a unique id for each post
                post_id = post_link['href'].split('/')[-3]
                print(f"{count} - {post_id}")
                count += 1
                if post_id not in self.postids:
                    self.postids.append(post_id)

    def destroy(self):
        self.driver.close()