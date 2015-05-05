import bs4
import urllib
import sys
import os
import time
from contextlib import closing
from selenium.webdriver import Firefox
from selenium.webdriver.support.ui import WebDriverWait

def retrieve_url(url):
	retry_flag = True
	while retry_flag:
		page = urllib.urlopen(url)
		data = page.read()
		soup = bs4.BeautifulSoup(data)
		h2_list = soup.find_all("h2")
		if len(h2_list) == 0 or h2_list[0].get_text() != "Oops!":
			retry_flag = False
		time.sleep(1)
	return data

def retrieve_reviews(review_url, page_count, directory, count_offset):
	data = retrieve_url(review_url)
	review_soup = bs4.BeautifulSoup(data)
	reviews = review_soup.find_all("span",
		class_="a-size-base review-text")

	stars = review_soup.find(id="cm_cr-review_list").find_all("span", class_="a-icon-alt")

	count = 1
	for r in reviews:
		star_count = stars[count - 1].get_text()
		fout = open(directory + "/" + str(count + count_offset) + ".txt" ,"w")
		fout.write("Review #" + str(count + count_offset) + "\n")
		fout.write(star_count + " stars\n")
		fout.write(r.get_text().encode("ascii", "ignore") + "\n\n")
		fout.close()
		count += 1

	if page_count > 1:
		page_link = review_soup.find_all("li", class_="a-selected page-button")[0].a["href"]
		for i in range(2, page_count + 1):
			retrieve_reviews("http://www.amazon.com" + page_link + "?pageNumber=" + str(i), 0, directory, (i-1) * 10)

def retrieve_item_info(item_url, index):
	print index
	if not os.path.exists(str(index)):
		os.makedirs(str(index))
	fout = open(str(index) + "/info.txt", "w")

	item_data = retrieve_url(item_url)
	item_soup = bs4.BeautifulSoup(item_data)

	image = item_soup.find(id="imgTagWrapperId")
	if not (image is None):
		image_link = image.img["src"]
		urllib.urlretrieve(image_link, str(index) + "/icon.jpg")

	with open("item.html", "w") as f:
		f.write(item_data)
		f.close()

	fout.write("Title: " + item_soup.find(id="productTitle").get_text().encode("ascii", "ignore") + "\n")
	fout.write("URL: " + item_url + "\n")
	
	price_div = item_soup.find(id="price")
	if not (price_div is None):
		fout.write(" ".join(price_div.get_text().split()) + "\n")

	star_div = item_soup.find(id="acrPopover")
	if not (star_div is None):
		fout.write("Rating: " + star_div["title"] + "\n")

	features_div = item_soup.find(id="feature-bullets")
	if not (features_div is None):
		fout.write("Features:\n")
		for f in features_div.find_all("span", class_="a-list-item"):
			fout.write(f.get_text().encode("ascii", "ignore") + "\n")
		fout.write("\n")

	description_div = item_soup.find("div", class_="productDescriptionWrapper")
	if not (description_div is None):
		fout.write("Description:\n" + description_div.get_text().encode("ascii", "ignore") + "\n")
		fout.write("\n")

	review_link_ls = item_soup.find_all("a", 
		class_="a-link-emphasis a-text-normal a-nowrap")
	review_link_ls += item_soup.find_all("a", 
		class_="a-link-emphasis a-nowrap")
	for link in review_link_ls:
		link_text = link.get_text()
		if len(link_text) > 3 and link_text[:3] == "See":
			review_url = link["href"]
			if link_text[:7] == "See all":
				review_count = int(link_text.split()[2].replace(",", ""))
				fout.write(str(review_count) + " reviews in total.\n\n")
				retrieve_reviews(review_url, (review_count - 1)/10 + 1, str(index), 0)

	fout.close()
				
def retrieve_items(list_url):
	count_offset = 0
	for i in range(1,6):
		url = list_url + "#" + str(i)

		with closing(Firefox()) as browser:
			browser.get(url)
			time.sleep(5)
			page_source = browser.page_source

		list_soup = bs4.BeautifulSoup(page_source)

		count = 1
		for item in list_soup.find_all("div", class_="zg_title"):
			item_url = item.a["href"].replace("%0A", "")
			retrieve_item_info(item_url, count + count_offset)
			count += 1

		count_offset += 20

# put one best seller url in the url.txt file for scraping.
with open("url.txt", "r") as f:
	url = f.read()

retrieve_items(url)