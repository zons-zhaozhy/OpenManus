import re
from typing import List

import requests
from bs4 import BeautifulSoup

from app.tool.search.base import SearchItem, WebSearchEngine

# 保留原有的导入，但注释掉不再使用的baidusearch导入
# from baidusearch.baidusearch import search


class BaiduSearchEngine(WebSearchEngine):
    def perform_search(
        self, query: str, num_results: int = 10, *args, **kwargs
    ) -> List[SearchItem]:
        """
        Baidu search engine.

        Returns results formatted according to SearchItem model.
        Uses direct requests and BeautifulSoup instead of baidusearch library.
        """
        try:
            # 尝试使用baidusearch库
            try:
                from baidusearch.baidusearch import search

                raw_results = search(query, num_results=num_results)
                return self._process_baidusearch_results(raw_results)
            except ImportError:
                # 如果baidusearch库不可用，使用自定义实现
                return self._custom_baidu_search(query, num_results)
        except Exception as e:
            # 如果发生任何错误，返回错误信息
            return [
                SearchItem(
                    title="搜索错误", url="", description=f"百度搜索出错: {str(e)}"
                )
            ]

    def _custom_baidu_search(
        self, query: str, num_results: int = 10
    ) -> List[SearchItem]:
        """自定义百度搜索实现，不依赖baidusearch库"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

        results = []

        try:
            url = f"https://www.baidu.com/s?wd={query}&rn={num_results}"
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            search_results = soup.select(".result.c-container")

            for i, result in enumerate(search_results):
                if i >= num_results:
                    break

                # 提取标题
                title_elem = result.select_one(".t")
                title = (
                    title_elem.get_text().strip()
                    if title_elem
                    else f"百度搜索结果 {i+1}"
                )

                # 提取URL
                link_elem = title_elem.find("a") if title_elem else None
                url = link_elem.get("href", "") if link_elem else ""

                # 提取描述
                desc_elem = result.select_one(".c-abstract")
                description = desc_elem.get_text().strip() if desc_elem else None

                results.append(
                    SearchItem(title=title, url=url, description=description)
                )

            # 如果结果不足，添加一个提示
            if len(results) < num_results:
                results.append(
                    SearchItem(
                        title="提示",
                        url="",
                        description=f"只找到 {len(results)} 个搜索结果，少于请求的 {num_results} 个结果",
                    )
                )

        except Exception as e:
            results.append(
                SearchItem(
                    title="搜索错误",
                    url="",
                    description=f"自定义百度搜索出错: {str(e)}",
                )
            )

        return results

    def _process_baidusearch_results(self, raw_results) -> List[SearchItem]:
        """处理baidusearch库返回的结果"""
        results = []
        for i, item in enumerate(raw_results):
            if isinstance(item, str):
                # 如果只是URL
                results.append(
                    SearchItem(title=f"百度搜索结果 {i+1}", url=item, description=None)
                )
            elif isinstance(item, dict):
                # 如果是包含详细信息的字典
                results.append(
                    SearchItem(
                        title=item.get("title", f"百度搜索结果 {i+1}"),
                        url=item.get("url", ""),
                        description=item.get("abstract", None),
                    )
                )
            else:
                # 尝试直接获取属性
                try:
                    results.append(
                        SearchItem(
                            title=getattr(item, "title", f"百度搜索结果 {i+1}"),
                            url=getattr(item, "url", ""),
                            description=getattr(item, "abstract", None),
                        )
                    )
                except Exception:
                    # 回退到基本结果
                    results.append(
                        SearchItem(
                            title=f"百度搜索结果 {i+1}", url=str(item), description=None
                        )
                    )

        return results
