from pandas.core.frame import DataFrame
from requests_html  import  HTMLSession
from bs4 import BeautifulSoup
import pandas as pd
import time, random, unicodedata, os
from util import CollectedData

articles_csv = pd.read_csv("./sqr0.csv")
conference_papers_csv = pd.read_csv("./sqr1.csv")

###########################################################################################################
articles_data = CollectedData()
conference_papers_data  = CollectedData()
###########################################################################################################

#GET INFO
def convert_str_to_int(num):
    if num[-1] == 'k':
        b = int(num[:-1])
        b = b * 1000
        return b
    return int(num)

def collect_authors(attrs : dict, soup : BeautifulSoup, data_collector : CollectedData): 
    authors = []
    g_metrics = []
    author_tag_list = soup.find_all(attrs=attrs)
    for tag in author_tag_list:        
        authors.append(unicodedata.normalize("NFKD", tag.text.strip()))
    for i, author in enumerate(authors, start=0):
        print("\t[" + str(i) + "]  gs metric of : " + str(len(authors)-1)+ " author: "+author)
        g_metrics.append(articles_data.scrap_google_scholar_metrics(author))
    data_collector.data["authors"].append(authors)
    data_collector.data["googleScholarMetrics"].append(g_metrics)

def collect_metrics(find_tag : str, attrs : dict, child_tag : str, soup : BeautifulSoup, data_collector : CollectedData): 
    metrics = {"citations":0 ,"downloads":0 ,"accesses":0 , "altmetric":0}
    metric_tag_list = soup.find(find_tag, attrs)
    metric_tag_list = metric_tag_list.findChildren(child_tag)
    for child in metric_tag_list:
        k = child.text.strip().split()[1].lower()
        v = child.text.strip().split()[0]
        if k in metrics.keys():
            metrics[k] = convert_str_to_int(v)
    data_collector.data["metrics"].append(metrics)

def collect_abstract(find_tag : str, attrs : dict, child_tag : str, soup : BeautifulSoup, data_collector : CollectedData): 
    abstract = ""
    father_tag = soup.find(find_tag, attrs)
    if father_tag is not None:
        father_tag = father_tag.findChild(child_tag)
        abstract = father_tag.text.strip()
    data_collector.data["abstract"].append(abstract)

def collect_keywords(find_tag : str, attrs : dict, soup : BeautifulSoup, data_collector : CollectedData):
    keywords = []
    keywords_tag_list = soup.find_all(find_tag, attrs)
    for tag in keywords_tag_list:
        keywords.append(tag.text.strip())
    data_collector.data["keywords"].append(keywords)

def scrap_springer_link_articles(articles_csv : DataFrame, articles_data: CollectedData):
    for i, url in enumerate(articles_csv["URL"], start=0):
        session = HTMLSession()
        r = session.get(url)
        soup = BeautifulSoup(r.content, "html.parser")

        print("["+ str(i) + "] article of : " + str(len(articles_csv["URL"])-1) +" "+ url)   
        collect_authors({"data-test" : "author-name" }, soup, articles_data)        
        collect_metrics("ul", {"class" :  "c-article-metrics-bar"}, "p", soup, articles_data)
        collect_abstract("div", {"id" :  "Abs1-section"}, "p", soup, articles_data)
        collect_keywords("span", {"itemprop" : "about" }, soup, articles_data)
        session.close()   
        time.sleep(5)    
        os.system('clear') 
            
def scrap_springer_link_conference_papers(conference_papers_csv : DataFrame, conference_papers_data : CollectedData):
    for i, url in enumerate(conference_papers_csv["URL"], start=0):
        session = HTMLSession()
        r = session.get(url)        
        soup = BeautifulSoup(r.content, "html.parser")
        
        print("["+ str(i) + "] conference paper of : " + str(len(conference_papers_csv["URL"])-1) + " " +url)    
        collect_authors({"class" : "authors__name" }, soup, conference_papers_data)
        collect_metrics("ul", {"class" :  "article-metrics"}, "li", soup, conference_papers_data)
        collect_abstract("section", {"id" :  "Abs1"}, "p", soup, conference_papers_data)
        collect_keywords("span", {"class" : "Keyword" }, soup, conference_papers_data)
        session.close()
        time.sleep(5)    
        os.system('clear') 
        
scrap_springer_link_articles(articles_csv, articles_data)        
scrap_springer_link_conference_papers(conference_papers_csv, conference_papers_data)

#MERGE COLLECTED INFO INTO CSV
paper_data = {'Item Title' : [],
        'Publication Title' : [],
        'Item DOI' : [], 
        'Publication Year' : [],
        'URL' : [], 
        'Content Type' : [],
        
        'Authors': [], 
        'Abstract' : [],
        'Keywords' : [],
        #Metrics
        'Citations' : [],
        'Downloads' : [],
        'Accesses' : [],
        'Altmetric' : []
        }

author_data = {'Author' : [],
        'Citations' : [], 
        'Citations -5 Years' : [], 
        'H-index' : [], 
        'H-index -5 Years' : [], 
        'I10-index' : [],
        'I10-index -5 Years' : [] 
        }

def unite_paper_data(paper_data : 'dict[str, list]', data_collector : CollectedData, csv: DataFrame):
    for it, pt, id, py, u, ct,  authors, abstract, keywords, metrics in zip(csv["Item Title"], csv["Publication Title"], csv["Item DOI"], 
                                        csv["Publication Year"], csv["URL"], csv["Content Type"],
                                        data_collector.data["authors"], data_collector.data["abstract"], data_collector.data["keywords"],
                                        data_collector.data["metrics"]):
        paper_data["Item Title"].append(it)
        paper_data["Publication Title"].append(pt)
        paper_data["Item DOI"].append(id)
        paper_data["Publication Year"].append(py)
        paper_data["URL"].append(u)
        paper_data["Content Type"].append(ct)

        names = ""
        for au in authors:
            names = names + au.replace(";", "") + '; '
        names = names[:-2]
        paper_data["Authors"].append(names)

        paper_data["Abstract"].append(abstract)

        keyw = ""
        for k in keywords:
            keyw = keyw + k.replace(";", "") + '; '
        keyw = keyw[:-2]
        paper_data["Keywords"].append(keyw)


        paper_data["Citations"].append(metrics["citations"])
        paper_data["Downloads"].append(metrics["downloads"])
        paper_data["Accesses"].append(metrics["accesses"])
        paper_data["Altmetric"].append(metrics["altmetric"])

unite_paper_data(paper_data, articles_data, articles_csv)
unite_paper_data(paper_data, conference_papers_data, conference_papers_csv)

def unite_author_data(author_data : 'dict[str, list]', data_collector : CollectedData):
    for list_of_authors in data_collector.data['googleScholarMetrics']:        
        for author_dict in list_of_authors:
            if author_dict:
                author_data['Author'].append(author_dict["author"])
                author_data['Citations'].append(author_dict["citations"][0])
                author_data['Citations -5 Years'].append(author_dict["citations"][1])
                author_data['H-index'].append(author_dict["h-index"][0])
                author_data['H-index -5 Years'].append(author_dict["h-index"][1])
                author_data['I10-index'].append(author_dict["i10-index"][0])
                author_data['I10-index -5 Years'].append(author_dict["i10-index"][1])            

unite_author_data(author_data, articles_data)
unite_author_data(author_data, conference_papers_data)
   
df_papers = DataFrame(data=paper_data)
df_authors = DataFrame(data=author_data)

print(df_papers)
print()
print(df_authors)

df_papers.to_csv('./papers_info.csv', index=False)
df_authors.to_csv('./authors_info.csv', index=False)
