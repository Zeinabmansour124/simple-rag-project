import logging
import os
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import ollama
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnablePassthrough
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import DirectoryLoader
from upload import getDoc 
import streamlit as st
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language



def ingest_java_folder(folder_path):
    loader = DirectoryLoader(
        folder_path,
        glob="*.java",
        loader_cls=TextLoader
    )
    documents = loader.load()
    return documents


#def split_pdf(documents):
#    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=300)
#    chunks = text_splitter.split_documents(documents)
#    logging.info("Documents split successfully")
#    return chunks

def split_java_code(documents):
    text_splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.JAVA,
        chunk_size=1200,
        chunk_overlap=300
    )
    chunks = text_splitter.split_documents(documents)
    return chunks

def main():
    documents = ingest_java_folder("test_code")
    chunks = split_java_code(documents)
    print(f"Nombre de chunks crees : {len(chunks)}")
    print(chunks[0].page_content)  # affiche le premier chunk en entier

if __name__ == "__main__":
    main()