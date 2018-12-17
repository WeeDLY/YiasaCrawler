import sys
sys.path.append('..')
import util.logger as logger

def debug(log):
    print('Started debug mode')
    debugMode = True
    while debugMode:
        cmd = input('$ ')
        if cmd == 'q' or cmd == 'e':
            debugMode = False
            
    print('Exiting debug mode')