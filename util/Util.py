from config.PreConfig import GLOBAL_CONFIG

global_config = GLOBAL_CONFIG()

def convert_str_to_int(num):
    #25k 
    if num[-1] == 'k':
    # treat 1.3k case
        return int(float(num[:-1])*1000)
    return int(num)

def printd(*value):
    if global_config.DBG_FLAG:
        print(value)