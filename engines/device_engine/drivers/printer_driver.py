import os

class Driver:

    def print_text(self, text):

        os.system(f'echo "{text}" | lp')
