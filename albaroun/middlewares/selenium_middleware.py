from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from scrapy.http import TextResponse
from scrapy.exceptions import CloseSpider
from scrapy import signals
import time

class SeleniumMiddleware(object):

    def __init__(self, s):
        # self.exec_path = s.get('PHANTOMJS_PATH', './phantomjs.exe')
        self.exec_path = s.get('C:/Users/phantomjs.exe')

###########################################################

    @classmethod
    def from_crawler(cls, crawler):
        obj = cls(crawler.settings)

        crawler.signals.connect(obj.spider_opened,
                                signal=signals.spider_opened)
        crawler.signals.connect(obj.spider_closed,
                                signal=signals.spider_closed)
        return obj

###########################################################

    def spider_opened(self, spider):
        try:
            self.d = init_driver(self.exec_path)
        except TimeoutException:
            CloseSpider('PhantomJS Timeout Error!!!')

###########################################################

    def spider_closed(self, spider):
        self.d.quit()
###########################################################
    
    def process_request(self, request, spider):
        if spider.use_selenium:
            print "############################ Received url request from scrapy #####"

            try:
                self.d.get(request.url)
                

            except TimeoutException as e:
                print "Timeout error"          
                #raise CloseSpider('TIMEOUT ERROR')
            time.sleep(2)

            if request.url == "https://angel.co/login":
                email_edit = self.d.find_element_by_xpath('//*[@id="user_email"]')
                pw_edit = self.d.find_element_by_xpath('//*[@id="user_password"]')
                login_button = self.d.find_element_by_xpath('//*[@class="c-button c-button--blue s-vgPadLeft1_5 s-vgPadRight1_5"]')
                if email_edit and pw_edit and login_button:
                    time.sleep(1)
                    email_edit.click()
                    email_edit.send_keys("josec1126@yahoo.com")
                    # email_edit.send_keys("bbanzzakji@gmail.com")
                    time.sleep(1)
                    pw_edit.click()
                    pw_edit.send_keys("WeLivv16")
                    # pw_edit.send_keys("Jin1234%")
                    time.sleep(1)
                    login_button.click()
                    time.sleep(5)

            elif request.url == "https://www.linkedin.com/":
                email_edit = self.d.find_element_by_xpath('//*[@id="login-email"]')
                pw_edit = self.d.find_element_by_xpath('//*[@id="login-password"]')
                login_button = self.d.find_element_by_xpath('//*[@id="login-submit"]')
                if email_edit and pw_edit and login_button:

                    email_edit.click()
                    # email_edit.send_keys("pe.dev324@yahoo.com")
                    email_edit.send_keys("hwangtailong@yahoo.com")
                    time.sleep(0.5)
                    pw_edit.click()
                    # pw_edit.send_keys("Jinyong!")
                    pw_edit.send_keys("Jin1234%")
                    time.sleep(0.5)
                    login_button.click()
                    time.sleep(5)


            elif request.url == "https://adiglobal.us/Pages/WebRegistration.aspx":
                email_edit = self.d.find_element_by_xpath('//*[@id="ctl00_PlaceHolderMain_ctl00_ctlLoginView_MainLoginView_MainLogin_UserName"]')
                pw_edit = self.d.find_element_by_xpath('//*[@id="ctl00_PlaceHolderMain_ctl00_ctlLoginView_MainLoginView_MainLogin_Password"]')
                login_button = self.d.find_element_by_xpath('//*[@id="ctl00_PlaceHolderMain_ctl00_ctlLoginView_MainLoginView_MainLogin_LoginButton"]')
                if email_edit and pw_edit and login_button:

                    email_edit.click()
                    # email_edit.send_keys("pe.dev324@yahoo.com")
                    email_edit.send_keys("pcarson7")
                    time.sleep(0.5)
                    pw_edit.click()
                    # pw_edit.send_keys("Jinyong!")
                    pw_edit.send_keys("Dil11lon")
                    time.sleep(0.5)
                    login_button.click()
                    time.sleep(15)

            # lastHeight = self.d.execute_script("return document.body.scrollHeight")
            # print "*** Last Height = ", lastHeight
            # while True:
            #     self.d.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            #     time.sleep(2)
            #     newHeight = self.d.execute_script("return document.body.scrollHeight")
            #     if newHeight == lastHeight:
            #         break
            #     lastHeight = newHeight
            time.sleep(2.5)
            resp = TextResponse(url=self.d.current_url,
                                body=self.d.page_source,
                                encoding='utf-8')
            resp.request = request.copy()
            
            return resp

###########################################################
###########################################################

def init_driver(path):
    d = webdriver.PhantomJS(executable_path='C:/Users/jin/phantomjs.exe')
    # d = webdriver.Firefox()
    d.set_page_load_timeout(50)

    return d