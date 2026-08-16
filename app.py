import streamlit as st
import openai
import json
import docx
from io import BytesIO
from docx import Document

# Page Configuration
st.set_page_config(
    page_title="Form I-589 Legal Intake & Affidavit Generator",
    page_icon="📄",
    layout="wide"
)

# Sidebar Navigation
st.sidebar.title("Form I-589 Suite")
page = st.sidebar.radio("Navigation", ["🏠 Overview", "🤖 Intake & Affidavit Generator"])

openai_api_key = st.secrets.get("OPENAI_API_KEY")

if page == "🏠 Overview":
    st.title("📄 Form I-589 Legal Intake & Affidavit Generator")
    st.subheader("Multimodal Legal Data Pipeline")

    st.markdown("""
    This application transforms unstructured legal intakes—whether text, documents, or WhatsApp audio—into 
    standardized USCIS-compliant legal packets. 
    """)

elif page == "🤖 Intake & Affidavit Generator":
    st.title("🤖 Multimodal Intake Generator")
    
    if not openai_api_key:
        st.warning("⚠️ Please configure your OPENAI_API_KEY in your Streamlit app secrets.")
    else:
        client = openai.OpenAI(api_key=openai_api_key)

        # INPUT OPTIONS: Text, Document, or Audio
        input_type = st.radio("Choose intake source:", ["Paste Text Notes", "Upload Document (.txt, .docx)", "Upload Audio Recording (WhatsApp/MP3/WAV)"])
        
        client_input = ""

        if input_type == "Paste Text Notes":
            client_input = st.text_area("Paste Raw Notes:", height=200)

        elif input_type == "Upload Document (.txt, .docx)":
            uploaded_file = st.file_uploader("Upload client transcript:", type=["txt", "docx"])
            if uploaded_file:
                if uploaded_file.name.endswith(".txt"):
                    client_input = uploaded_file.getvalue().decode("utf-8")
                else:
                    doc = docx.Document(uploaded_file)
                    client_input = "\n".join([para.text for para in doc.paragraphs])
                st.text_area("Review Extracted Text:", value=client_input, height=100)

        elif input_type == "Upload Audio Recording (WhatsApp/MP3/WAV)":
            # Added support for WhatsApp audio formats (ogg, opus)
            audio_file = st.file_uploader("Upload interview audio (WhatsApp/MP3/WAV/OGG):", type=["mp3", "wav", "m4a", "ogg", "opus"])
            if audio_file and st.button("Transcribe Audio"):
                with st.spinner("Transcribing..."):
                    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                    client_input = transcript.text
                    st.success("Transcription complete!")
                    st.text_area("Review Transcript:", value=client_input, height=100)

        # GENERATION LOGIC
        if st.button("Generate Legal Intake Packet & Affidavit 🚀", type="primary"):
            if client_input.strip():
                with st.spinner("Extracting biographic parameters and drafting narrative..."):
                    try:
                        system_prompt = (
                            "You are an expert immigration paralegal. "
                            "Extract data into JSON: full_name, dob, citizenship, current_us_address, "
                            "date_of_entry, manner_of_entry, spouse_and_children, persecuting_agent, "
                            "harm_feared, police_involvement, draft_affidavit_narrative."
                        )

                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": client_input}],
                            response_format={"type": "json_object"},
                            temperature=0.0
                        )

                        data = json.loads(response.choices[0].message.content)

                        # UI PREVIEW
                        st.success("Packet Generated!")
                        st.json(data)

                        # WORD EXPORT
                        doc = Document()
                        doc.add_heading("Form I-589 Legal Intake Packet", level=1)
                        for key, val in data.items():
                            doc.add_heading(key.replace('_', ' ').title(), level=2)
                            doc.add_paragraph(str(val))

                        doc_io = BytesIO()
                        doc.save(doc_io)
                        doc_io.seek(0)

                        st.download_button(
                            label="📥 Download Court-Ready Packet (.docx)",
                            data=doc_io,
                            file_name="Legal_Intake_Packet.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("⚠️ Please provide input data.")

                       
                   
                      
                          
