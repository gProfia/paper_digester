import os
from Singleton import Singleton

class DataNotFoundLogger(metaclass = Singleton):

    def __init__(self):
        self.create_record()        

    def create_record(self):
        if not os.path.isfile('../missing_authors'):
            open('../missing_authors', 'w').close()
        

    def register_gs_author_not_found(self, name):
        if os.path.isfile('../missing_authors'):
            f = open('../missing_authors', 'a')
            f.write(name+ '\n')
            f.close()
