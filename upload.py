import streamlit as st
import os 

def getDoc():
    st.title("PDF Uploader")
    uploaded_document = st.file_uploader("Upload a PDF file", type=["pdf"])
    if uploaded_document is not None:
        os.makedirs("uploaded_docs", exist_ok=True)    
        with open(os.path.join("uploaded_docs", uploaded_document.name), "wb") as f:
            f.write(uploaded_document.getbuffer())
            st.success("File uploaded successfully!")
            doc_path = os.path.join("uploaded_docs", uploaded_document.name)

    else:
        st.warning("Please upload a PDF file.")
        doc_path = None
    return doc_path