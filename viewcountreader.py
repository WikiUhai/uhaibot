import gzip
import time
from datetime import datetime, timedelta
import gc
import re
import os
import pickle

FILE_PATTERN = re.compile(r'pageviews-\d{8}-\d{6}.gz')


class ViewCountReader:
    def __init__(self,
                 prefix: str = 'en',
                 namespaces: list = None,
                 path: str = '/public/dumps/pageviews/',
                 save_path: str = '.',
                 verbose: bool = False
                 ):
        self.prefix = prefix
        self.prefixm = prefix + '.m'
        if namespaces is None:
            namespaces = ['Media', 'Special', 'Talk', 'User', 'User_talk', 'Wikipedia', 'Wikipedia_talk', 'File',
                          'File_talk', 'MediaWiki', 'MediaWiki_talk', 'Template', 'Template_talk', 'Help', 'Help_talk',
                          'Category', 'Category_talk', 'Portal', 'Portal_talk', 'Book', 'Book_talk', 'Draft',
                          'Draft_talk', 'Education_Program', 'Education_Program_talk', 'TimedText', 'TimedText_talk',
                          'Module', 'Module_talk', 'Gadget', 'Gadget_talk', 'Gadget_definition',
                          'Gadget_definition_talk']
        self.namespaces = [namespace + ':' for namespace in namespaces]
        self.path = path
        self.save_path = save_path
        self.verbose = verbose

        self.year = None
        self.month = None
        self.counts = {}
        self.files = []
        self.file_data = None
        self.full_path = None

    def get_previous_year_month(self):
        today = datetime.today()
        previous_month = today - timedelta(days=today.day)
        self.year = previous_month.strftime("%Y")
        self.month = previous_month.strftime("%m")

    def get_files(self):
        for file in os.listdir(self.full_path):
            if FILE_PATTERN.search(file):
                self.files.append(os.path.join(self.full_path, file))

        self.printv(str(len(self.files)) + ' view count dump files found')

    def read_gz_file(self, filename):
        with gzip.open(filename, 'rt', encoding='utf-8') as file:
            self.file_data = None
            gc.collect()
            self.file_data = file.readlines()

    def parse_file(self):
        for line in self.file_data:
            arr = line.split(' ')

            prefix = str(arr[0])
            title = str(arr[1])
            value = int(arr[2])

            try:
                if prefix == self.prefix or prefix == self.prefixm:
                    if ':' in title and any(title.startswith(namespace) for namespace in self.namespaces):
                        continue

                    self.counts[title] = self.counts.get(title, 0) + value
            except Exception as e:
                self.printv(e)

    def save_counts(self):
        save_loc = os.path.join(self.save_path, self.year + '-' + self.month + '-viewcounts.pkl')
        self.printv('Saving results to ' + save_loc)

        with open(save_loc, 'wb') as file:
            pickle.dump(self.counts, file)

    def clean_up(self):
        self.counts = {}
        self.files = []

    def get_data(self):
        start = time.time()

        for file in self.files:
            self.printv('Parsing ' + file)

            self.read_gz_file(file)
            self.parse_file()

        self.printv('Data pull completed in ' + str(round((time.time() - start) / 60, 2)) + ' minutes')

    def run(self, year: str = None, month: str = None, save: bool = False):
        self.clean_up()

        if year is None or month is None:
            self.get_previous_year_month()
        else:
            self.year = year
            self.month = month

        self.full_path = os.path.join(self.path, self.year, self.year + '-' + self.month)

        self.printv('Pulling view count data for ' + self.prefix + ' for ' + self.year + '-' + self.month)

        self.get_files()
        self.get_data()

        self.file_data = None
        gc.collect()

        if save:
            self.save_counts()

        return self.counts

    def printv(self, string):
        if self.verbose:
            print(string)


if __name__ == '__main__':
    vcr = ViewCountReader(verbose=True)
    counts = vcr.run(save=True)
