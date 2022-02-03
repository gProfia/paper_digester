import unicodedata
from requests_html  import  HTMLSession
import time, random 
from bs4 import BeautifulSoup
from util.DataNotFoundLogger import DataNotFoundLogger
from util.ScrapErrors import *
from util.ParserSearchString import *
from util.Util import *
import re
from selenium import webdriver
from config.PreConfig import GLOBAL_CONFIG

#singleton
logger = DataNotFoundLogger()
global_config = GLOBAL_CONFIG()

class CollectedData:
    def __init__(self, base : str, delay : int = 5):
        if base not in ["elsevier", "ieeex", "acm", "springer"]:
            raise BaseUndefinedError(base)                
        self.base = base
        self.paper_data = {       
            "item_title" : [] , #[str]
            "publication_title" : [], #[str]
            "item_DOI" : [], #[str]
            "publication_year" : [], #[str]
            "URL" : [], #[str]
            "content_type" : [], #[str]
            "authors" : [], #[list: str] 
            "abstract" : [], #[str]            
            "keywords" : [], #[list: str]
            #metrics
            "Citations": [], #[str]
            "Downloads": [], #[str]
            "Accesses": [], #[str]
            "Altmetric": [], #[str]

            "base" : [] #[str]
            }
        self.author_data = {
            'Author' : [],
            'Citations' : [], 
            'Citations -5 Years' : [], 
            'H-index' : [], 
            'H-index -5 Years' : [], 
            'I10-index' : [],
            'I10-index -5 Years' : [] 
        }
        self.query_url_attrib = {
                'domain' : '', 
                'pre_query' : '',
                'pre_query_pagination' : '',                
                'params' : '',
                'pagination_param' : '',
                'pagination_itens_per_page' : '',                
                'initial_url' : [] 
                }
        self.queries : 'list[str]' = []        
        self.init_pag_range : int = {"elsevier":1, "ieeex":2, "acm":1, "springer":2}[self.base]
        self.pagination_size : int = {"elsevier":25, "ieeex":25, "acm":20, "springer":20}[self.base]
        self.initial_amount_of_results = 0
        self.delay = delay
        self.content_type = ""
        self.content_type_abs = ""

        self.loop = False
        self.year_start = ""
        self.year_end = ""

    def mount_search_page_url(self, content_type : str, year_start : str, year_end : str,
     query : str):
        try:
            if not year_start or not year_end :
                year_start, year_end = '2020', '2021' 
            if not content_type:
                raise ContentTypeUndefinedError("empty")
            if content_type not in ['paper', 'article', 'chapter']:
                raise ContentTypeError(content_type)            
            self.content_type_abs = content_type
            self.year_start = year_start
            self.year_end = year_end

            if self.base == "springer":
                content_type = 'Article' if content_type == 'article' else ('Chapter' if content_type == 'chapter' else 'ConferencePaper')
                self.content_type = content_type
                p_open, p_close, space, d_quotes = '%28', '%29', '+', '%22'                        

                self.query_url_attrib['domain'] = 'https://link.springer.com'                
                self.query_url_attrib['pre_query'] = 'search'                
                self.query_url_attrib['pre_query_pagination'] = 'search/page/'                                
                self.queries = parse_search_query(self.base, query, p_open, p_close, space, d_quotes)                
                self.query_url_attrib['params'] = "?facet-content-type=" + d_quotes + content_type + d_quotes +\
                    '&date-facet-mode=between' + '&facet-start-year=' + year_start + '&facet-end-year=' + year_end +\
                    '&facet-language=' + d_quotes + 'En' + d_quotes + '&query=' + self.queries.pop()                                  
                self.query_url_attrib['initial_url'] = self.query_url_attrib['domain'] + '/' + self.query_url_attrib['pre_query'] +\
                    self.query_url_attrib['params'] 

            elif self.base == "acm":
                content_type = 'research-article' if content_type == 'article' else "short-paper"
                self.content_type = content_type
                p_open, p_close, space, d_quotes = '%28', '%29', '+', '%22'
                
                self.query_url_attrib['domain'] = 'https://dl.acm.org'                
                self.query_url_attrib['pre_query'] = 'action/doSearch'                
                self.queries = parse_search_query(self.base, query, p_open, p_close, space, d_quotes)                
                self.query_url_attrib['params'] = "?AllField=" + self.queries.pop() + "&expand=all" + "&ContentItemType="+ content_type +\
                    "&Ppub=[" + year_start + "0101" +"+TO+" + str((int(year_end)+1)) + "0101" +"]" # [= %5B ]= %5D
                self.query_url_attrib['pagination_param'] = "&startPage="
                self.query_url_attrib['pagination_itens_per_page'] = "&pageSize="
                self.query_url_attrib['initial_url'] = self.query_url_attrib['domain'] + '/' + self.query_url_attrib['pre_query'] +\
                    self.query_url_attrib['params'] 

            elif self.base == "ieeex":
                p_open, p_close, space, d_quotes = '(', ')', '%20', '%22'
                content_type = 'Early%20Access%20Articles' if content_type == 'article' else "Conferences"
                self.content_type = content_type

                self.query_url_attrib['domain'] = 'https://ieeexplore.ieee.org'                
                self.query_url_attrib['pre_query'] = 'search/searchresult.jsp'                
                self.queries = parse_search_query(self.base, query, p_open, p_close, space, d_quotes)                
                self.query_url_attrib['params'] = "?queryText=" + self.queries.pop() + "&highlight=true&returnFacets=ALL&returnType=SEARCH&matchPubs=true" +\
                    "&ranges=" + year_start + "_" + year_end + "_Year" + \
                    "&refinements=ContentType:" + content_type 
                self.query_url_attrib['pagination_param'] = "&pageNumber="
                self.query_url_attrib['initial_url'] = self.query_url_attrib['domain'] + '/' + self.query_url_attrib['pre_query'] +\
                    self.query_url_attrib['params'] 
                
            elif self.base == "elsevier":
                p_open, p_close, space, d_quotes = '%28', '%29', '%20', '%22'     

                content_type = 'FLA' if content_type == 'article' else "CH"
                self.content_type = content_type

                self.query_url_attrib['domain'] = 'https://www.sciencedirect.com'                
                self.query_url_attrib['pre_query'] = 'search'                
                if not self.loop:
                    self.queries = parse_search_query(self.base, query, p_open, p_close, space, d_quotes)                
                self.query_url_attrib['params'] = "?qs=" + self.queries.pop() + "&lastSelectedFacet=years" +\
                    "&articleTypes=" + content_type  +\
                    "&years=" + year_start + "%2C" + year_end  
                    
                self.query_url_attrib['pagination_param'] = "&offset="
                self.query_url_attrib['initial_url'] = self.query_url_attrib['domain'] + '/' + self.query_url_attrib['pre_query'] +\
                    self.query_url_attrib['params']
                
            else:
                raise BaseUndefinedError(self.base)    

        except BaseUndefinedError as err:
            print(err.message)
        except ContentTypeUndefinedError as err:
            print(err.message)
        except ContentTypeError as err:
            print(err.message)
       
        if global_config.DBG_FLAG:
            for a in self.query_url_attrib:
                print(a + ":\t" + self.query_url_attrib[a])                                

    def get_page(self, query_url : str, delay : int = 5) -> BeautifulSoup:
        options = webdriver.ChromeOptions() # Options()                        
        #options.headless = True            
        driver = webdriver.Chrome(global_config.CHROMEDRIVER_PATH, options=options)                        
        driver.get(query_url)
        time.sleep(delay)
        soup = BeautifulSoup(driver.page_source, "html.parser")            
        driver.quit()            
        time.sleep(self.delay)            
        return soup        

    def collect_links_to_inner_pages(self, outer_page : BeautifulSoup) -> 'list[str]':
        res = []
        if self.base == "springer":                                  
            link_tag_list = outer_page.find_all("a", attrs={"class" : "title"})
            if link_tag_list:
                for tag in link_tag_list:    
                    if tag['href']:
                        res.append(tag['href'])                            
            return res

        elif self.base == "acm":
            link_tag_list = outer_page.find_all("span", attrs={"class":"hlFld-Title"})
            if link_tag_list:
                for tag in link_tag_list:
                    if tag.find("a", recursive=False) and tag.find("a", recursive=False)['href']:
                        res.append(tag.find("a", recursive=False)['href'])                            
            return res

        elif self.base == "ieeex":
            link_tag_list = outer_page.find_all("div", attrs={"class":"List-results-items"})
            if link_tag_list:
                for tag in link_tag_list:
                    if tag.find('h2') and tag.find('h2').find("a", recursive=False) and tag.find('h2').find("a", recursive=False)['href']:
                        res.append(tag.find('h2').find("a", recursive=False)['href'])                            
            return res

        elif self.base == "elsevier":
            links = outer_page.find_all("a", {"class":"result-list-title-link"})
            if links:
                for tag in links:
                    if tag['href']:
                        res.append(tag['href'])                            
            return res
        else:
            raise BaseUndefinedError(self.base)                

    def collect_from_page(self, inner_page : BeautifulSoup, url : str):
        ct = self.content_type
        cta = self.content_type_abs
        base = self.base

        def collect_item_title(): 
            title = ""
            if self.base == "springer":            
                c = {'Article':"c-article-title", 'Chapter': "ChapterTitle", 'ConferencePaper' : "ChapterTitle"}[ct]
                title_tag = inner_page.find("h1", attrs={"class" : c})                
            elif self.base == "acm":
                title_tag = inner_page.find("h1", attrs={"class": "citation__title"})
            elif self.base == "ieeex":
                title_tag = inner_page.find("h1", {"class": "document-title"})
            elif self.base == "elsevier":                
                title_tag = inner_page.find("span", {"class":"title-text"})            
            else:
                raise BaseUndefinedError(self.base)     
            
            title = title_tag.text.strip() if title_tag else ""
            printd("Title: " + title)

        def collect_publication_title():
            publication_title = ""
            if self.base == "springer":            
                c = {'Article':{"data-test":"journal-link"}, 'Chapter': {"data-track-action":"Book title"}, 'ConferencePaper' : {"data-track-action" : "Book title"}}[ct]                
                p_title_tag = inner_page.find("a", attrs=c)
                publication_title = p_title_tag.text.strip() if p_title_tag is not None else ""                
            elif self.base == "acm":
                p_title_tag = inner_page.find("span", attrs={"class":"epub-section__title"})
                publication_title = p_title_tag.text.strip() if p_title_tag is not None else ""                
            elif self.base == "ieeex":            
                p_title_tag = inner_page.find("div", attrs={"class":"stats-document-abstract-publishedIn"})
                publication_title = (p_title_tag.find('a').text.strip() if p_title_tag.find('a') else "") if p_title_tag is not None else ""
            elif self.base == "elsevier":
                p_title_tag = inner_page.find("h2", attrs={"id":"publication-title"})
                if p_title_tag is not None:
                    publication_title = p_title_tag.text.strip()
                else:
                    p_title_tag = inner_page.find("h2", attrs={"class":"publication-title-link"})
                    if p_title_tag is not None:
                        publication_title = p_title_tag.text.strip()
                    else:
                        p_title_tag = inner_page.find("img", attrs={"class":"article-branding"})
                        if p_title_tag is not None and p_title_tag['alt'] is not None:
                            publication_title = p_title_tag['alt'].strip()
                        else:
                            p_title_tag = inner_page.find("div", attrs={"id":"publication"})
                            if p_title_tag is not None:
                                 publication_title = p_title_tag.text.strip()      
            else:
                raise BaseUndefinedError(self.base)   
            printd("Pub Title: " + publication_title)  
                        
        def collect_item_DOI():
            doi = ""
            if self.base == "springer":            
                c = {'Article':{"data-track-action":"view doi"}, 'Chapter': {"id":"doi-url"}, 'ConferencePaper' : {"id":"doi-url"}}[ct]                
                tag = {'Article':"a", 'Chapter': "span", 'ConferencePaper' : "span"}[ct]                
                doi_tag = inner_page.find(tag, attrs=c)
                if doi_tag:
                    doi = doi_tag.text.strip() 
                else:
                    c = {'Article':{"class":"c-bibliographic-information__list-item--doi"}, 'Chapter': {"id":"doi-url"}, 'ConferencePaper' : {"id":"doi-url"}}[ct]                
                    tag = {'Article':"li", 'Chapter': "span", 'ConferencePaper' : "span"}[ct]                
                    doi_tag = inner_page.find(tag, attrs=c)
                    if doi_tag:
                        doi = re.findall(r'(http.+)',doi_tag.text.strip())[0] if re.findall(r'(http*)',doi_tag.text.strip()) else ""
            elif self.base == "acm":            
                doi_tag = inner_page.find("a", attrs={"class":"issue-item__doi"})
                doi = doi_tag.text.strip() if doi_tag else ""
            elif self.base == "ieeex":
                doi_tag = inner_page.find("div", attrs={"class":"stats-document-abstract-doi"})
                doi = (doi_tag.find('a').text.strip() if doi_tag.find('a') else "") if doi_tag else ""                 
            elif self.base == "elsevier":
                doi_tag = inner_page.find("a", attrs={"class":"doi"})
                doi = doi_tag.text.strip() if doi_tag else ""
            else:
                raise BaseUndefinedError(self.base)     
            
            printd("Doi: " + doi)

        def collect_publication_year():
            publication_year = ""
            if self.base == "springer":            
                c = {'Article':{"data-test":"article-publication-year"}, 'Chapter': {"class":"article-dates__first-online"}, 'ConferencePaper' : {"class":"article-dates__first-online"}}[ct]                
                tag = {'Article':"span", 'Chapter': "span", 'ConferencePaper' : "span"}[ct]                
                year_tag = inner_page.find(tag, attrs=c) 
                if year_tag:
                    if ct == "Article":
                        publication_year = year_tag.text.strip()
                    else:
                        if len(year_tag.text.strip().split()) >= 3:
                            publication_year = year_tag.text.strip().split()[2]                       
            elif self.base == "acm":               
                year_tag = inner_page.find("span", attrs={"class":"epub-section__date"})                 
                if year_tag:
                    res = re.findall(r'([2][0][1-2][0-9]|[1][8-9][0-9]{2})',year_tag.text)
                    if res:
                        publication_year= res[0]                       
            elif self.base == "ieeex":
                year_tag = inner_page.find("div", attrs={"class":("doc-abstract-pubdate" if cta == "article" else "doc-abstract-confdate")})
                if year_tag:
                    res = re.findall(r'([2][0][1-2][0-9]|[1][8-9][0-9]{2})',year_tag.text.strip())
                    if res:
                        publication_year= res[0]                                                           
            elif self.base == "elsevier":               
                date_tag = inner_page.find_all("div", attrs={"class":"text-xs"})                
                if date_tag:
                    for tag in date_tag:
                        res = re.findall(r'([2][0][1-2][0-9]|[1][8-9][0-9]{2})',tag.text.strip())
                        if res:
                            publication_year= res[0]
                            break                           
            else:
                raise BaseUndefinedError(self.base)     
            printd("Pub Year: " + publication_year)

        def collect_URL(url : str):
            printd(url)
            
        def collect_content_type(ct: str):
            printd(ct)

        def collect_authors():
            authors=[]
            if self.base == "springer":            
                c = {'Article':{"data-test" : "author-name" }, 'Chapter': {"class":"authors__name"}, 'ConferencePaper' : {"class":"authors__name"}}[ct]                
                tag = {'Article':"a", 'Chapter': "span", 'ConferencePaper' : "span"}[ct]               
                tag_list = inner_page.find_all(tag, attrs=c) 
                if tag_list:
                    for tag in tag_list:
                        authors.append(unicodedata.normalize("NFKD", tag.text.strip()))                
            elif self.base == "acm":                
                tag_list = inner_page.find_all("div", attrs={"class":"author-data"}) 
                if tag_list:
                    for tag in tag_list:
                        if tag.find("span") and tag.find("span").find("span"):
                            authors.append(unicodedata.normalize("NFKD", tag.find("span").find("span").text.strip()))                
            elif self.base == "ieeex":
                tag = inner_page.find("div", attrs={"class":"authors-container"}) 
                if tag:
                    authors = list(map(lambda x: x.strip(), unicodedata.normalize("NFKD", tag.text.strip()).split(";")))            
            elif self.base == "elsevier":
                tag = inner_page.find("div", attrs={"id":"author-group"}) 
                if tag is not None:
                    al = tag.findAll("a", attrs={"class":"author"})
                    if al:
                        for x in al:
                            res = ""
                            name = x.find("span", {"class": "given-name"})
                            surname = x.find("span", {"class": "surname"})
                            if name:
                                res = res + unicodedata.normalize("NFKD",name.text.strip())
                            if surname:
                                res = res + " " + unicodedata.normalize("NFKD",surname.text.strip())
                            authors.append(res)   
            else:
                raise BaseUndefinedError(self.base)    
            printd("Authors: ", authors)

        def collect_abstract():
            abstract = ""
            if self.base == "springer":            
                att = {'Article':{"id" :  "Abs1-section"}, 'Chapter': {"id" :  "Abs1"} , 'ConferencePaper' :{"id" :  "Abs1"} }[ct]                
                tag = {'Article':"div", 'Chapter': "section", 'ConferencePaper' : "section"}[ct]               
                child_tag = {'Article':"p", 'Chapter': "p", 'ConferencePaper' : "p"}[ct]               
                father_tag = inner_page.find(tag, attrs=att) 
                if father_tag is not None:
                    father_tag = father_tag.findChild(child_tag)
                    if father_tag:
                        abstract = father_tag.text.strip()                
            elif self.base == "acm":
                father_tag = inner_page.find("div", attrs={"class":"abstractSection abstractInFull"})
                if father_tag is not None:
                    tag = father_tag.findChild("p")
                    if tag:
                        abstract = tag.text.strip()
            elif self.base == "ieeex":
                father_tag = inner_page.find("div", attrs={"class":"abstract-text"})            
                abstract = (father_tag.text.strip()[9:] if father_tag.text.strip()[:9] == "Abstract:" else father_tag.text.strip()) if father_tag else ""
            elif self.base == "elsevier":                
                father_tag = inner_page.find("div", attrs={"id":"abstracts"})            
                abstract = (father_tag.text.strip()[8:] if father_tag.text.strip()[:8] == "Abstract" else father_tag.text.strip()) if father_tag else "" 
            else:
                raise BaseUndefinedError(self.base)  
            printd("Abstract: " + abstract)

        def collect_keywords():
            keywords = []
            if self.base == "springer":                            
                att = {'Article':{"itemprop" : "about" }, 'Chapter': {"class" : "Keyword" } , 'ConferencePaper' :{"class" : "Keyword" }}[ct]                
                tag = {'Article':"span", 'Chapter': "span", 'ConferencePaper' : "span"}[ct]               
                keywords_tag_list = inner_page.find_all(tag, attrs=att)
                if keywords_tag_list:
                    for t in keywords_tag_list:
                        keywords.append(t.text.strip())
                else:
                    att = {'Article':{"class" : "c-article-subject-list__subject" }, 'Chapter': {"class" : "Keyword" } , 'ConferencePaper' :{"class" : "Keyword" }}[ct]                
                    tag = {'Article':"li", 'Chapter': "span", 'ConferencePaper' : "span"}[ct]               
                    keywords_tag_list = inner_page.find_all(tag, attrs=att)     
                    if keywords_tag_list:
                        for t in keywords_tag_list:
                            keywords.append(t.text.strip())                                   
            elif self.base == "acm":                
                keywords_tag_list = inner_page.find_all("ol", attrs={"class":"rlist"})                
                if keywords_tag_list:
                    kw = [x.find("p") for x in keywords_tag_list]
                    keywords = list(set([x.text.strip() for x in kw if x]))                
            elif self.base == "ieeex":                                
                tag_list = inner_page.find_all("a", {"class":"stats-keywords-list-item"})
                if tag_list:
                    keywords = list(set([x.text.strip() for x in tag_list if x]))
            elif self.base == "elsevier":                
                tag_list = inner_page.find_all("div", {"class":"keyword"})
                if tag_list:
                    keywords = list(map(lambda x: x.text.strip(), tag_list))
            else:
                raise BaseUndefinedError(self.base)  
            printd("Keywords: ", keywords)

        def collect_metrics():
            metrics = {"citations":0, "downloads":0, "accesses":0, "altmetric":0, "views":0, "mentions":0, "readers":0}        
            if self.base == "springer":                            
                #accesses and altmetric -> weak
                att = {'Article':{"class" :  "c-article-metrics-bar"}, 'Chapter':{"class" :  "article-metrics"} , 'ConferencePaper' :{"class" :  "article-metrics"}}[ct]                
                tag = {'Article':"ul", 'Chapter': "ul", 'ConferencePaper' : "ul"}[ct]               
                child_tag = {'Article':"p", 'Chapter': "li", 'ConferencePaper' : "li"}[ct]               
                find_tag = inner_page.find(tag, attrs=att)
                if find_tag:
                    tag_list = find_tag.findChildren(child_tag)
                    if tag_list:
                        for c in tag_list:
                            k = c.text.strip().split()[1].lower() if len(c.text.strip().split()) > 1 else ""
                            v = c.text.strip().split()[0] if c.text.strip().split() else ""
                            if k in metrics.keys():
                                metrics[k] = convert_str_to_int(v)                                    
            elif self.base == "acm":
                tag1 = inner_page.find("span", attrs={'class':'citation'})
                tag2 = inner_page.find("span", attrs={'class':'metric'})
                if tag1:
                    res = re.findall(r'([0-9]+)',tag1.text.strip().replace(',','').replace('.',''))
                    if res:                        
                        metrics["citations"] = int(res[0])
                if tag2:
                    res = re.findall(r'([0-9]+)',tag2.text.strip().replace(',','').replace('.',''))
                    if res:                        
                        metrics["downloads"] = int(res[0])                
            elif self.base == "ieeex":                                
                button_list = inner_page.find_all("button", {"class":"document-banner-metric"})
                if button_list:
                    raw_metrics = [x.text.strip() for x in button_list if x]
                    for x in raw_metrics:                    
                        k = 'citations' if 'citation' in x.lower() else 'views' if 'views' in x.lower() else ""
                        v = re.findall(r'([0-9]+)',x)[0]  if re.findall(r'([0-9]+)',x) else 0
                        if k in metrics.keys():                        
                            metrics[k] = int(v) + metrics[k]                  
            elif self.base == "elsevier":
                father_tag = inner_page.find("div", {"class":"pps-cols"})
                if father_tag is not None:
                    tag_list = father_tag.find_all("div", {"class":"pps-col"})
                    raw_metrics = [x.text.strip() for x in tag_list if x]
                    for x in raw_metrics:
                        k = 'readers' if 'readers' in x.lower() else 'citations' if 'citations' in x.lower() else 'mentions' if 'mentions' in x.lower() else "" 
                        res = re.findall(r'([0-9]+)', x)
                        v = res[0] if res else 0
                        if k in metrics.keys():
                            metrics[k] = int(v) + metrics[k]                    
            else:
                raise BaseUndefinedError(self.base)  
            printd("Metrics: ", metrics)

        def collect_base(base : str):
            printd(base)

        collect_item_title()
        collect_publication_title()        
        collect_item_DOI()    
        collect_publication_year()
        collect_URL(url)
        collect_content_type(cta)
        collect_authors()        
        collect_abstract()
        collect_keywords()            
        collect_metrics()         
        collect_base(base)
        printd("####################################################")   
        #collect_googleScholarMetrics():          

    def scrap_google_scholar_metrics(self, author: str) -> dict:
        gs_block : bool = None
        i = 1
        while gs_block != False:
            gs_block = False

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
                logger.register_gs_author_not_found(author)
                return {}
            link = nal.find_all("a", href=True)[0]['href']
            if random.randrange(3) == 0:
                time.sleep(random.uniform(20,27))            
            elif random.randrange(3) == 1:
                time.sleep(random.uniform(7,10))
            else:
                time.sleep(random.uniform(10,15))

            r = session.get("https://scholar.google.com"+link)
            soup = BeautifulSoup(r.content, "html.parser")
        
            values_tags = soup.find_all("td", {"class" : "gsc_rsb_std"})
            values = [x.text.strip() for x in values_tags]
            session.close()

            if len(values) != 6 or len(values) == 0 or not values[0].isnumeric():                
                gs_block = True
                printd()
                printd("########################### ["+str(i)+"]robot detected!!!###############################")
                printd()
                i = i + 1
                if i == 3:
                    logger.register_gs_author_not_found(author)
                    return {}
                time.sleep(200 + random.randrange(100))

        return {"author" : author,
                "citations" : (int(values[0]), int(values[1])), 
                "h-index" : (int(values[2]), int(values[3])), 
                "i10-index" : (int(values[4]), int(values[5]))
                }
               
    def execute(self):

        def scrap_number_of_pages(first_outer_page : BeautifulSoup) -> int:
            if self.base == "springer":               
                nop = first_outer_page.find("span", {"class" : "number-of-pages"})
                if nop is None:
                    return None
                return int(nop.get_text())

            elif self.base == "acm":                
                number_of_results = first_outer_page.find("span", {"class" : "hitsLength"})
                if number_of_results is None:
                    return None
                number_of_results :int = int(number_of_results.get_text().strip().replace(',',''))
                
                printd(number_of_results)
                
                if int( number_of_results / self.pagination_size ) == 0:
                    return 1
                if ( number_of_results % self.pagination_size) > 0:
                    return int(number_of_results / self.pagination_size) + 1
                return int(number_of_results / self.pagination_size)

            elif self.base == "ieeex":                         
                number_of_results = ""
                spans = first_outer_page.find("div", {"class" : "Dashboard-section"})
                if spans is not None:
                    if spans.find('span') is not None:
                        if spans.find('span').text.strip() == "No results found":
                            return 0
                        if spans.find('span').findAll('span') is not None and len(spans.find('span').findAll('span')) >=2:
                            number_of_results :int = int(spans.find('span').findAll('span')[1].text.strip().replace(',',''))
                        else:
                            return None
                    else: 
                        return None
                else:
                    return None

                printd(number_of_results)

                if int( number_of_results / self.pagination_size ) == 0:
                    return 1
                if ( number_of_results % self.pagination_size) > 0:
                    return int(number_of_results / self.pagination_size) + 1
                return int(number_of_results / self.pagination_size)

            elif self.base == "elsevier":                          
                tag = first_outer_page.find("ol", {"id":"srp-pagination"})
                tag_error = first_outer_page.find("div", {"class":"error-zero-results"})
                if tag_error is not None and "No results found".lower() in tag_error.text.strip().lower() :
                    return 0
                if tag is None or tag.find("li") is None:
                    return None
                if len(re.findall(r'([0-9]+)',tag.find("li").text.strip())) > 1:
                    max_page_number = re.findall(r'([0-9]+)',tag.find("li").text.strip())[1] 
                    printd(max_page_number)
                    return int(max_page_number)
                else:
                    return None
            else:
                raise BaseUndefinedError(self.base)                
        all_links : set = set()
        links : set = None
        flag_first = True
        while(self.queries or flag_first):
            first_search_page = self.get_page(self.query_url_attrib['initial_url'])
            number_of_pages : int = scrap_number_of_pages(first_search_page)
            if number_of_pages is None:
                first_search_page = self.get_page(self.query_url_attrib['initial_url'], delay=10)
                number_of_pages : int = scrap_number_of_pages(first_search_page)
            if number_of_pages is None:
                raise InsufficientDelayError("10 Seconds")
            if number_of_pages == 0:
                raise NoResultsForSearchStringError(self.base)
                #TODO: treat error and continue
            links : set = set(self.collect_links_to_inner_pages(first_search_page))
            
            printd(links)    
                
            #TODO: checar qtd de paginas é maior que um, ou se existem matchs para busca
            #   ACM:             
            #   if self.init_pag_range == number_of_pages:
            #                    break
            #   ELSEVIER:
            #   if number of pages = 1


            printd(self.init_pag_range, number_of_pages)
            for page_index in range(self.init_pag_range, (number_of_pages + 1 if self.base != "elsevier" else number_of_pages)):                        
                
                printd(self.base + ", " + self.content_type +    " page :" + str(page_index) + " of " + str(number_of_pages) )
                url : str = ""

                if self.base == "springer":
                    url = self.query_url_attrib['domain'] + '/' + self.query_url_attrib['pre_query_pagination'] \
                        + str(page_index) + self.query_url_attrib['params'] 
                
                elif self.base == "acm":                
                    url = self.query_url_attrib['domain'] + '/' + self.query_url_attrib['pre_query'] \
                        + self.query_url_attrib['params'] +  self.query_url_attrib['pagination_itens_per_page'] + str(self.pagination_size) \
                        +  self.query_url_attrib['pagination_param'] + str(page_index)                                  
                
                elif self.base == "ieeex":               
                    url = self.query_url_attrib['domain'] + '/' + self.query_url_attrib['pre_query'] \
                        + self.query_url_attrib['params'] +  self.query_url_attrib['pagination_itens_per_page'] + str(self.pagination_size) \
                        +  self.query_url_attrib['pagination_param'] + str(page_index)                                                  

                elif self.base == "elsevier":
                    url = self.query_url_attrib['domain'] + '/' + self.query_url_attrib['pre_query'] \
                        + self.query_url_attrib['params'] +  self.query_url_attrib['pagination_param'] + str(page_index * self.pagination_size)                                                                  

                else:
                    raise BaseUndefinedError(self.base)            
                
                outer_page : BeautifulSoup = self.get_page(url)                                    
                lol : 'list[str]' = self.collect_links_to_inner_pages(outer_page)
                links.update(lol)                                   
                all_links.update(links)

                if global_config.DBG_FLAG:
                    break
            if global_config.DBG_FLAG:
                break            
            
            flag_first = False 
            self.loop = True
            if self.queries:
                self.mount_search_page_url(self.content_type_abs, self.year_start, self.year_end, "")
                
        for doi_link in all_links:                        
            url=""
            if self.base == "springer":                
                url = self.query_url_attrib['domain'] + doi_link                                
                inner_page : BeautifulSoup = self.get_page(url)                                                    
                self.collect_from_page(inner_page, url)
                
            elif self.base == "acm":
                url = self.query_url_attrib['domain'] + doi_link                                
                inner_page : BeautifulSoup = self.get_page(url)                                                    
                self.collect_from_page(inner_page, url)

            elif self.base == "ieeex":
                url = self.query_url_attrib['domain'] + doi_link                                
                url = (url if url[-1:] == '/' else url + '/') + 'keywords#keywords'
                inner_page : BeautifulSoup = self.get_page(url)                                                    
                self.collect_from_page(inner_page, url)

            elif self.base == "elsevier":
                url = self.query_url_attrib['domain'] + doi_link                                
                inner_page : BeautifulSoup = self.get_page(url)                                                    
                self.collect_from_page(inner_page, url)
                
            else:
                raise BaseUndefinedError(self.base)                                    
            
    def register():
        pass