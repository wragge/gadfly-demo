# We're going to harvest images of front pages from the SA newspaper Gadfly.

import re
import time
import csv
from operator import itemgetter
from urllib import urlretrieve
from dateutil.parser import parse
from trove_python.trove_core import trove
from trove_python.trove_harvest.harvest import TroveHarvester

QUERY = 'http://api.trove.nla.gov.au/result?q=firstpageseq:1&zone=newspaper&encoding=json&l-title=898&reclevel=full'
IMAGE_URL = 'http://trove.nla.gov.au/ndp/imageservice/nla.news-page{}/level3'
PAGE_URL = 'http://nla.gov.au/nla.news-page{}'
GITHUB_URL = 'https://raw.githubusercontent.com/wragge/gadfly-demo/master/images/{}.jpg'


class GadflyHarvester(TroveHarvester):

    # Need to get results for articles on page 1
    # Then get ids for the page

    def process_results(self, results):
        try:
            articles = results[0]['records']['article']
            # Write results to a CSV file
            with open('results.csv', 'ab') as results_file:
                writer = csv.writer(results_file)
                for article in articles:
                    # We want the date and the page id
                    page_id = re.search(r'page\/(\d+)', article['trovePageUrl']).group(1)
                    image = IMAGE_URL.format(page_id)
                    date = parse(article['date'])
                    title = "The Gadfly, {:%e %B %Y}".format(date)
                    url = PAGE_URL.format(page_id)
                    writer.writerow([article['date'], page_id, title, url, image])

            time.sleep(0.5)
            self.harvested += self.get_highest_n(results)
            print('Harvested: {}'.format(self.harvested))
        except KeyError:
            pass


def get_images():
    """
    Remove duplicate pages from results, sort them, write to a new file, and download images.
    """
    pages = []
    # Remove duplicates
    with open('results.csv', 'rb') as results_file:
        reader = csv.reader(results_file)
        for row in reader:
            if row not in pages:
                pages.append(row)
    # Sort by date
    pages = sorted(pages, key=itemgetter(0))
    # Write to a new CSV file
    with open('pages.csv', 'wb') as pages_file:
        writer = csv.writer(pages_file)
        writer.writerow(['date', 'id', 'title', 'url', 'image_url'])
        for page in pages:
            # This rewrites the image url for import into Omeka (needs a file extension)
            page[4] = GITHUB_URL.format(page[1])
            writer.writerow(page)
            # Download the images
            urlretrieve(page[4], 'images/{}.jpg'.format(page[1]))


def start_harvest(key, query=QUERY):
    trove_api = trove.Trove(key)
    harvester = GadflyHarvester(trove_api, query=QUERY)
    harvester.harvest()
