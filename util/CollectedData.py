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
from selenium.webdriver.chrome.options import Options
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
        self.init_pag_range : int = {"elsevier":0, "ieeex":2, "acm":1, "springer":2}[self.base]
        self.pagination_size : int = {"elsevier":0, "ieeex":25, "acm":20, "springer":20}[self.base]
        self.initial_amount_of_results = 0
        self.delay = delay
        self.content_type = ""
        self.content_type_abs = ""

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
                    "&ranges=" + year_start + "_" + year_end + "_" + \
                    "&refinements=ContentType:" + content_type 
                self.query_url_attrib['pagination_param'] = "&pageNumber="
                self.query_url_attrib['initial_url'] = self.query_url_attrib['domain'] + '/' + self.query_url_attrib['pre_query'] +\
                    self.query_url_attrib['params'] 
                
            elif self.base == "elsevier":
                p_open, p_close, space = '%28', '%29', '%20'     
                a="https://www.sciencedirect.com/search?qs=%28%28dependable%20OR%20fault%20OR%20failure%29%20AND%20%28iot%20OR%20m2m%29%20AND%20%28systems%20OR%20devices%29%29"
                pass
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
        if self.base in ["springer", 'acm', 'elsevier']:
            session = HTMLSession()
            r = session.get(query_url)
            soup = BeautifulSoup(r.content, "html.parser")
            session.close()
            time.sleep(self.delay)            
            return soup        
        else: 
            options = Options()
            options.headless = True            
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
            for tag in link_tag_list:                
                res.append(tag['href'])                            
            return res

        elif self.base == "acm":
            link_tag_list = outer_page.find_all("span", attrs={"class":"hlFld-Title"})
            for tag in link_tag_list:
                res.append(tag.find("a", recursive=False)['href'])                            
            return res

        elif self.base == "ieeex":
            link_tag_list = outer_page.find_all("div", attrs={"class":"List-results-items"})
            for tag in link_tag_list:
                res.append(tag.find('h2').find("a", recursive=False)['href'])                            
            return res

        elif self.base == "elsevier":
            pass
        else:
            raise BaseUndefinedError(self.base)                

    def collect_from_page(self, inner_page : BeautifulSoup, url : str):
        ct = self.content_type
        cta = self.content_type_abs
        base = self.base

        def collect_item_title(): 
            if self.base == "springer":            
                c = {'Article':"c-article-title", 'Chapter': "ChapterTitle", 'ConferencePaper' : "ChapterTitle"}[ct]
                title_tag = inner_page.find("h1", attrs={"class" : c})
                printd(title_tag.text.strip())
                
            elif self.base == "acm":
                title_tag = inner_page.find("h1", attrs={"class": "citation__title"})
                printd(title_tag.text.strip())

            elif self.base == "ieeex":
                title_tag = inner_page.find("h1", {"class": "document-title"})
                printd(title_tag.text.strip())

            elif self.base == "elsevier":
                pass
            else:
                raise BaseUndefinedError(self.base)     
            
        def collect_publication_title():
            if self.base == "springer":            
                c = {'Article':{"data-test":"journal-link"}, 'Chapter': {"data-track-action":"Book title"}, 'ConferencePaper' : {"data-track-action" : "Book title"}}[ct]                
                p_title_tag = inner_page.find("a", attrs=c)
                printd(p_title_tag.text.strip())
                
            elif self.base == "acm":
                p_title_tag = inner_page.find("span", attrs={"class":"epub-section__title"})
                printd(p_title_tag.text.strip())

            elif self.base == "ieeex":
                pass
            elif self.base == "elsevier":
                pass
            else:
                raise BaseUndefinedError(self.base)     
                        
        def collect_item_DOI():
            if self.base == "springer":            
                c = {'Article':{"data-track-action":"view doi"}, 'Chapter': {"id":"doi-url"}, 'ConferencePaper' : {"id":"doi-url"}}[ct]                
                tag = {'Article':"a", 'Chapter': "span", 'ConferencePaper' : "span"}[ct]                
                doi_tag = inner_page.find(tag, attrs=c)
                printd(doi_tag.text.strip())
                
            elif self.base == "acm":            
                doi_tag = inner_page.find("a", attrs={"class":"issue-item__doi"})
                printd(doi_tag.text.strip())

            elif self.base == "ieeex":
                pass
            elif self.base == "elsevier":
                pass
            else:
                raise BaseUndefinedError(self.base)     
            
        def collect_publication_year():
            if self.base == "springer":            
                c = {'Article':{"data-test":"article-publication-year"}, 'Chapter': {"class":"article-dates__first-online"}, 'ConferencePaper' : {"class":"article-dates__first-online"}}[ct]                
                tag = {'Article':"span", 'Chapter': "span", 'ConferencePaper' : "span"}[ct]                
                year_tag = inner_page.find(tag, attrs=c) 
                printd(year_tag.text.strip() if ct == "Article" else year_tag.text.strip().split()[2])
                
            elif self.base == "acm":               
                year_tag = inner_page.find("span", attrs={"class":"epub-section__date"})                 
                printd(re.findall(r'([1-3][0-9]{3})',year_tag.text)[0])

            elif self.base == "ieeex":
                pass
            elif self.base == "elsevier":
                pass
            else:
                raise BaseUndefinedError(self.base)     

        def collect_URL(url : str):
            printd(url)
            
        def collect_content_type(ct: str):
            printd(ct)

        def collect_authors():
            if self.base == "springer":            
                c = {'Article':{"data-test" : "author-name" }, 'Chapter': {"class":"authors__name"}, 'ConferencePaper' : {"class":"authors__name"}}[ct]                
                tag = {'Article':"a", 'Chapter': "span", 'ConferencePaper' : "span"}[ct]               
                tag_list = inner_page.find_all(tag, attrs=c) 
                a = []
                for tag in tag_list:
                    a.append(unicodedata.normalize("NFKD", tag.text.strip()))                
                printd(a)

            elif self.base == "acm":                
                tag_list = inner_page.find_all("div", attrs={"class":"author-data"}) 
                a = []
                for tag in tag_list:
                    a.append(unicodedata.normalize("NFKD", tag.find("span").find("span").text.strip()))                
                printd(a)

            elif self.base == "ieeex":
                pass
            elif self.base == "elsevier":
                pass
            else:
                raise BaseUndefinedError(self.base)    

        def collect_abstract():
            if self.base == "springer":            
                abs = ""
                att = {'Article':{"id" :  "Abs1-section"}, 'Chapter': {"id" :  "Abs1"} , 'ConferencePaper' :{"id" :  "Abs1"} }[ct]                
                tag = {'Article':"div", 'Chapter': "section", 'ConferencePaper' : "section"}[ct]               
                child_tag = {'Article':"p", 'Chapter': "p", 'ConferencePaper' : "p"}[ct]               

                father_tag = inner_page.find(tag, attrs=att) 
                if father_tag is not None:
                    father_tag = father_tag.findChild(child_tag)
                    abs = father_tag.text.strip()                
                printd(abs)

            elif self.base == "acm":
                abs = ""
                father_tag = inner_page.find("div", attrs={"class":"abstractSection abstractInFull"})
                if father_tag is not None:
                    tag = father_tag.findChild("p")
                    abs = tag.text.strip()
                printd(abs)

            elif self.base == "ieeex":
                pass
            elif self.base == "elsevier":
                pass
            else:
                raise BaseUndefinedError(self.base)  

        def collect_keywords():
            if self.base == "springer":            
                keywords = []
                att = {'Article':{"itemprop" : "about" }, 'Chapter': {"class" : "Keyword" } , 'ConferencePaper' :{"class" : "Keyword" }}[ct]                
                tag = {'Article':"span", 'Chapter': "span", 'ConferencePaper' : "span"}[ct]               

                keywords_tag_list = inner_page.find_all(tag, attrs=att)
                for t in keywords_tag_list:
                    keywords.append(t.text.strip())
                
                printd(keywords)
                
            elif self.base == "acm":                
                keywords_tag_list = inner_page.find_all("ol", attrs={"class":"rlist"})                
                kw = [x.find("p") for x in keywords_tag_list]
                kw = list(set([x.text.strip() for x in kw if x]))                
                printd(kw)

            elif self.base == "ieeex":
                pass
            elif self.base == "elsevier":
                pass
            else:
                raise BaseUndefinedError(self.base)  

        def collect_metrics():
            if self.base == "springer":            
                metrics = {"citations":0 ,"downloads":0 ,"accesses":0 , "altmetric":0}

                att = {'Article':{"class" :  "c-article-metrics-bar"}, 'Chapter':{"class" :  "article-metrics"} , 'ConferencePaper' :{"class" :  "article-metrics"}}[ct]                
                tag = {'Article':"ul", 'Chapter': "ul", 'ConferencePaper' : "ul"}[ct]               
                child_tag = {'Article':"p", 'Chapter': "li", 'ConferencePaper' : "li"}[ct]               

                find_tag = inner_page.find(tag, attrs=att)
                tag_list = find_tag.findChildren(child_tag)

                for c in tag_list:
                    k = c.text.strip().split()[1].lower()
                    v = c.text.strip().split()[0]
                    if k in metrics.keys():
                        metrics[k] = convert_str_to_int(v)
                printd(metrics)
                
            elif self.base == "acm":
                tag1 = inner_page.find("span", attrs={'class':'citation'})
                tag2 = inner_page.find("span", attrs={'class':'metric'})
                printd(tag1.find_all("span")[0].text) #citations
                printd(tag2.find_all("span")[0].text) #downloads

            elif self.base == "ieeex":
                pass
            elif self.base == "elsevier":
                pass
            else:
                raise BaseUndefinedError(self.base)  
        
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
                return int(nop.get_text())

            elif self.base == "acm":                
                number_of_results = first_outer_page.find("span", {"class" : "hitsLength"})
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
                pass
            else:
                raise BaseUndefinedError(self.base)                

        first_search_page = self.get_page(self.query_url_attrib['initial_url'])
        number_of_pages : int = scrap_number_of_pages(first_search_page)
        if number_of_pages is None:
            first_search_page = self.get_page(self.query_url_attrib['initial_url'], delay=10)
            number_of_pages : int = scrap_number_of_pages(first_search_page)
        if number_of_pages is None:
            raise InsufficientDelayError("10 Seconds")
        if number_of_pages == 0:
            raise NoResultsForSearchStringError(self.base)

        links : set = set(self.collect_links_to_inner_pages(first_search_page))
        
        printd(links)    
            
        #TODO: checar qtd de paginas é maior que um, ou se existem matchs para busca
        #   ACM:             
        #   if self.init_pag_range == number_of_pages:
        #                    break
        #

        for page_index in range(self.init_pag_range, number_of_pages + 1):                        
            
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
                pass
                url = self.query_url_attrib['domain'] + '/' + self.query_url_attrib['pre_query'] \
                    + self.query_url_attrib['params'] +  self.query_url_attrib['pagination_itens_per_page'] + str(self.pagination_size) \
                    +  self.query_url_attrib['pagination_param'] + str(page_index)                                                  

            elif self.base == "elsevier":
                pass
            else:
                raise BaseUndefinedError(self.base)            
            
            outer_page : BeautifulSoup = self.get_page(url)                                    
            lol : 'list[str]' = self.collect_links_to_inner_pages(outer_page)
            for l in lol:
                links.add(l)                                    
            
            if global_config.DBG_FLAG:
               break

        for doi_link in links:                        
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
                inner_page : BeautifulSoup = self.get_page(url)                                                    
                self.collect_from_page(inner_page, url)

            elif self.base == "elsevier":
                pass
            else:
                raise BaseUndefinedError(self.base)                                    
            

    def register():
        pass