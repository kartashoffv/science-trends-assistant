# pip install arxiv
import arxiv


# TODO: Обработчик на AUTHENTIFICATION ERROR (в случае долгого простоя)
# TODO: Обработка missing field error
# TODO: Придумать, как загружать документы (сейчас работает не оптимально)
# TODO: Предобработка запроса - убрать все символы


class ArxivPapers:
    def __init__(self):
        self.client = arxiv.Client()
        self.papers = []

    def get_papers(self, query, n=3, sorting="newest"):
        """Принимает запрос (ключевые слова для поиска).

        Возвращает строку из последних n статей, подходящих по запросу.
        """

        if sorting == "relevance":
            sorting_condition = arxiv.SortCriterion.Relevance
        elif sorting == "newest":
            sorting_condition = arxiv.SortCriterion.SubmittedDate
        else:
            sorting_condition = arxiv.SortCriterion.LastUpdatedDate

        search = arxiv.Search(query=query, max_results=n,
                              sort_by=sorting_condition)

        results = self.client.results(search)

        self.papers = results  # <==
        answer = []
        info_for_download = {}
        for paper in results:
            authors = " ".join([author.name for author in paper.authors])
            pdf_url = paper.pdf_url
            title = paper.title
            info_for_download[title] = pdf_url
            summary = paper.summary.replace('\n', '')

            article_info = f"{title}\n\n{paper.published}\n{authors}\n\n{summary}\n\nСсылка на оригинал{pdf_url}"
            answer.append(article_info)
            response = [answer, info_for_download]
        return response


# TODO: Обработчик на AUTHENTIFICATION ERROR (в случае долгого простоя)
