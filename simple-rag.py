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
from upload import getJavaFile
import streamlit as st
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from auth_utils import charger_config, sauvegarder_config
import javalang

folder_path = "test_code"
model = "mistral:7b-instruct-q4_0"
embedding_model = "nomic-embed-text"

logging.basicConfig(level=logging.INFO)


def ingest_java_folder(folder_path):
    loader = DirectoryLoader(
        folder_path,
        glob="*.java",
        loader_cls=TextLoader
    )
    documents = loader.load()
    return documents


def split_java_code(documents):
    text_splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.JAVA,
        chunk_size=1200,
        chunk_overlap=300
    )
    chunks = text_splitter.split_documents(documents)
    return chunks


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


def retrieve_combined(vector_db_commune, vector_db_personnelle, model, question):
    docs_communs = []
    docs_perso = []

    if vector_db_commune is not None:
        retriever_commun, llm = retrieve_from_vector_db_java(vector_db_commune, model)
        docs_communs = retriever_commun.invoke(question)

    if vector_db_personnelle is not None:
        retriever_perso, llm = retrieve_from_vector_db_java(vector_db_personnelle, model)
        docs_perso = retriever_perso.invoke(question)

    tous_les_docs = docs_communs + docs_perso
    return tous_les_docs, llm


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


def generate_response(context_docs, llm, question, historique=""):
    contexte_texte = "\n\n".join([doc.page_content for doc in context_docs])

    template = """
        Tu es un expert en revue de code Java.
        
        Voici l'historique de la conversation jusqu'a present :
        {historique}
        
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
    chain = prompt | llm | StrOutputParser()
    res = chain.invoke({"context": contexte_texte, "question": question, "historique": historique})
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


def generer_reponse_analyse(llm_model, code, resultat_analyse):
    prompt = f"""Tu es un expert en revue de code Java.

Voici un extrait de code fourni par l'utilisateur :
{code}

Voici les resultats d'une analyse automatique de ce code :
{resultat_analyse}

Consigne stricte : tu dois trouver et signaler AU MOINS un point d'amelioration
ou probleme potentiel dans le code, meme mineur (edge case non teste, absence
de validation, etc). Ne te contente jamais de dire que tout est correct.

Reponds UNIQUEMENT avec un objet JSON valide, exactement dans ce format,
sans aucun texte avant ou apres :
{{"explication": "ton explication en francais ici", "code_corrige": "le code Java corrige complet ici"}}
"""
    response = ollama.generate(model=llm_model, prompt=prompt, format="json")
    resultat = json.loads(response["response"])
    explication = resultat["explication"]
    code_corrige = resultat["code_corrige"]

    try:
        javalang.parse.parse(code_corrige)
        code_valide = True
    except Exception:
        code_valide = False

    if not code_valide:
        explication += "\n\n⚠️ Attention : le code corrige propose n'a pas pu etre valide syntaxiquement. Une verification manuelle est recommandee avant utilisation."

    return explication, code_corrige, code_valide

def sauvegarder_correction(explication, code_corrige, folder_path_utilisateur):
    contenu_final = f"""/*
 * NOTES DE CORRECTION AUTOMATIQUE :
 * {explication}
 */

{code_corrige}
"""
    nom_fichier = f"correction_{len(os.listdir(folder_path_utilisateur)) + 1}.java"
    chemin = os.path.join(folder_path_utilisateur, nom_fichier)

    with open(chemin, "w", encoding="utf-8") as f:
        f.write(contenu_final)

    return True


def formatter_historique(messages, limite=6):
    historique_recent = messages[-limite:]
    texte = ""
    for m in historique_recent:
        role = "Utilisateur" if m["role"] == "user" else "Assistant"
        texte += f"{role}: {m['content']}\n"
    return texte


def main():
    # --- Chargement sécurisé du config ---
    try:
        config = charger_config("config.yaml")
    except (FileNotFoundError, ValueError) as e:
        st.error(str(e))
        return

    # --- Validation minimale de la structure ---
    config.setdefault("preauthorized", {"emails": []})
    if "credentials" not in config or "cookie" not in config:
        st.error("Le fichier de configuration est incomplet (credentials/cookie manquants).")
        return

    # --- Clé de cookie récupérée depuis les secrets, pas depuis le YAML ---
    try:
        cookie_key = st.secrets["cookie"]["cookie_key"]
    except Exception:
        st.error("La clé de cookie est introuvable dans st.secrets. Vérifie .streamlit/secrets.toml.")
        return

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        cookie_key,
        config['cookie']['expiry_days']
    )

    authenticator.login()

    auth_status = st.session_state.get('authentication_status')

    if auth_status is False:
        st.error("Nom d'utilisateur/mot de passe incorrect")
        return

    elif auth_status is None:
        st.warning("Merci d'entrer votre nom d'utilisateur et mot de passe")

        st.divider()
        st.subheader("Pas encore de compte ?")
        try:
            email, username, name = authenticator.register_user(pre_authorized=config['preauthorized']['emails'])
            if email:
                st.success("Compte cree avec succes ! Vous pouvez maintenant vous connecter.")
                sauvegarder_config(config, "config.yaml")
        except Exception as e:
            st.error(e)

        return

    elif auth_status is True:
        authenticator.logout()

        username = st.session_state.get('username')
        folder_path_utilisateur = f"test_code_{username}"
        persist_directory_utilisateur = f"chroma_db_java_{username}"
        tracking_file_utilisateur = f"fichiers_indexes_{username}.json"
        os.makedirs(folder_path_utilisateur, exist_ok=True)

        if "messages" not in st.session_state:
            st.session_state.messages = []

        st.title("Hello, welcome to AI space!")
        st.markdown("""
        <style>
        button[data-testid="stChatInputSubmitButton"] {
            background-color: skyblue !important;
        }
        button[data-testid="stChatInputSubmitButton"] svg {
            fill: white !important;
        }
        </style>
    """, unsafe_allow_html=True)

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # --- Base COMMUNE (partagee par tous les utilisateurs) ---
        if "vector_db" not in st.session_state:
            st.session_state.vector_db = None

        if folder_path is not None and st.session_state.vector_db is None:
            a_change, fichiers_actuels = liste_fichiers_a_change(folder_path)

            if a_change:
                with st.spinner("Nouveaux fichiers detectes dans la base commune, traitement en cours..."):
                    try:
                        documents = ingest_java_folder(folder_path)
                        chunks = split_java_code(documents)
                        st.session_state.vector_db = add_to_vector_db(chunks, embedding_model, persist_directory="chroma_db_java", collection_name="java_code")

                        with open("fichiers_indexes.json", "w") as f:
                            json.dump(fichiers_actuels, f)
                    except Exception as e:
                        st.error(f"Erreur lors de l'indexation de la base commune : {str(e)}")
                        return
            else:
                st.session_state.vector_db = add_to_vector_db(None, embedding_model, persist_directory="chroma_db_java", collection_name="java_code")

        # --- Base PERSONNELLE (propre a chaque utilisateur) ---
        if "vector_db_personnelle" not in st.session_state:
            st.session_state.vector_db_personnelle = None

        fichiers_perso = os.listdir(folder_path_utilisateur)
        if fichiers_perso:
            a_change_perso, fichiers_actuels_perso = liste_fichiers_a_change(folder_path_utilisateur, tracking_file_utilisateur)

            if a_change_perso:
                with st.spinner("Traitement de vos fichiers personnels..."):
                    try:
                        documents_perso = ingest_java_folder(folder_path_utilisateur)
                        chunks_perso = split_java_code(documents_perso)
                        st.session_state.vector_db_personnelle = add_to_vector_db(chunks_perso, embedding_model, persist_directory=persist_directory_utilisateur, collection_name="java_code_perso")

                        with open(tracking_file_utilisateur, "w") as f:
                            json.dump(fichiers_actuels_perso, f)
                    except Exception as e:
                        st.error(f"Erreur lors de l'indexation de vos fichiers personnels : {str(e)}")
            else:
                st.session_state.vector_db_personnelle = add_to_vector_db(None, embedding_model, persist_directory=persist_directory_utilisateur, collection_name="java_code_perso")
        else:
            st.info("Vous n'avez pas encore de fichiers personnels. Seule la base commune sera utilisee.")

        st.divider()
        if "afficher_upload" not in st.session_state:
            st.session_state.afficher_upload = False

        if st.button("➕ Ajouter un fichier"):
            st.session_state.afficher_upload = not st.session_state.afficher_upload

        if st.session_state.afficher_upload:
            getJavaFile(folder_path_utilisateur)

        input_question = st.chat_input("Enter your question here:")

        if input_question:
            if st.session_state.vector_db is None:
                st.warning("Merci d'uploader un document PDF avant de poser une question.")
                return

            st.session_state.messages.append({"role": "user", "content": input_question})
            with st.chat_message("user"):
                st.write(input_question)

            with st.spinner("Processing your question..."):
                try:
                    if est_du_code(input_question):
                        resultat_mcp = asyncio.run(appeler_analyser_code(input_question))
                        explication, code_corrige, code_valide = generer_reponse_analyse(model, input_question, resultat_mcp)
                        reponse_finale = f"{explication}\n\n```java\n{code_corrige}\n```"
                        if code_valide:
                            sauvegarder_correction(explication, code_corrige, folder_path_utilisateur)
                            st.info("Cette correction a ete ajoutee a votre base personnelle.")
                        else:
                            st.warning("Le code corrige n'a pas pu etre valide syntaxiquement, il n'a pas ete ajoute a votre base personnelle.")
                    else:
                        context_docs, llm = retrieve_combined(st.session_state.vector_db, st.session_state.vector_db_personnelle, model, input_question)
                        historique_texte = formatter_historique(st.session_state.messages)
                        reponse_finale = generate_response(context_docs, llm, input_question, historique_texte)

                    st.session_state.messages.append({"role": "assistant", "content": reponse_finale})
                    with st.chat_message("assistant"):
                        st.write(reponse_finale)

                    st.success("Done processing your question!")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        else:
            st.info("Please enter a question to get started.")


if __name__ == "__main__":
    main()