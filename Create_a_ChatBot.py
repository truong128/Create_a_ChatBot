import streamlit as st
import openai
import pandas as pd
import os
import base64
from PIL import Image
import io
import PyPDF2
import tempfile

# Set OpenAI API key directly
openai.api_key = "add Your OpenAI API here"

# Configure page settings
st.set_page_config(
    page_title="Truong Nguyen ChatBot",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS with color names
st.markdown("""
    <style>
    /* Main title and headers */
    .stApp h1 {
        font-size: 48px !important;
    }
    
    .stApp h3 {
        font-size: 36px !important;
    }
    
    /* Chat container and messages */
    .stChatMessage {
        font-size: 28px !important;
    }
    
    /* Chat input box */
    .stChatInputContainer textarea {
        font-size: 28px !important;
        height: 100px !important;  /* Make input box taller */
    }
    
    /* Message content */
    .stChatMessage p {
        font-size: 28px !important;
        line-height: 1.8 !important;  /* Reduced line height for better readability */
    }
    
    /* User/Assistant labels */
    .stChatMessage .name-text {
        font-size: 24px !important;
        font-weight: bold;
    }
    
    /* Sidebar text */
    .css-1d391kg {
        font-size: 20px !important;
    }
    
    /* File uploader text */
    .stUploadMessage {
        font-size: 24px !important;
    }
    
    /* Chat input placeholder */
    textarea::placeholder {
        font-size: 28px !important;
    }
    
    /* Button text */
    .stButton > button {
        font-size: 24px !important;
        padding: 10px 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'current_doc_content' not in st.session_state:
        st.session_state.current_doc_content = None
    if 'current_doc_type' not in st.session_state:
        st.session_state.current_doc_type = None
    if 'current_doc_name' not in st.session_state:
        st.session_state.current_doc_name = None

def read_pdf(file):
    """Read PDF file and return text content"""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

def read_excel(file):
    """Read Excel file and return DataFrame"""
    try:
        df = pd.read_excel(file)
        return df
    except Exception as e:
        st.error(f"Error reading Excel file: {str(e)}")
        return None

def process_image(image_file):
    """Process uploaded image"""
    try:
        image = Image.open(image_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        
        buffered = io.BytesIO()
        image.save(buffered, format=image.format)
        image_bytes = buffered.getvalue()
        
        with st.spinner('Analyzing image...'):
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What's in this image?"},
                            {
                                "type": "image_url",
                                "image_url": f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode()}"
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            analysis = response['choices'][0]['message']['content']
            st.markdown(f"### Image Analysis\n{analysis}")
            
            # Store image analysis in chat history
            st.session_state.messages.append({"role": "assistant", "content": f"I've analyzed the image. Here's what I see:\n\n{analysis}"})
        
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")

def process_document(file, file_type):
    """Process uploaded document"""
    try:
        with st.spinner(f'Processing {file_type} file...'):
            content = None
            if file_type == "PDF":
                content = read_pdf(file)
                if content:
                    st.markdown("### PDF Content Preview")
                    st.text_area("Content", content[:2000] + "...", height=500)
                    # Store content in session state
                    st.session_state.current_doc_content = content
                    st.session_state.current_doc_type = "PDF"

            elif file_type == "Excel":
                df = read_excel(file)
                if df is not None:
                    st.markdown("### Excel Preview")
                    st.dataframe(df.head(), use_container_width=True)
                    content = df.to_string()
                    # Store content in session state
                    st.session_state.current_doc_content = content
                    st.session_state.current_doc_type = "Excel"

            # Analyze content with GPT-4
            if content:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": f"You are analyzing a {file_type} document. Keep this context for future questions."},
                        {"role": "user", "content": f"Please analyze this document and provide a summary:\n\n{content[:4000]}"}
                    ]
                )
                analysis = response['choices'][0]['message']['content']
                st.markdown(f"### Document Analysis\n{analysis}")
                
                # Store initial analysis in chat history
                st.session_state.messages.append({"role": "assistant", "content": f"I've analyzed the {file_type} document. Here's the summary:\n\n{analysis}"})

    except Exception as e:
        st.error(f"Error processing document: {str(e)}")

def main():
    initialize_session_state()
    
    # Sidebar with instructions and current document info
    with st.sidebar:
        st.title("Instructions")
        st.markdown("""
        ### Supported Files
        - Images (PNG, JPG, JPEG)
        - PDF Documents
        - Excel Files (XLSX)
        
        ### How to Use
        1. Upload your file using the upload button
        2. View the analysis
        3. Chat with the AI about the documents
        """)
        
        if st.session_state.current_doc_type:
            st.markdown("---")
            st.markdown(f"### Current Document\nType: {st.session_state.current_doc_type}")
    
    # Main interface
    st.title("Truong Nguyen ChatBot 📄")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload a file", 
        type=['png', 'jpg', 'jpeg', 'pdf', 'xlsx']
    )
    
    if uploaded_file is not None:
        file_type = uploaded_file.type
        st.write(f"Processing: {uploaded_file.name}")
        st.session_state.current_doc_name = uploaded_file.name
        
        if file_type in ['image/png', 'image/jpeg']:
            process_image(uploaded_file)
        elif file_type == 'application/pdf':
            process_document(uploaded_file, "PDF")
        elif file_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            process_document(uploaded_file, "Excel")
    
    # Chat interface
    st.markdown("---")
    st.markdown("### Chat")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about the documents or type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                messages = [
                    {"role": "system", "content": "You are a helpful assistant analyzing documents. "
                     f"Current document type: {st.session_state.current_doc_type if st.session_state.current_doc_type else 'None'}"}
                ]
                
                # Add document content for context if available
                if st.session_state.current_doc_content:
                    messages.append({
                        "role": "user",
                        "content": f"Here's the document content:\n\n{st.session_state.current_doc_content[:4000]}"
                    })
                
                # Add chat history
                messages.extend([{"role": m["role"], "content": m["content"]} 
                               for m in st.session_state.messages])
                
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=messages
                )
                reply = response['choices'][0]['message']['content']
                message_placeholder.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # Clear all button
    if st.button("Clear All"):
        st.session_state.messages = []
        st.session_state.current_doc_content = None
        st.session_state.current_doc_type = None
        st.session_state.current_doc_name = None
        st.experimental_rerun()

if __name__ == "__main__":
    main()
