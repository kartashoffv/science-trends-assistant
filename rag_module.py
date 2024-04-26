from langchain_community.embeddings.gigachat import GigaChatEmbeddings
from langchain.vectorstores import Chroma
from langchain_community.document_loaders import UnstructuredMarkdownLoader, PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders.csv_loader import CSVLoader
import os
from dotenv import load_dotenv
load_dotenv()

CREDENTIALS = os.getenv('OPENAI_API_KEY')


class GigaRAG:
    def __init__(self) -> None:
        self.embeddings = GigaChatEmbeddings(
            credentials=CREDENTIALS,
            verify_ssl_certs=False,
            scope='GIGACHAT_API_CORP'
        )

    def file_vectorization(self, file_path, file_extension, chunk_size=1000):
        if file_extension == '.pdf':
            loader = PyPDFLoader(file_path)
            data = loader.load()
            chunk_size = chunk_size
            chunk_overlap = 0
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            splitted_docs = text_splitter.split_documents(data)

            return splitted_docs

        elif file_extension == '.docx':
            loader = Docx2txtLoader(file_path)
            data = loader.load()
            chunk_size = chunk_size
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=0
            )
            splitted_docs = text_splitter.split_documents(data)

            return splitted_docs

        elif file_extension == '.md':
            loader = UnstructuredMarkdownLoader(file_path)
            data = loader.load()
            chunk_size = chunk_size
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=0
            )
            splitted_docs = text_splitter.split_documents(data)
            return splitted_docs

        elif file_extension == '.csv':
            loader = CSVLoader(file_path)
            data = loader.load()
            return data

    def create_chroma(self, documents, persist_directory=False):
        return Chroma.from_documents(
            documents,
            self.embeddings,
            persist_directory=persist_directory
        )

    def chroma_as_retriever(self, persist_directory):
        vectorstore = Chroma(persist_directory=persist_directory,
                             embedding_function=self.embeddings)
        return vectorstore.as_retriever()

    def add_documents(self, doc, file_extension, persist_directory):
        doc_splits = self.file_vectorization(doc, file_extension)
        vectorstore = self.chroma_as_retriever(persist_directory)
        vectorstore.add_documents(doc_splits)
        return vectorstore
