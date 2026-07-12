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
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

#doc_path = getDoc()
folder_path="test_code"
model = "mistral:7b-instruct-q4_0"
embedding_model = "nomic-embed-text"

logging.basicConfig(level=logging.INFO)

#def ingest_pdf(doc_path, model):
#    if doc_path:
#        loader = PDFPlumberLoader(file_path=doc_path)
#        documents = loader.load()
#        logging.info("PDF file loaded successfully")
#    else:
#        logging.error("Invalid PDF file path provided")
#        raise ValueError("chemin invalide")
    
#    return documents


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

#def add_to_vector_db(chunks, embedding_model):
#    if os.path.exists("chroma_db"):
#       if os.path.exists("chroma_db"):
#        vector_db = Chroma(
#            persist_directory="chroma_db",
#            embedding_function=OllamaEmbeddings(model=embedding_model),
#            collection_name="simple_rag"
#        )
#        logging.info("Base vectorielle existante chargee.")
#        return vector_db
#    else:
#        ollama.pull(embedding_model)  
#        print(os.path.exists("chroma_db"))
#        try:
#            vector_db = Chroma.from_documents(
#                documents=chunks,
#                embedding=OllamaEmbeddings(model=embedding_model),
#                persist_directory="chroma_db",
#                collection_name="simple_rag"
#                                )
#            logging.info(f"Vector DB créée avec {len(chunks)} chunks.")
#            return vector_db
#        except Exception as e:
#            logging.error(f"Erreur lors de la création de la vector DB : {str(e)}")
#            raise

def add_to_vector_db(chunks, embedding_model, persist_directory="chroma_db", collection_name="simple_rag"):
    if os.path.exists(persist_directory):
        vector_db = Chroma(
            persist_directory=persist_directory,
            embedding_function=OllamaEmbeddings(model=embedding_model),
            collection_name=collection_name
        )
        logging.info("Base vectorielle existante chargee.")
        return vector_db
    else:
        ollama.pull(embedding_model)
        try:
            vector_db = Chroma.from_documents(
                documents=chunks,
                embedding=OllamaEmbeddings(model=embedding_model),
                persist_directory=persist_directory,
                collection_name=collection_name
            )
            logging.info(f"Vector DB créée avec {len(chunks)} chunks.")
            return vector_db
        except Exception as e:
            logging.error(f"Erreur lors de la création de la vector DB : {str(e)}")
            raise

#def retrieve_from_vector_db(vector_db, model):
#    llm = ChatOllama(model=model)
#    QUERY_PROMPT = PromptTemplate(
#        input_variables=["question"],
#        template=""" You are an AI language model assistant. Your task is to generate five 
#        different versions of the given user question to retrieve relevant documents from 
#        the vector database. By generating multiple versions of the question, your goal is 
#        to help the user overcome some of the limitations of the distance-based similarity search.
#        Provide these alternative questions separated by new lines.
#        Original question: {question}
#        """ 
#    )
#    retriever = MultiQueryRetriever.from_llm(
#        vector_db.as_retriever(),
#        llm=llm,
#        prompt=QUERY_PROMPT,
#    )
#    return retriever, llm
def retrieve_from_vector_db_java(vector_db, model):
    llm = ChatOllama(model=model)
    QUERY_PROMPT = PromptTemplate(
        input_variables=["question"],
        template=""" You are an AI language model assistant specialized in Java code analysis.
        Your task is to generate five different versions of the given user question to retrieve
        relevant code snippets from the vector database. By generating multiple versions of the
        question, your goal is to help the user overcome some of the limitations of the
        distance-based similarity search, taking into account class names, method names, and
        common code-review terminology (bug, error, exception, refactor, best practice).
        Provide these alternative questions separated by new lines.
        Original question: {question}
        """ 
    )
    retriever = MultiQueryRetriever.from_llm(
        vector_db.as_retriever(),
        llm=llm,
        prompt=QUERY_PROMPT,
    )
    return retriever, llm

def generate_response(retriever, llm, question):
    template = """
        Tu es un expert en revue de code Java.
        
        Consigne stricte : tu dois trouver et signaler AU MOINS un point 
        d'amelioration ou probleme potentiel dans le code, meme mineur 
        (edge case non teste, absence de setter, absence de validation, etc).
        Ne te contente jamais de decrire le code sans emettre un avis critique.
        
        Pour chaque probleme trouve, cite la methode ou variable concernee.
        
        Contexte (code source) :
        {context}
        
        Question : {question}
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm 
        | StrOutputParser()
    )
    res = chain.invoke(question)
    return res

async def appeler_analyser_code(code):
    server_params = StdioServerParameters(
        command="python",
        args=["mcp-test.py"]
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("analyser_code", {"code": code})
            return result
def est_du_code(texte):
    indices_code = ["public ", "private ", "class ", "void ", "{", "}", ";"]
    compteur = sum(1 for indice in indices_code if indice in texte)
    return compteur >= 3

def liste_fichiers_a_change(folder_path, tracking_file="fichiers_indexes.json"):
    fichiers_actuels = sorted(os.listdir(folder_path))
    
    if not os.path.exists(tracking_file):
        return True, fichiers_actuels
    
    with open(tracking_file, "r") as f:
        fichiers_precedents = json.load(f)
    
    a_change = fichiers_actuels != fichiers_precedents
    return a_change, fichiers_actuels

def generer_reponse_analyse(llm, code, resultat_analyse):
    template = """
        Tu es un expert en revue de code Java.
        
        Voici un extrait de code fourni par l'utilisateur :
        {code}
        
        Voici les resultats d'une analyse automatique de ce code :
        {resultat_analyse}
        
        En te basant sur ces resultats et sur le code, redige une explication
        claire en francais : indique si le code presente des risques ou 
        ameliorations possibles, et propose une correction concrete si pertinent.
    """
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    reponse = chain.invoke({"code": code, "resultat_analyse": str(resultat_analyse)})
    return reponse

def main():
    st.title("Hello, welcome to AI space!")

    if "vector_db" not in st.session_state:
        st.session_state.vector_db = None

    if folder_path is not None and st.session_state.vector_db is None:
        a_change, fichiers_actuels = liste_fichiers_a_change(folder_path)

        if a_change:
            with st.spinner("Nouveaux fichiers detectes, traitement en cours..."):
                try:
                    documents = ingest_java_folder(folder_path)
                    chunks = split_java_code(documents)
                    st.session_state.vector_db = add_to_vector_db(chunks, embedding_model, persist_directory="chroma_db_java", collection_name="java_code")

                    with open("fichiers_indexes.json", "w") as f:
                        json.dump(fichiers_actuels, f)

                    st.success("Document indexé avec succès !")
                except Exception as e:
                    st.error(f"Erreur lors de l'indexation du document : {str(e)}")
                    return
        else:
            st.session_state.vector_db = add_to_vector_db(None, embedding_model, persist_directory="chroma_db_java", collection_name="java_code")
            st.info("Aucun nouveau fichier, base existante reutilisee.")

    input_question = st.text_input("Enter your question here:")

    if input_question:
        if st.session_state.vector_db is None:
            st.warning("Merci d'uploader un document PDF avant de poser une question.")
            return

        with st.spinner("Processing your question..."):
            try:
                if est_du_code(input_question):
                    resultat_mcp = asyncio.run(appeler_analyser_code(input_question))
                    llm = ChatOllama(model=model)
                    reponse_finale = generer_reponse_analyse(llm, input_question, resultat_mcp)
                    st.write(reponse_finale)
                else:
                    retriever, llm = retrieve_from_vector_db_java(st.session_state.vector_db, model)
                    response = generate_response(retriever, llm, input_question)
                    st.write(response)
                st.success("Done processing your question!")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    else:
        st.info("Please enter a question to get started.")

if __name__ == "__main__":
    main()