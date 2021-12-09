from pandas.core.frame import DataFrame
from requests_html  import  HTMLSession
from bs4 import BeautifulSoup
import pandas as pd
import time, random, unicodedata, os, math
from util.CollectedData import CollectedData

short_paper_url      = "https://dl.acm.org/action/doSearch?AllField=%28dependable+OR+dependability+OR+reliability+OR+availability+OR+maintainability+OR+safety+OR+reliable+OR+fault+tolerant+OR+qos+OR+security+OR+failure+OR+fault+OR+latent+error+OR+fault-avoidance+OR+fault-tolerance+OR+fault+removal+OR+fault+forecasting+OR+error-removal+OR+error-forecasting+OR+fault+avoidance+OR+fault+tolerance+OR+error+removal+OR+error+forecasting+OR+redundancy+OR+%28%28physical+OR+human-made+OR+design+OR+interaction+%29+AND+%28+faults%29%29+OR+elementary+failure+OR+%28%28corrective+OR+preventive%29+AND+maintenance%29+OR+%28error+AND+%28processing+OR+recovery+OR+compensation+OR+detection+OR+masking+%29%29+OR+confidentiality+integrity+availability+OR+security+attributes+OR+information+security+OR+vulnerabilities+OR+threats+OR+authenticity+OR+non-repudiation+OR+privacy+OR+auditability+OR+authentication%29+AND+%28+iiot+OR+fog+OR+iot+OR+m2m+OR+wsn+OR+iomt%29+AND+%28systems+OR+devices+OR+system+OR+device+OR+software+OR+hardware+OR+middleware+OR+component+OR+components+OR+computing+OR+service%29+&Ppub=%5B20191207+TO+20211207%5D&expand=all&startPage=&ContentItemType=short-paper"

research_article_url = "https://dl.acm.org/action/doSearch?AllField=%28dependable+OR+dependability+OR+reliability+OR+availability+OR+maintainability+OR+safety+OR+reliable+OR+fault+tolerant+OR+qos+OR+security+OR+failure+OR+fault+OR+latent+error+OR+fault-avoidance+OR+fault-tolerance+OR+fault+removal+OR+fault+forecasting+OR+error-removal+OR+error-forecasting+OR+fault+avoidance+OR+fault+tolerance+OR+error+removal+OR+error+forecasting+OR+redundancy+OR+%28%28physical+OR+human-made+OR+design+OR+interaction+%29+AND+%28+faults%29%29+OR+elementary+failure+OR+%28%28corrective+OR+preventive%29+AND+maintenance%29+OR+%28error+AND+%28processing+OR+recovery+OR+compensation+OR+detection+OR+masking+%29%29+OR+confidentiality+integrity+availability+OR+security+attributes+OR+information+security+OR+vulnerabilities+OR+threats+OR+authenticity+OR+non-repudiation+OR+privacy+OR+auditability+OR+authentication%29+AND+%28+iiot+OR+fog+OR+iot+OR+m2m+OR+wsn+OR+iomt%29+AND+%28systems+OR+devices+OR+system+OR+device+OR+software+OR+hardware+OR+middleware+OR+component+OR+components+OR+computing+OR+service%29+&Ppub=%5B20191207+TO+20211207%5D&expand=all&startPage=&ContentItemType=research-article"
a                    = "https://dl.acm.org/action/doSearch?AllField=%28dependable+OR+dependability+OR+reliability+OR+availability+OR+maintainability+OR+safety+OR+reliable+OR+fault+tolerant+OR+qos+OR+security+OR+failure+OR+fault+OR+latent+error+OR+fault-avoidance+OR+fault-tolerance+OR+fault+removal+OR+fault+forecasting+OR+error-removal+OR+error-forecasting+OR+fault+avoidance+OR+fault+tolerance+OR+error+removal+OR+error+forecasting+OR+redundancy+OR+%28%28physical+OR+human-made+OR+design+OR+interaction+%29+AND+%28+faults%29%29+OR+elementary+failure+OR+%28%28corrective+OR+preventive%29+AND+maintenance%29+OR+%28error+AND+%28processing+OR+recovery+OR+compensation+OR+detection+OR+masking+%29%29+OR+confidentiality+integrity+availability+OR+security+attributes+OR+information+security+OR+vulnerabilities+OR+threats+OR+authenticity+OR+non-repudiation+OR+privacy+OR+auditability+OR+authentication%29+AND+%28+iiot+OR+fog+OR+iot+OR+m2m+OR+wsn+OR+iomt%29+AND+%28systems+OR+devices+OR+system+OR+device+OR+software+OR+hardware+OR+middleware+OR+component+OR+components+OR+computing+OR+service%29+&Ppub=%5B20191207+TO+20211207%5D&expand=all&startPage=1&ContentItemType=research-article&pageSize=20"                
b                    = "https://dl.acm.org/action/doSearch?AllField=%28dependable+OR+dependability+OR+reliability+OR+availability+OR+maintainability+OR+safety+OR+reliable+OR+fault+tolerant+OR+qos+OR+security+OR+failure+OR+fault+OR+latent+error+OR+fault-avoidance+OR+fault-tolerance+OR+fault+removal+OR+fault+forecasting+OR+error-removal+OR+error-forecasting+OR+fault+avoidance+OR+fault+tolerance+OR+error+removal+OR+error+forecasting+OR+redundancy+OR+%28%28physical+OR+human-made+OR+design+OR+interaction+%29+AND+%28+faults%29%29+OR+elementary+failure+OR+%28%28corrective+OR+preventive%29+AND+maintenance%29+OR+%28error+AND+%28processing+OR+recovery+OR+compensation+OR+detection+OR+masking+%29%29+OR+confidentiality+integrity+availability+OR+security+attributes+OR+information+security+OR+vulnerabilities+OR+threats+OR+authenticity+OR+non-repudiation+OR+privacy+OR+auditability+OR+authentication%29+AND+%28+iiot+OR+fog+OR+iot+OR+m2m+OR+wsn+OR+iomt%29+AND+%28systems+OR+devices+OR+system+OR+device+OR+software+OR+hardware+OR+middleware+OR+component+OR+components+OR+computing+OR+service%29+&Ppub=%5B20191207+TO+20211207%5D&expand=all&startPage=2&ContentItemType=research-article&pageSize=20"


short_paper = "short-paper"
research_article="research-article"
base_link = "https://dl.acm.org"

paper_data = CollectedData()
article_data = CollectedData()

def length_of_content(soup : BeautifulSoup)-> int:
    #pg_count = soup.find("span", {"class" : "result__count"})
    seach_len = soup.find("span", {"class" : "hitsLength"})
    l = seach_len.text.strip().replace(",", "").replace(" ", "")
    return int(l) if l.isnumeric() else 0

def get_page_links(soup : BeautifulSoup):#-> 'list[str]':
    a = soup.find_all("span", {"class":"hlFld-Title"})
    for l in a:
        b = l.find_all("a")    
        for l1 in b:
            #print(l1.text.strip())
            print(l1["href"])

def scrap(content_type : str, data_collector : CollectedData):
    base_url = "https://dl.acm.org/action/doSearch?AllField=%28dependable+OR+dependability+OR+reliability+OR+availability+OR+maintainability+OR+safety+OR+reliable+OR+fault+tolerant+OR+qos+OR+security+OR+failure+OR+fault+OR+latent+error+OR+fault-avoidance+OR+fault-tolerance+OR+fault+removal+OR+fault+forecasting+OR+error-removal+OR+error-forecasting+OR+fault+avoidance+OR+fault+tolerance+OR+error+removal+OR+error+forecasting+OR+redundancy+OR+%28%28physical+OR+human-made+OR+design+OR+interaction+%29+AND+%28+faults%29%29+OR+elementary+failure+OR+%28%28corrective+OR+preventive%29+AND+maintenance%29+OR+%28error+AND+%28processing+OR+recovery+OR+compensation+OR+detection+OR+masking+%29%29+OR+confidentiality+integrity+availability+OR+security+attributes+OR+information+security+OR+vulnerabilities+OR+threats+OR+authenticity+OR+non-repudiation+OR+privacy+OR+auditability+OR+authentication%29+AND+%28+iiot+OR+fog+OR+iot+OR+m2m+OR+wsn+OR+iomt%29+AND+%28systems+OR+devices+OR+system+OR+device+OR+software+OR+hardware+OR+middleware+OR+component+OR+components+OR+computing+OR+service%29+&Ppub=%5B20191207+TO+20211207%5D&expand=all&startPage="
    content_type_url = "&ContentItemType=" + content_type
    page_count_url = "&pageSize=20"

    ACM_default_pagination = 20

    #1) GET NUMBER OF ARTICLES|PAPERS
    #mount url
    start_url = base_url + content_type_url
    session = HTMLSession()
    r = session.get(start_url)
    soup = BeautifulSoup(r.content, "html.parser")
    len_of_content = length_of_content(soup)
    
    # SET NUMBER OF OUTER LOOP ITERATIONS
    loop_iteractions = int(math.ceil(len_of_content / ACM_default_pagination ))
    # START OUTER LOOP(FOR PAGE)
    for page_index in range(loop_iteractions + 1):
        #mount url
        if page_index == 0:
            outer_page_url = base_url + content_type_url
        else:
            outer_page_url = base_url + str(page_index) + content_type_url + page_count_url
        
        r = session.get(outer_page_url)
        soup = BeautifulSoup(r.content, "html.parser")
        links = get_page_links(soup)
        # START INNER LOOP(FOR PAPER|ARTIGLE IN PAGE)

        break
        #       COLLECT DATA()
    #SYNTHETIZE COLLECTED DATA

def exec_scrap():
    scrap(short_paper, paper_data)
