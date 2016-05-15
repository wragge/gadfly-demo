import re
import time
import csv
import os
from urllib import urlretrieve
from dateutil.parser import parse
from trove_python.trove_core import trove
from trove_python.trove_harvest.harvest import TroveHarvester

# The API query we're going to use (minus the API key).
# The 'q=firstpageseq:1' says to return articles on the front page.
QUERY = 'http://api.trove.nla.gov.au/result?q=firstpageseq:1&zone=newspaper&encoding=json&l-title=898&reclevel=full&sortby=dateAsc'
# This is how URLs to page images are constucted (insert page id).
# Higher level values (eg level4) give higher res images.
IMAGE_URL = 'http://trove.nla.gov.au/ndp/imageservice/nla.news-page{}/level3'
# Page identifier
PAGE_URL = 'http://nla.gov.au/nla.news-page{}'


class GadflyHarvester(TroveHarvester):
    """
    Subclass of TroveHarvester.
    Defines process_results() to download page images.
    """

    page_ids = []

    def process_results(self, results):

        """
        Process a set of results.
        Identify page ids and download page images.
        Save details to a CSV file.
        """

        try:
            articles = results[0]['records']['article']
            # Check to see if images directory exists
            images_dir = make_images_dir()
            # Write results to a CSV file
            with open('results.csv', 'ab') as results_file:
                writer = csv.writer(results_file)
                for article in articles:
                    # Get the page id from trovePageUrl
                    page_id = re.search(r'page\/(\d+)', article['trovePageUrl']).group(1)
                    # Check for duplicate ids
                    if page_id not in self.page_ids:
                        self.page_ids.append(page_id)
                        # Format the page image url
                        image_url = IMAGE_URL.format(page_id)
                        # Parse date and format a nice title for the CSV file
                        date = parse(article['date'])
                        title = "The Gadfly, {:%e %B %Y}".format(date)
                        # Format the persistent link for the page in Trove
                        url = PAGE_URL.format(page_id)
                        # Format the image filename and download the page image
                        image_filename = '{}-{}.jpg'.format(article['date'], page_id)
                        urlretrieve(image_url, os.path.join(images_dir, image_filename))
                        # Write data to the CSV file
                        writer.writerow([article['date'], page_id, title, url, image_filename])
            # Give the Trove API a break
            time.sleep(0.5)
            # Update the harvester so it knows where it's up to.
            self.harvested += self.get_highest_n(results)
            print('Harvested: {}'.format(self.harvested))
        except KeyError:
            pass

def make_images_dir(path='images'):

    """
    Checks to see if the supplied directory exists in the current working directory.
    Creates it if it doens't. Returns the full path.
    """

    images_dir = os.path.join(os.getcwd(), path)
    try:
        os.makedirs(images_dir)
    except OSError:
        if not os.path.isdir(images_dir):
            raise
    return images_dir


def start_harvest(key, query=QUERY):
    # Initialise a Trove class with an API key
    trove_api = trove.Trove(key)
    # Initialise harvester subclass
    harvester = GadflyHarvester(trove_api, query=QUERY)
    # Start harvest
    harvester.harvest()
