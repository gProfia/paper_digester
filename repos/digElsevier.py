import urllib.request
import shutil
import os
import re

class ElsevierData:

    def __init__(self, api_key):
        self.api_key = api_key    
        self.bibs = []
        self.xmls = []
        
    def findBibs(self, queryString):
        pass

    def extractURL(self, fileContent):
        
        #url = {https://www.sciencedirect.com/science/article/pii/S1877050921014435},
        
        pattern =  re.compile(r"(http[s]?://[a-zA-Z0-9.-/]+sciencedirect[a-zA-Z0-9.-/]+)")
        urls = re.findall(pattern,  fileContent.lower())
        
        return urls
        
    def savePapersXML(self, pathToDotBib, apiKey):

        #file = open('./citations.bib', encoding="utf-8")
        file = open(pathToDotBib, encoding="utf-8")
        fileContent = file.read()
        urls = (self.extractURL(fileContent))

        for url in urls:

            #name = url.split('/', 1)[-1][0:-1]
            pii = url.split('/',-1)[-1]
            print(pii)
            
            request='https://api.elsevier.com/content/article/pii/'+pii+'?apiKey='+apiKey
            
            response, headers = urllib.request.urlretrieve(request)

            filename = os.path.join('./', response)

            shutil.copy(filename, './out/'+pii+'.xml')

