from numpy import number
from requests_html  import  HTMLSession
import time, random 
from bs4 import BeautifulSoup
from util.DataNotFoundLogger import DataNotFoundLogger
from util.ScrapErrors import *
from util.ParserSearchString import *

#singleton
logger = DataNotFoundLogger()

class CollectedData:
    def __init__(self, base : str, delay : int = 5):
        if base not in ["elsevier", "ieeex", "acm", "springer"]:
            raise BaseUndefinedError(base)                
        self.base = base
        self.data = {       
            "item_title" : [] , #[str]
            "publication_title" : [], #[str]
            "item_DOI" : [], #[str]
            "publication_year" : [], #[str]
            "URL" : [], #[str]
            "content_type" : [], #[str]
            "authors" : [], #[list: str] 
            "abstract" : [], #[str]            
            "keywords" : [], #[list: str]
            "metrics": [], #[dict]
            "googleScholarMetrics" : [], #[list(dicts)]
            # [[a1{author: str, cit: (All, Since), h_i : (All, Since), i10 : (All, Since) }, a2, ...] ...]
            "base" : [] #[str]
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
        self.init_pag_range : int = {"elsevier":0, "ieeex":0, "acm":0, "springer":2}[self.base]
        self.initial_amount_of_results = 0
        self.delay = delay
        self.content_type = ""

    def mount_search_page_url(self, content_type : str, year_start : str, year_end : str,
     query : str):
        try:
            if not year_start or not year_end :
                year_start, year_end = '2020', '2021' 
            if not content_type:
                raise ContentTypeUndefinedError("empty")
            if content_type not in ['paper', 'article', 'chapter']:
                raise ContentTypeError(content_type)            
            
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

                for a in self.query_url_attrib:
                    print(a + ":\t" + self.query_url_attrib[a])                                

            elif self.base == "acm":
                p_open, p_close, space = '%28', '%29', ''
                a="https://dl.acm.org/action/doSearch?AllField=%28%28dependable+OR+fault+OR+failure%29+AND+%28iot+OR+m2m%29+AND+%28systems+OR+devices%29%29&expand=all"
                pass
            elif self.base == "ieeex":
                p_open, p_close, space = '(', ')', '%20'
                a="https://ieeexplore.ieee.org/search/searchresult.jsp?newsearch=true&queryText=((dependable%20OR%20fault%20OR%20failure)%20AND%20(iot%20OR%20m2m)%20AND%20(systems%20OR%20devices))"
                pass
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

    def get_page(self, query_url : str) -> BeautifulSoup:
        session = HTMLSession()
        r = session.get(query_url)
        soup = BeautifulSoup(r.content, "html.parser")
        session.close()
        return soup        
    
    def collect_links_to_inner_pages(self, outer_page : BeautifulSoup) -> 'list[str]':
        res = []
        if self.base == "springer":                                  
            link_tag_list = outer_page.find_all("a", attrs={"class" : "title"})
            for tag in link_tag_list:
                res.append(tag['href'])                            
            return res
        elif self.base == "acm":
            pass
        elif self.base == "ieeex":
            pass
        elif self.base == "elsevier":
            pass
        else:
            raise BaseUndefinedError(self.base)                

    def collect_from_page(self, inner_page : BeautifulSoup):

        def collect_item_title(): 
            if self.base == "springer":
                pass
            elif self.base == "acm":
                pass
            elif self.base == "ieeex":
                pass
            elif self.base == "elsevier":
                pass
            else:
                raise BaseUndefinedError(self.base)     
            pass
        def collect_publication_title():
            pass
        def collect_item_DOI():
            pass
        def collect_publication_year():
            pass
        def collect_URL():
            pass
        def collect_content_type():
            pass
        def collect_authors():
            pass
        def collect_abstract():
            pass
        def collect_keywords():
            pass
        def collect_metrics():
            pass
        def collect_googleScholarMetrics():
            pass
        

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
                print()
                print("########################### ["+str(i)+"]robot detected!!!###############################")
                print()
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
                #print(first_outer_page)
                nop = first_outer_page.find("span", {"class" : "number-of-pages"})
                return int(nop.get_text())
            elif self.base == "acm":
                pass
            elif self.base == "ieeex":
                pass
            elif self.base == "elsevier":
                pass
            else:
                raise BaseUndefinedError(self.base)                

        first_search_page = self.get_page(self.query_url_attrib['initial_url'])
        number_of_pages : int = scrap_number_of_pages(first_search_page)

        links : set = set(self.collect_links_to_inner_pages(first_search_page))
        
        #TODO: checar qtd de paginas é maior que um, ou se existem matchs para busca
        for page_index in range(self.init_pag_range, number_of_pages + 1):                        
            print(self.base + ", " + self.content_type +    " page :" + str(page_index) + " of " + str(number_of_pages + 1) )
            url : str = ""
            if self.base == "springer":
                url = self.query_url_attrib['domain'] + '/' + self.query_url_attrib['pre_query_pagination'] \
                    + str(page_index) + self.query_url_attrib['params'] 
            elif self.base == "acm":
                pass
            elif self.base == "ieeex":
                pass
            elif self.base == "elsevier":
                pass
            else:
                raise BaseUndefinedError(self.base)            
            
            outer_page : BeautifulSoup = self.get_page(url)                                    
            lol : 'list[str]' = self.collect_links_to_inner_pages(outer_page)
            for l in lol:
                links.add(l)                        
            time.sleep(self.delay)            

        for doi_link in links:
            
            if self.base == "springer":                
                url = self.query_url_attrib['domain'] + doi_link                
                #TODO: SCRAP
                
            elif self.base == "acm":
                pass
            elif self.base == "ieeex":
                pass
            elif self.base == "elsevier":
                pass
            else:
                raise BaseUndefinedError(self.base)            
            

            

    def register():
        pass