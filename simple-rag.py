import logging

from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_community.document_loaders import OnlinePDFLoader
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
import ollama
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnablePassthrough
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from upload import getDoc 
import streamlit as st

doc_path = getDoc()
model="mistral"
embedding_model="nomic-embed-text"

logging.basicConfig(level=logging.INFO)

def ingest_pdf(doc_path, model):
   if doc_path:
    loader = UnstructuredPDFLoader(file_path=doc_path)
    documents = loader.load()
    print("done  loading the pdf file")
   else :
    print("please provide a valid pdf file path")
    raise ValueError("chemin invalide")

   return documents

def split_pdf(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=300)
    chunks=text_splitter.split_documents(documents)
    print("done splitting")
    return chunks


def add_to_vector_db(chunks, embedding_model):
  ollama.pull(embedding_model)
  vector_db=Chroma.from_documents(
    documents=chunks,
    embedding=OllamaEmbeddings(model=embedding_model),
    collection_name="simple_rag" 
)
  print("done adding to vector database")
  return vector_db

def retrieve_from_vector_db(vector_db, model):
  llm=ChatOllama(model=model)
  QUERY_PROMPT=PromptTemplate(
    input_variables=["question"],
    template=""" You are an AI language model assistant . your task is to generate five 
    different versions of the givent user question to retreive relevant documents from 
    the vector database . By generating multiple versions of the question , your goal is 
    to help the user overcome some of the limitations of the distance-based similarity search.
    Provide these alternative questions separated by new lines.
    Original question : {question},
    """ 
)
  retriever=MultiQueryRetriever.from_llm(
    vector_db.as_retriever(),
    llm=llm,
    prompt=QUERY_PROMPT,
)
  return retriever,llm


def generate_response(retriever,llm,question):
  template="""
            Answer the question based only on the following context
            {context}
            Question : {question}
        """

  prompt=ChatPromptTemplate.from_template(template)
  chain=(
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm 
    | StrOutputParser()
    )
  res = chain.invoke(question)
  return res

def main():
    st.title("Hello, welcome to the PDF RAG app!")

    input=st.text_input("Enter your question here:")
    if input:
      with st.spinner("Processing your question..."):
        try:
          documents=ingest_pdf(doc_path, model)
          chunks=split_pdf(documents)
          vector_db=add_to_vector_db(chunks, embedding_model)
          if vector_db is None:
            st.error("Vector database is empty. Please check the PDF file.")
            return
          retriever,llm=retrieve_from_vector_db(vector_db, model)
          response=generate_response(retriever,llm,input)
          st.write(response)
          st.success("Done processing your question!")
        except Exception as e:
          st.error(f"An error occurred: {str(e)}")
    else:
      st.info("Please enter a question to get started.")

if __name__ == "__main__":
    main()