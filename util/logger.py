from enum import Enum
import os
import datetime

class LogLevel(Enum):
    """ logger loglevels """
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

class Logger():
    """ Logger class """
    def __init__(self, filename, folder, max_size=3000, print_level=LogLevel.INFO):
        self.filename = filename
        self.folder = folder
        self.max_size = max_size
        self.print_level = print_level

        folder = self.check_folder()
        if folder is False:
            print('Something went wrong in Logger.check_folder')
            return
        self.current_file = self.get_current_log_file()
        self.current_size = self.get_file_length(self.current_file)

    def get_current_log_file(self):
        """ returns the new logfile """
        tempfile = '%s/%s.log' % (self.folder, self.filename)
        num = 1
        while self.get_file_length(tempfile) >= self.max_size:
            tempfile = '%s/%s%d.log' % (self.folder, self.filename, num)
            num += 1
        return tempfile

    def check_folder(self):
        """ Checks the folder the logs are placed """
        try:
            if os.path.isdir(self.folder) is False:
                os.makedirs(self.folder)
            return True 
        except IOError as ioerror:
            print(ioerror)
            return False
        except Exception as e:
            print(e)
            if not os.path.isdir(self.folder):
                raise
            return False

    def log(self, logLevel, msg, forcePrint=False):
        """ Logs messages """
        date = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        logString = "%s [%s]: %s " % (date, logLevel.name, msg)
        if forcePrint or self.print_level.value <= logLevel.value:
            print(logString)

        self.write_log(logString)

    def write_log(self, logString):
        """ Writes the log to a logfile """
        try:
            with open(self.current_file, 'a') as file:
                file.write(logString + '\n')
            self.current_size += 1
            if self.current_size >= self.max_size:
                self.current_file = self.get_current_log_file()
        except Exception as e:
            print(e)

    def get_file_length(self, file):
        """ returns file length of a given file """
        lines = 0
        try:
            with open(file, 'r') as file:
                for _ in file.readlines():
                    lines += 1
                return lines
        except IOError:
            return 0 # File does not exist
        except Exception as e:
            print(e)