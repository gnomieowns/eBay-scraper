from lxml import html
import requests
import csv
from traceback import format_exc
import re
import argparse
from matplotlib import pyplot as plt
from numpy import mean

url = "https://www.ebay.com/sch/Portable-Audio-Headphones/15052/i.html?_udlo=50&_udhi=310&_mPrRngCbx=1&LH_Complete=1&_sop=13&_nkw=sony+wh-1000xm2&_ipg=200&rt=nc"
brand = "sony wh-1000xm2"
regex = re.compile("[0-9.]+")


def parse(url):
    scraped_products = []
    for i in range(1, 4):
            try:
                # url = 'http://www.ebay.com/sch/i.html?_nkw={0}&_sacat=0'.format(brand)
                url += "&_pgn={}".format(str(i))
                print("Retrieving {}".format(url))
                response = requests.get(url)
                print("Parsing page")
                parser = html.fromstring(response.text)
                product_listings = parser.xpath('//li[contains(@class,"lvresult")]')
                raw_result_count = parser.xpath("//span[@class='rcnt']//text()")
                result_count = ''.join(raw_result_count).strip()
                print("Found {0} results for {1}".format(result_count, brand))

                for product in product_listings:
                    # // shortcuts to specific class
                    # use //header[@class="class"]
                    # or //header[contains(@class, 'class')]
                    # first period dot limits to nth (target) instance
                    raw_url = product.xpath("//a[@class='vip']/@href")
                    raw_title = product.xpath(".//a[@class='vip']/text()")
                    raw_status = product.xpath(".//div[@class='lvsubtitle']/text()")
                    raw_date = product.xpath(".//span[@class='tme']/span/text()")
                    raw_price = product.xpath(".//li[@class='lvprice prc']/span/text()")
                    raw_shipping = product.xpath(".//span[@class='ship']/span/text()")
                    raw_shipping = product.xpath(".//span[@class='fee']/text()")

                    title = ' '.join(' '.join(raw_title).split())
                    status = ' '.join(' '.join(raw_status).split())
                    price = ' '.join(' '.join(raw_price).split())
                    # skip item if it has no price
                    if len(price) < 2:
                        continue
                    price = float(price.strip('$'))

                    shipping = ' '.join(' '.join(raw_shipping).split())
                    if len(shipping) > 0:
                        shipping = float(str(re.findall(regex, shipping)[0]))
                    else:
                        shipping = 0.0

                    data = {
                        'url': raw_url[0],
                        'title': title,
                        'status': status,
                        'date': raw_date,
                        'price': price,
                        'shipping': shipping,
                        'total_price': price + shipping
                    }
                    scraped_products.append(data)
            except Exception as e:
                print(format_exc(e))
    return scraped_products


scrape_list = parse(url)
print("\n{}\n".format(scrape_list[7]))

status_list = ["Brand New", "Pre-Owned"]
status_dict = {}

for status in status_list:
    status_n_list = []
    for data in scrape_list:
        if data["status"] == status:
            status_n_list.append(data["total_price"])
    status_dict[status] = status_n_list
    print("\n{} Average: {:.2f}".format(status, mean(status_n_list)))

for subdict in status_dict:
    # print(subdict)
    price_list = status_dict[subdict]
    plt.figure(subdict)
    plt.hist(price_list)
plt.show()

with open('{}-ebay-scraped-data.csv'.format(brand), 'w', encoding='utf-8') as csvfile:
        fieldnames = ["date", "title", "status", "total_price", "price", "shipping"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore',
                                quoting=csv.QUOTE_ALL, lineterminator='\n')
        writer.writeheader()
        for data in scrape_list:
            writer.writerow(data)
