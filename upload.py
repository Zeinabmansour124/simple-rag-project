import streamlit as st
import os

def getJavaFile(dossier_destination):
    uploaded_document = st.file_uploader("Choisir un fichier .java", type=["java"])
    if uploaded_document is not None:
        os.makedirs(dossier_destination, exist_ok=True)
        with open(os.path.join(dossier_destination, uploaded_document.name), "wb") as f:
            f.write(uploaded_document.getbuffer())
            st.success(f"Fichier {uploaded_document.name} ajoute avec succes !")
        doc_path = os.path.join(dossier_destination, uploaded_document.name)
    else:
        doc_path = None
    return doc_path