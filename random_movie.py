import argparse
import json
import random
from urllib import parse

import requests
from bs4 import BeautifulSoup as bs

BASE_URL = "https://www.imdb.com/search/title/?"


def has_next(response_html):
    """Find next url to search for movies
    """

    next_url = response_html.find("a", {"class": "lister-page-next next-page"})
    relative_url = next_url.get("href", None) if next_url else None

    if relative_url is not None:
        return parse.urljoin(BASE_URL, relative_url)
    return None


def bs4_object_as_text(obj):
    """Parse bs4 object as text
    """

    if obj is not None:
        return obj.get_text(strip=True)
    return None


def structure_data(item):
    """Parse a movie on IMdB
    """

    data = {"name": "", "position": "", "year": "", "score": "", "metascore": "", "summary": "",
            "length": "", "certificate": "", "genres": "", "directors": "", "stars": "", "gross": ""}

    # 0 - position / 1 - name / 2 - year
    title = item.find("h3").get_text()
    title_items = list(filter(str, title.split("\n")))

    data["position"] = title_items[0]
    data["name"] = title_items[1]
    data["year"] = title_items[2]

    #  certificate / length / genres
    subtitle_items = item.find("p", {"class": "text-muted"})

    certificate = subtitle_items.find("span", {"class": "certificate"})
    length = subtitle_items.find("span", {"class": "runtime"})
    genres = subtitle_items.find("span", {"class": "genre"})

    data["certificate"] = bs4_object_as_text(certificate)
    data["length"] = bs4_object_as_text(length)
    data["genres"] = bs4_object_as_text(genres)

    # ratings-bar / rate / metascore
    ratings = item.find("div", {"class": "ratings-bar"})

    score = ratings.find("strong")
    metascore = ratings.find("span", {"class": "metascore"})

    data["score"] = bs4_object_as_text(score)
    data["metascore"] = bs4_object_as_text(metascore)

    # summary
    summary = item.find_all("p", {"class": "text-muted"})[-1]
    data["summary"] = bs4_object_as_text(summary)

    # director / stars
    list_of_p = item.find_all("p")
    content = bs4_object_as_text(list_of_p[-2]).split("|")

    directors = content[0].split(",")
    directors[0] = directors[0].split(":")[1]
    data["directors"] = directors

    stars = content[1].split(",")
    stars[0] = stars[0].split(":")[1]
    data["stars"] = stars

    # gross
    gross = list_of_p[-1]
    gross = [bs4_object_as_text(span) for span in gross.find_all("span")]

    if "Gross:" in gross:
        data["gross"] = gross[-1]

    return data


def parse_data(response_html):
    """Parse HTML content
    """

    movies_data = []

    items = response_html.find_all(
        "div", {"class": "lister-item mode-advanced"})

    for item in items:
        data = structure_data(item)
        movies_data.append(data)

    return movies_data


def get_url(url, header={}):
    """Create session obj
    """

    session = requests.Session()
    response = session.get(url)

    return response


def get_movies(url):
    """Check if has any movie to get
    """

    movies = []

    while True:
        response = get_url(url)
        response_html = bs(response.text, "html.parser")

        movies.extend(parse_data(response_html))
        url = has_next(response_html)

        if url is None:
            break

    return movies


def process_args(args):
    """Process user args params
    """

    top = args.get("top", None)
    years = args.get("year", None)

    if top is not None:
        top = f"groups=top_{top}"

    if years is not None:
        years = f"release_date={years}"

    url = f"{BASE_URL}{years}&{top}&adult=include"

    return url


def cli_args():
    """Define some user params to use when executing
    """

    args = argparse.ArgumentParser("Search a random movie from IMDb")
    args.add_argument("-t", "--top", required=True,
                      help="Search between top 100/250/1000", type=int, choices={100, 250, 1000})
    args.add_argument("-y", "--year", required=True,
                      help="Year to search. Can separate using comma like '2015,2020'", type=str)
    return args


def run():
    """Startup foo
    """

    args = vars(cli_args().parse_args())
    url = process_args(args)
    movies = get_movies(url)
    movie = random.choices(movies)[0]

    print(json.dumps(movie, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    run()
