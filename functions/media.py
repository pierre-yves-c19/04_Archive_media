import os
import pandas as pd
import requests
import time
from bs4 import BeautifulSoup
import pyprind
from requests_tor import RequestsTor


class France_Info:

    def __init__(
        self, start_date="2020-02-01", end_date="2023-12-31", folder_name="france_info"
    ) -> None:
        # Create a data folder
        self.path = f"data/{folder_name}"
        if not os.path.isdir(self.path):
            os.mkdir(self.path)
        # List of days to itervate over
        self.list_date = pd.date_range(start="2020-02-01", end="2023-12-31", freq="D")
        self.request_session = requests.Session()

    def get_url(self, date):
        url_base = "https://www.francetvinfo.fr/archives/"
        date_string = date.strftime("%d-%B-%Y").replace("é", "e").replace("û", "u")
        url_full = f"{url_base}{date.year}/{date_string}.html"
        return url_full

    def get_papers_one_day(self, date):
        url_full = self.get_url(date=date)
        # r = requests.get(url=url_full)
        r = self.request_session.get(url=url_full)
        if r.status_code != 200:
            print(url_full)
            raise Warning(f"Status code incorect: {r.status_code}")
        else:
            # print(date)
            soup = BeautifulSoup(r.content, features="lxml")
            list_article = soup.find_all("article")
            list_info = []
            for i, article in enumerate(list_article):
                url_article = article.a.get("href")
                title_article = article.get_text().replace("\n", "").strip()
                list_info.append([title_article, url_article])
            df = pd.DataFrame(list_info, columns=["title", "url"])
            df = pd.concat([df], axis=0, keys=[date])
            date_str = date.strftime("%Y-%m-%d")
            df.to_pickle(f"{self.path}/df_{date_str}.pkl")
            return df

    def download_all(self, retry=False):
        bar = pyprind.ProgBar(len(self.list_date))
        for date in self.list_date:
            date_str = date.strftime("%Y-%m-%d")
            if not os.path.isfile(f"{self.path}/df_{date_str}.pkl"):
                df = self.get_papers_one_day(date=date)
            bar.update()

    def load_data(self):
        final_file = f"{self.path}/DF.pkl"
        if not os.path.isfile(final_file):
            list_file = os.listdir(self.path)
            list_file = [file for file in list_file if file.startswith("df_")]
            list_df = []
            for file in list_file:
                df = pd.read_pickle(self.path + "/" + file)
                list_df.append(df)
            DF = pd.concat(list_df)
            DF.to_pickle(final_file)
        DF = pd.read_pickle(final_file)
        self.dataframe = DF
        return DF

    def is_COVID_related(self):
        def check_if_COVID_related(row):
            """Test if some COVID related keywords are mentioned"""
            title = row.lower()
            COVID_keywords = [
                "covid",
                "coronavirus",
                "2019-nCoV",
                "Covid-19",
            ]  # "épidémie", "pandémie",
            COVID_keywords = set([kw.lower() for kw in COVID_keywords])
            title_words = set(title.split())
            if COVID_keywords.intersection(title_words):
                COVID_related = True
            else:
                COVID_related = False
            return COVID_related

        self.dataframe["COVID_related"] = self.dataframe.title.apply(
            check_if_COVID_related
        )

    def load_content_of_COVID_related_papers(self):
        file = f"{self.path}/DF_with_content.pkl"
        if not os.path.isfile(file):
            df = self.dataframe
            df = df[df.COVID_related]

            def get_twitter_description(url_article, bar):
                """Download the "chapeau" of the article"""
                url_full = "https://www.francetvinfo.fr/" + url_article
                r = self.request_session.get(url=url_full)
                if r.status_code != 200:
                    raise Warning(f"Status code incorect: {r.status_code}")
                soup = BeautifulSoup(r.content, features="lxml")
                description = soup.find(attrs={"property": "twitter:description"})
                bar.update()
                return description.attrs["content"]

            bar = pyprind.ProgBar(df.shape[0])
            df["content"] = df.url.apply(lambda x: get_twitter_description(x, bar=bar))
            df.to_pickle(file)

        df = pd.read_pickle(file)
        self.dataframe_COVID_related = df
        return df


class Le_Parisien:

    def __init__(
        self, start_date="2020-02-01", end_date="2023-12-31", folder_name="le_parisien"
    ) -> None:
        # Create a data folder
        self.path = f"data/{folder_name}"
        if not os.path.isdir(self.path):
            os.mkdir(self.path)
        # List of days to itervate over
        self.list_date = pd.date_range(start="2020-02-01", end="2023-12-31", freq="D")
        self.request_session = requests.Session()

    def get_url(self, date):
        url_base = "https://www.leparisien.fr/archives/"
        date_string = date.strftime("%d-%m-%Y")
        url_full = f"{url_base}/{date.year}/{date_string}"
        return url_full

    def get_papers_one_day(self, date):
        url_full = self.get_url(date=date)
        # r = requests.get(url=url_full)
        r = self.request_session.get(url=url_full)
        if r.status_code != 200:
            print(url_full)
            raise Warning(f"Status code incorect: {r.status_code}")
        else:
            # print(date)
            soup = BeautifulSoup(r.content, features="lxml")
            list_article = soup.find_all(
                "div",
                attrs={"class": "story-preview story-preview--oneline flex-feed-unit"},
            )
            list_info = []
            for i, article in enumerate(list_article):
                url_article = article.a.get("href").replace("//", "https://")
                title_article = article.find(attrs={"class": "story-headline"}).text
                list_info.append([title_article, url_article])
            df = pd.DataFrame(list_info, columns=["title", "url"])
            df = pd.concat([df], axis=0, keys=[date])
            date_str = date.strftime("%Y-%m-%d")
            df.to_pickle(f"{self.path}/df_{date_str}.pkl")
            return df

    def download_all(self, retry=False):
        bar = pyprind.ProgBar(len(self.list_date))
        for date in self.list_date:
            date_str = date.strftime("%Y-%m-%d")
            if not os.path.isfile(f"{self.path}/df_{date_str}.pkl"):
                df = self.get_papers_one_day(date=date)
            bar.update()

    def load_data(self):
        final_file = f"{self.path}/DF.pkl"
        if not os.path.isfile(final_file):
            list_file = os.listdir(self.path)
            list_file = [file for file in list_file if file.startswith("df_")]
            list_df = []
            for file in list_file:
                df = pd.read_pickle(self.path + "/" + file)
                list_df.append(df)
            DF = pd.concat(list_df)
            DF.to_pickle(final_file)
        DF = pd.read_pickle(final_file)
        self.dataframe = DF
        return DF

    def is_COVID_related(self):
        def check_if_COVID_related(row):
            """Test if some COVID related keywords are mentioned"""
            title = row.lower()
            COVID_keywords = [
                "covid",
                "coronavirus",
                "2019-nCoV",
                "Covid-19",
            ]  # "épidémie", "pandémie",
            COVID_keywords = set([kw.lower() for kw in COVID_keywords])
            title_words = set(title.split())
            if COVID_keywords.intersection(title_words):
                COVID_related = True
            else:
                COVID_related = False
            return COVID_related

        self.dataframe["COVID_related"] = self.dataframe.title.apply(
            check_if_COVID_related
        )


class Le_Monde:

    def __init__(
        self, start_date="2020-02-01", end_date="2023-12-31", folder_name="le_monde"
    ) -> None:
        # Create a data folder
        self.path = f"data/{folder_name}"
        if not os.path.isdir(self.path):
            os.mkdir(self.path)
        # List of days to itervate over
        self.list_date = pd.date_range(start="2020-02-01", end="2023-12-31", freq="D")
        # self.request_session = requests.Session()
        self.request_session = RequestsTor()
        self.request_session.proxies = {
            "http": "socks5h://localhost:9050",
            "https": "socks5h://localhost:9050",
        }
        # RequestsTor(tor_ports=(9000, 9001, 9002, 9003, 9004), autochange_id=5)

    def get_url(self, date, page):
        url_base = "https://www.lemonde.fr/archives-du-monde"
        date_string = date.strftime("%d-%m-%Y")
        url_full = f"{url_base}/{date_string}/{page}/"
        return url_full

    def get_papers_one_page(self, date, page):
        url_full = self.get_url(date=date, page=page)
        # r = requests.get(url=url_full)
        r = self.request_session.get(url=url_full)
        if r.status_code != 200:
            print(url_full)
            raise Warning(f"Status code incorect: {r.status_code}")
        else:
            # print(date)
            soup = BeautifulSoup(r.content, features="lxml")
            list_article = list_article = soup.find_all(
                "a", attrs={"class": "teaser__link"}
            )
            list_info = []
            for i, article in enumerate(list_article):
                url_article = article.get("href")
                title_article = str(article.h3.string)
                description_article = str(article.p.text)
                list_info.append([title_article, url_article, description_article])
            df = pd.DataFrame(list_info, columns=["title", "url", "description"])
            df = pd.concat([df], axis=0, keys=[date])
            return df

    def get_papers_one_day(self, date):
        # Get the number of page
        ##Procedure go to next date and "click" on previous
        url_full = self.get_url(date=date + pd.Timedelta("1D"), page=1)
        # r = requests.get(url=url_full)
        r = self.request_session.get(url=url_full)
        soup = BeautifulSoup(r.content, features="lxml")
        try:
            n_page = int(
                soup.find("link", attrs={"rel": "prev"}).get("href").split("/")[-2]
            )
        except:
            n_page = 1
        # print(n_page)
        list_df = []
        for page in range(n_page):
            page += 1
            df = self.get_papers_one_page(date=date, page=page)
            list_df.append(df)
        df = pd.concat(list_df)
        date_str = date.strftime("%Y-%m-%d")
        df.to_pickle(f"{self.path}/df_{date_str}.pkl")
        return df

    def download_all(self, retry=False):
        bar = pyprind.ProgBar(len(self.list_date))
        for date in self.list_date:
            date_str = date.strftime("%Y-%m-%d")
            if not os.path.isfile(f"{self.path}/df_{date_str}.pkl"):
                df = self.get_papers_one_day(date=date)
            bar.update()

    def load_data(self):
        final_file = f"{self.path}/DF.pkl"
        if not os.path.isfile(final_file):
            list_file = os.listdir(self.path)
            list_file = [file for file in list_file if file.startswith("df_")]
            list_df = []
            for file in list_file:
                df = pd.read_pickle(self.path + "/" + file)
                list_df.append(df)
            DF = pd.concat(list_df)
            DF.to_pickle(final_file)
        DF = pd.read_pickle(final_file)
        self.dataframe = DF
        return DF

    def is_COVID_related(self):
        def check_if_COVID_related(row):
            """Test if some COVID related keywords are mentioned"""
            title = row.lower()
            COVID_keywords = [
                "covid",
                "coronavirus",
                "2019-nCoV",
                "Covid-19",
            ]  # "épidémie", "pandémie",
            COVID_keywords = set([kw.lower() for kw in COVID_keywords])
            title_words = set(title.split())
            if COVID_keywords.intersection(title_words):
                COVID_related = True
            else:
                COVID_related = False
            return COVID_related

        self.dataframe["COVID_related"] = self.dataframe.title.apply(
            check_if_COVID_related
        )


class Lexpress:

    def __init__(
        self, start_date="2020-02-01", end_date="2023-12-31", folder_name="lexpress"
    ) -> None:
        # Create a data folder
        self.path = f"data/{folder_name}"
        if not os.path.isdir(self.path):
            os.mkdir(self.path)
        # List of days to itervate over
        self.list_date = pd.date_range(start="2020-02-01", end="2023-12-31", freq="D")
        self.request_session = requests.Session()
        # self.request_session= RequestsTor()
        # RequestsTor(tor_ports=(9000, 9001, 9002, 9003, 9004), autochange_id=5)

    def get_url(self, date, page):
        url_base = "https://www.lexpress.fr/archives/"
        date_string = date.strftime("%Y-%m-%d")
        url_full = f"{url_base}/{date_string}/{page}/"
        return url_full

    def get_papers_one_page(self, date, page):
        url_full = self.get_url(date=date, page=page)
        # r = requests.get(url=url_full)
        r = self.request_session.get(url=url_full)
        if r.status_code != 200:
            print(url_full)
            raise Warning(f"Status code incorect: {r.status_code}")
        else:
            # print(date)
            soup = BeautifulSoup(r.content, features="lxml")
            list_article = soup.find_all(
                "div", attrs={"class": "archives-article__text"}
            )
            list_info = []
            for i, article in enumerate(list_article):
                url_short = str(article.a.get("href"))
                url_article = f"https://www.lexpress.fr/{url_short}"
                title_article = str(article.a.text)
                try:
                    description_article = str(article.p.text)
                except:
                    description_article = ""
                list_info.append([title_article, url_article, description_article])
            df = pd.DataFrame(list_info, columns=["title", "url", "description"])
            df = pd.concat([df], axis=0, keys=[date])
            return df

    def get_papers_one_day(self, date):
        url_full = self.get_url(date=date, page=1)
        r = self.request_session.get(url=url_full)
        soup = BeautifulSoup(r.content, features="lxml")
        try:
            n_page = int(
                soup.find("div", attrs={"class": "paginate paginate_list"}).a.text
            )
        except:
            n_page = 1
        # print(n_page)
        list_df = []
        for page in range(n_page):
            page += 1
            df = self.get_papers_one_page(date=date, page=page)
            list_df.append(df)
        df = pd.concat(list_df)
        date_str = date.strftime("%Y-%m-%d")
        df.to_pickle(f"{self.path}/df_{date_str}.pkl")
        return df

    def download_all(self, retry=False):
        bar = pyprind.ProgBar(len(self.list_date))
        for date in self.list_date:
            date_str = date.strftime("%Y-%m-%d")
            if not os.path.isfile(f"{self.path}/df_{date_str}.pkl"):
                df = self.get_papers_one_day(date=date)
            bar.update()

    def load_data(self):
        final_file = f"{self.path}/DF.pkl"
        if not os.path.isfile(final_file):
            list_file = os.listdir(self.path)
            list_file = [file for file in list_file if file.startswith("df_")]
            list_df = []
            for file in list_file:
                df = pd.read_pickle(self.path + "/" + file)
                list_df.append(df)
            DF = pd.concat(list_df)
            DF.to_pickle(final_file)
        DF = pd.read_pickle(final_file)
        self.dataframe = DF
        return DF

    def is_COVID_related(self):
        def check_if_COVID_related(row):
            """Test if some COVID related keywords are mentioned"""
            title = row.lower()
            COVID_keywords = [
                "covid",
                "coronavirus",
                "2019-nCoV",
                "Covid-19",
            ]  # "épidémie", "pandémie",
            COVID_keywords = set([kw.lower() for kw in COVID_keywords])
            title_words = set(title.split())
            if COVID_keywords.intersection(title_words):
                COVID_related = True
            else:
                COVID_related = False
            return COVID_related

        self.dataframe["COVID_related"] = self.dataframe.title.apply(
            check_if_COVID_related
        )


class Liberation:

    def __init__(
        self, start_date="2020-02-01", end_date="2023-12-31", folder_name="liberation"
    ) -> None:
        # Create a data folder
        self.path = f"data/{folder_name}"
        if not os.path.isdir(self.path):
            os.mkdir(self.path)
        # List of days to itervate over
        self.list_date = pd.date_range(start="2020-02-01", end="2023-12-31", freq="D")
        self.request_session = requests.Session()

    def get_url(self, date):
        url_base = "https://www.liberation.fr/archives/"
        date_string = date.strftime("%Y/%m/%d")
        url_full = f"{url_base}/{date_string}"
        return url_full

    def get_papers_one_day(self, date):
        url_full = self.get_url(date=date)
        # r = requests.get(url=url_full)
        r = self.request_session.get(url=url_full)
        if r.status_code != 200:
            print(url_full)
            raise Warning(f"Status code incorect: {r.status_code}")
        else:
            # print(date)
            soup = BeautifulSoup(r.content, features="lxml")
            list_article = soup.find_all("article")
            list_info = []
            for i, article in enumerate(list_article):
                url_short = str(article.a.get("href"))
                url_article = f"https://www.liberation.fr/{url_short}"
                title_article = article.text
                list_info.append([title_article, url_article])
            df = pd.DataFrame(list_info, columns=["title", "url"])
            df = pd.concat([df], axis=0, keys=[date])
            date_str = date.strftime("%Y-%m-%d")
            df.to_pickle(f"{self.path}/df_{date_str}.pkl")
            return df

    def download_all(self, retry=False):
        bar = pyprind.ProgBar(len(self.list_date))
        for date in self.list_date:
            date_str = date.strftime("%Y-%m-%d")
            if not os.path.isfile(f"{self.path}/df_{date_str}.pkl"):
                df = self.get_papers_one_day(date=date)
            bar.update()

    def load_data(self):
        final_file = f"{self.path}/DF.pkl"
        if not os.path.isfile(final_file):
            list_file = os.listdir(self.path)
            list_file = [file for file in list_file if file.startswith("df_")]
            list_df = []
            for file in list_file:
                df = pd.read_pickle(self.path + "/" + file)
                list_df.append(df)
            DF = pd.concat(list_df)
            DF.to_pickle(final_file)
        DF = pd.read_pickle(final_file)
        self.dataframe = DF
        return DF

    def is_COVID_related(self):
        def check_if_COVID_related(row):
            """Test if some COVID related keywords are mentioned"""
            title = row.lower()
            COVID_keywords = [
                "covid",
                "coronavirus",
                "2019-nCoV",
                "Covid-19",
            ]  # "épidémie", "pandémie",
            COVID_keywords = set([kw.lower() for kw in COVID_keywords])
            title_words = set(title.split())
            if COVID_keywords.intersection(title_words):
                COVID_related = True
            else:
                COVID_related = False
            return COVID_related

        self.dataframe["COVID_related"] = self.dataframe.title.apply(
            check_if_COVID_related
        )
