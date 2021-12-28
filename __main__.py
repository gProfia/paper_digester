
#from springer_link.get_info import exec_scrap
from util.CollectedData import CollectedData

def main():    

    #COLLECT DATA FROM BASES
    springer_collector = CollectedData("springer").mount_search_page_url(content_type='article',
        year_start='2020', year_end='2021',
        query="(dependable OR dependability OR reliability OR availability OR maintainability OR safety OR reliable OR fault tolerant OR qos OR security OR failure OR fault OR latent error OR fault-avoidance OR fault-tolerance OR fault removal OR fault forecasting OR error-removal OR error-forecasting OR fault avoidance OR fault tolerance OR error removal OR error forecasting OR redundancy \
                    OR ((physical OR human-made OR design OR interaction ) AND ( faults)) \
                    OR elementary failure \
                    OR ((corrective OR preventive) AND maintenance) \
                    OR (error AND (processing OR recovery OR compensation OR detection OR masking )) \
                    OR confidentiality integrity availability OR security attributes OR information security OR vulnerabilities OR threats OR authenticity OR non-repudiation OR privacy OR auditability OR authentication) \
               AND ( iiot OR fog OR iot OR m2m OR wsn OR iomt) \
               AND (systems OR devices OR system OR device OR software OR hardware OR middleware OR component OR components OR computing OR service) ")
        #query="((dependable OR fault OR failure) AND (iot computer OR m2m) AND (systems OR devices))")
    #acm = CollectedData("acm")
    #ieeex = CollectedData("ieeex")
    #elsevier = CollectedData("elsevier")

    #FILTER REPETITON
    #DATA COMPLETION
    #SELECTION BY CRITERIA
    #READING
    #EXTRACTION/ANALISIS

    pass


if __name__== '__main__':
    main()