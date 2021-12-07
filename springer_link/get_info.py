from pandas.core.frame import DataFrame
from requests_html  import  HTMLSession
from bs4 import BeautifulSoup
import pandas as pd
import time, random, unicodedata

articles_csv = pd.read_csv("./sqr0.csv")
conference_papers_csv = pd.read_csv("./sqr1.csv")

class ColectedData:
    def __init__(self):
         self.data = {            
            "authors" : [], #[list: str] 
            "abstract" : [], #[string]            
            "keywords" : [], #[list: string]
            "metrics": [], #[dict]
            "googleScholarMetrics" : [] #[list(dicts)]
            # [[a1{author: str, cit: (All, Since), h_i : (All, Since), i10 : (All, Since) }, a2, ...] ...]
            }
    
    def scrap_google_scholar_metrics(self, author: str) -> dict:
        au_str = author.split()
        au_str_q=""
        for name in au_str:
            au_str_q = au_str_q + name + '+'
        au_str_q = au_str_q[:-1]
        query_url = "https://scholar.google.com/citations?hl=en&view_op=search_authors&mauthors=" + au_str_q + "&btnG="

        session = HTMLSession()
        r = session.get(query_url)
        soup = BeautifulSoup(r.content, "html.parser")
        nal = soup.find("h3",{"class" : "gs_ai_name"}) #NAME AND LINK
        if nal is None or nal.text.strip().lower() != author.lower():
            return {}
        link = nal.find_all("a", href=True)[0]['href']
        if random.randrange(3) == 0:
            time.sleep(random.uniform(3,7))            
        elif random.randrange(3) == 1:
           time.sleep(random.uniform(7,10))
        else:
            time.sleep(random.uniform(10,15))

        r = session.get("https://scholar.google.com"+link)
        soup = BeautifulSoup(r.content, "html.parser")
       
        values_tags = soup.find_all("td", {"class" : "gsc_rsb_std"})
        values = [x.text.strip() for x in values_tags]
        session.close()
        return {"author" : author,
                "citations" : (int(values[0]), int(values[1])), 
                "h-index" : (int(values[2]), int(values[3])), 
                "i10-index" : (int(values[4]), int(values[5]))
                }
       
###########################################################################################################
articles_data = ColectedData()
conference_papers_data  = ColectedData()
###########################################################################################################

#GET INFO
def convert_str_to_int(num):
    if num[-1] == 'k':
        b = int(num[:-1])
        b = b * 1000
        return b
    return int(num)

def collect_authors(attrs : dict, soup : BeautifulSoup, data_collector : ColectedData): 
    authors = []
    g_metrics = []
    author_tag_list = soup.find_all(attrs=attrs)
    for tag in author_tag_list:
        authors.append(unicodedata.normalize("NFKD", tag.text.strip()))
    for author in authors:
        g_metrics.append(articles_data.scrap_google_scholar_metrics(author))
    data_collector.data["authors"].append(authors)
    data_collector.data["googleScholarMetrics"].append(g_metrics)

def collect_metrics(find_tag : str, attrs : dict, child_tag : str, soup : BeautifulSoup, data_collector : ColectedData): 
    metrics = {"citations":0 ,"downloads":0 ,"accesses":0 , "altmetric":0}
    metric_tag_list = soup.find(find_tag, attrs)
    metric_tag_list = metric_tag_list.findChildren(child_tag)
    for child in metric_tag_list:
        k = child.text.strip().split()[1].lower()
        v = child.text.strip().split()[0]
        if k in metrics.keys():
            metrics[k] = convert_str_to_int(v)
    data_collector.data["metrics"].append(metrics)

def collect_abstract(find_tag : str, attrs : dict, child_tag : str, soup : BeautifulSoup, data_collector : ColectedData): 
    abstract = ""
    father_tag = soup.find(find_tag, attrs)
    if father_tag is not None:
        father_tag = father_tag.findChild(child_tag)
        abstract = father_tag.text.strip()
    data_collector.data["abstract"].append(abstract)

def collect_keywords(find_tag : str, attrs : dict, soup : BeautifulSoup, data_collector : ColectedData):
    keywords = []
    keywords_tag_list = soup.find_all(find_tag, attrs)
    for tag in keywords_tag_list:
        keywords.append(tag.text.strip())
    data_collector.data["keywords"].append(keywords)

def scrap_springer_link_articles(articles_csv : DataFrame, articles_data: ColectedData):
    for i, url in enumerate(articles_csv["URL"], start=0):
        session = HTMLSession()
        r = session.get(url)
        soup = BeautifulSoup(r.content, "html.parser")
        
        collect_authors({"data-test" : "author-name" }, soup, articles_data)        
        collect_metrics("ul", {"class" :  "c-article-metrics-bar"}, "p", soup, articles_data)
        collect_abstract("div", {"id" :  "Abs1-section"}, "p", soup, articles_data)
        collect_keywords("span", {"itemprop" : "about" }, soup, articles_data)
        r.close()
        time.sleep(5)    

def scrap_springer_link_conference_papers(conference_papers_csv : DataFrame, conference_papers_data : ColectedData):
    for i, url in enumerate(conference_papers_csv["URL"], start=0):
        session = HTMLSession()
        r = session.get(url)        
        soup = BeautifulSoup(r.content, "html.parser")
        
        collect_authors({"class" : "authors__name" }, soup, conference_papers_data)
        collect_metrics("ul", {"class" :  "article-metrics"}, "li", soup, conference_papers_data)
        collect_abstract("section", {"id" :  "Abs1"}, "p", soup, conference_papers_data)
        collect_keywords("span", {"class" : "Keyword" }, soup, conference_papers_data)
        r.close()
        time.sleep(5)    


scrap_springer_link_conference_papers(conference_papers_csv, conference_papers_data)
print()
scrap_springer_link_articles(articles_csv, articles_data)

#MERGE COLLECTED INFO INTO CSV


