import subprocess
from util.ScrapErrors import *
from util.Singleton import Singleton

class GLOBAL_CONFIG(metaclass = Singleton):

    def __init__(self) -> None:
        self.CHROMEDRIVER_PATH : str 
        self.DBG_FLAG = False
        self.config_chromedriver_path()       
        

    def config_chromedriver_path(self):        
        try:
            if subprocess.run(['which', 'chromium.chromedriver']).returncode == 1:
                r=subprocess.run(['sudo', 'apt-get', 'install', 'chromium-chromedriver', '-y'])
                if r.returncode == 0:
                    print("chromium-chromedriver OK!")                
                    self.CHROMEDRIVER_PATH = subprocess.run(['which', 'chromium.chromedriver'], capture_output=True,text=True).stdout.replace('\n', '')
                else:
                    raise DependencyInstallationError("chromium-chromedriver")
            else:
                print("chromium-chromedriver OK!")            
                self.CHROMEDRIVER_PATH = subprocess.run(['which', 'chromium.chromedriver'], capture_output=True,text=True).stdout.replace('\n', '')
        except DependencyInstallationError as err:
            print(err.message)
      
                         



