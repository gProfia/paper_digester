from requests_html  import  HTMLSession
import time, random 
from bs4 import BeautifulSoup
from util.DataNotFoundLogger import DataNotFoundLogger

#singleton
logger = DataNotFoundLogger()

class CollectedData:
    def __init__(self):
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
            "googleScholarMetrics" : [] #[list(dicts)]
            # [[a1{author: str, cit: (All, Since), h_i : (All, Since), i10 : (All, Since) }, a2, ...] ...]
            }
    
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
       