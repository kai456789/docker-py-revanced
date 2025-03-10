"""Downloader Class."""
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag
from loguru import logger

from scripts.status_check import headers
from src.downloader.download import Downloader
from src.downloader.sources import APK_MIRROR_BASE_URL, apk_sources
from src.exceptions import APKMirrorAPKDownloadFailure
from src.utils import bs4_parser


class ApkMirror(Downloader):
    """Files downloader."""

    def _extract_force_download_link(self, link: str, app: str) -> None:
        """Extract force download link."""
        notes_divs = self._extracted_search_div(link, "tab-pane")
        possible_links = notes_divs.find_all("a")
        for possible_link in possible_links:
            if possible_link.get("href") and "download.php?id=" in possible_link.get(
                "href"
            ):
                return self._download(
                    APK_MIRROR_BASE_URL + possible_link["href"], f"{app}.apk"
                )
        raise APKMirrorAPKDownloadFailure(
            f"Unable to extract force download for {app}", url=link
        )

    def extract_download_link(self, main_page: str, app: str) -> None:
        """Function to extract the download link from apkmirror html page.

        :param main_page: Url of the page
        :param app: Name of the app
        """
        logger.debug(f"Extracting download link from\n{main_page}")
        download_button = self._extracted_search_div(main_page, "center")
        download_links = download_button.find_all("a")
        if final_download_link := next(
            (
                download_link["href"]
                for download_link in download_links
                if download_link.get("href")
                and "download/?key=" in download_link.get("href")
            ),
            None,
        ):
            self._extract_force_download_link(
                APK_MIRROR_BASE_URL + final_download_link, app
            )
        else:
            raise APKMirrorAPKDownloadFailure(
                f"Unable to extract link from {app} version list", url=main_page
            )

    def get_download_page(self, main_page: str) -> str:
        """Function to get the download page in apk_mirror.

        :param main_page: Main Download Page in APK mirror(Index)
        :return:
        """
        list_widget = self._extracted_search_div(main_page, "listWidget")
        table_rows = list_widget.find_all(class_="table-row")
        sub_url = None
        for row in table_rows:
            if row.find(class_="accent_color"):
                apk_type = row.find(class_="apkm-badge").get_text()
                if apk_type == "APK" and (
                    "arm64-v8a" in row.text.strip()
                    or "universal" in row.text.strip()
                    or "noarch" in row.text.strip()
                ):
                    sub_url = row.find(class_="accent_color")["href"]
                    break
        if not sub_url:
            raise APKMirrorAPKDownloadFailure(
                "Unable to extract download page", url=main_page
            )
        return f"{APK_MIRROR_BASE_URL}{sub_url}"

    @staticmethod
    def _extracted_search_div(url: str, search_class: str) -> Tag:
        """Extract search div."""
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            raise APKMirrorAPKDownloadFailure(
                f"Unable to connect with {url} on ApkMirror. Are you blocked by APKMirror or abused apkmirror "
                f"?.Reason - {r.text}",
                url=url,
            )
        soup = BeautifulSoup(r.text, bs4_parser)
        return soup.find(class_=search_class)

    def specific_version(self, app: str, version: str, main_page: str = "") -> None:
        """Function to download the specified version of app from  apkmirror.

        :param app: Name of the application
        :param version: Version of the application to download
        :param main_page: Version of the application to download
        :return: Version of downloaded apk
        """
        if not main_page:
            version = version.replace(".", "-")
            apk_main_page = apk_sources[app]
            version_page = apk_main_page + apk_main_page.split("/")[-2]
            main_page = f"{version_page}-{version}-release/"
        download_page = self.get_download_page(main_page)
        self.extract_download_link(download_page, app)

    def latest_version(self, app: str, **kwargs: Any) -> None:
        """Function to download whatever the latest version of app from
        apkmirror.

        :param app: Name of the application
        :return: Version of downloaded apk
        """

        app_main_page = apk_sources[app]
        versions_div = self._extracted_search_div(
            app_main_page, "listWidget p-relative"
        )
        app_rows = versions_div.find_all(class_="appRow")
        version_urls = [
            app_row.find(class_="downloadLink")["href"]
            for app_row in app_rows
            if "beta" not in app_row.find(class_="appRowTitle").get_text().lower()
            and "alpha" not in app_row.find(class_="appRowTitle").get_text().lower()
        ]
        return self.specific_version(
            app, "latest", APK_MIRROR_BASE_URL + max(version_urls)
        )
