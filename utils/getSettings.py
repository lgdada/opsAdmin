import os
import configparser
import re

program_path = os.path.dirname(os.path.dirname(__file__))

class settings(object):
    def __init__(self, config_file='settings/config.ini'):
        self.config_ini = os.path.join(program_path, config_file)
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config.read(self.config_ini, encoding="utf-8")

    def file_abspath(self, path):
        if re.match(r'^/(.*)$',path):
            return path
        else:
            return os.path.join(os.path.dirname(self.config_ini), path)

setting = settings()

if __name__ == '__main__':
    print (setting.file_abspath('/opt'))