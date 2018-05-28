from urllib.parse import urlencode
from bs4 import BeautifulSoup
import time
import urllib.request
from fake_useragent import UserAgent		
def get_html(url):
    ua = UserAgent()
    header = ua.random
    try:
        request = urllib.request.Request(url)
        request.add_header("User-Agent", header)
        html = urllib.request.urlopen(request).read()
        return html
    except urllib.error.HTTPError as e:
        print("Error accessing:", url)
        print(e)
    except Exception as e:
        print(e)
        print("Error accessing:", url)
        return None	
		
def _get_search_url(query, page=0, per_page=10, lang='en', area='co.uk', ncr=False):
    # note: num per page might not be supported by google anymore (because of
    # google instant)

    params = {'nl': lang, 'q': query.encode(
        'utf8'), 'start': page * per_page, 'num': per_page }

    params = urlencode(params)

    https = int(time.time()) % 2 == 0
    bare_url = u"https://www.google.co.uk/search?" if https else u"http://www.google.co.uk/search?"
    url = bare_url + params
    # return u"http://www.google.com/search?hl=%s&q=%s&start=%i&num=%i" %
    # (lang, normalize_query(query), page * per_page, per_page)    
    return url

def search(query, pages=1, lang='en', area='com', ncr=False, void=True):
    """Returns a list of GoogleResult.
    Args:
        query: String to search in google.
        pages: Number of pages where results must be taken.
        area : Area of google homepages.
    TODO: add support to get the google results.
    Returns:
        A GoogleResult object."""
    results = []
    for i in range(pages):
        url = _get_search_url(query, i, lang=lang, area=area, ncr=ncr)
        print(url)
        html = get_html(url)
        #print(html)
		
        soup = BeautifulSoup(html, "html.parser")
        #print(soup)
        div = soup.find("div", attrs={"class": "g"})
        print(div)
        return _get_google_link(div)
            

def _get_google_link(li):
    """Return google link from a search."""
    try:
        a = li.find("a")
        link = a["href"]
        return link
    except Exception:
        return None
		
if __name__ == "__main__":
    result = search("python")
    print(result)



