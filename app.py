import gradio as gr
from PyPDF2 import PdfReader
import requests
import json
import logging
import os
import zipfile
import tempfile

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Define the API endpoint and key
AZURE_OPENAI_URL = "https://minihackathon12.openai.azure.com/openai/deployments/gpt-4/chat/completions?api-version=2024-08-01-preview"
AZURE_API_KEY = "9ca8869e84af49ec92f9437576f63fa6"  # Replace with your actual API key

# Store the participant data globally for HR view
uploaded_resumes = []

def chat_completion_request(messages):
    # Payload structure for Azure OpenAI API
    payload = {
        "messages": messages,
        "max_tokens": 4000,
        "temperature": 0.7,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_API_KEY  # Azure OpenAI requires this header for authentication
    }

    # Send POST request to Azure OpenAI API
    response = requests.post(AZURE_OPENAI_URL, headers=headers, data=json.dumps(payload))

    # Handle response
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"API Request failed: {response.status_code}, {response.text}")
        return {"error": response.status_code, "message": response.text}

from docx import Document  # Import python-docx for reading .docx files

def participant_upload(files):
    global uploaded_resumes  # Store the resumes globally for HR view
    try:
        logging.debug("Starting participant resume upload.")
        for file in files:
            logging.debug(f"Processing file: {file.name}")

            # Store file name and content
            file_extension = os.path.splitext(file.name)[-1].lower()

            candidate_text = ""
            if file_extension == '.pdf':
                # Handle PDF files using PyPDF2
                pdf_reader = PdfReader(file)
                for page in pdf_reader.pages:
                    candidate_text += page.extract_text() if page.extract_text() else ""

            elif file_extension == '.docx':
                # Handle DOCX files using python-docx
                doc = Document(file)
                for paragraph in doc.paragraphs:
                    candidate_text += paragraph.text + "\n"

            else:
                logging.error(f"Unsupported file type: {file_extension}")
                continue

            if candidate_text.strip():  # Ensure that some text was extracted
                # Save the candidate information for HR analysis
                uploaded_resumes.append({
                    'name': file.name,
                    'text': candidate_text,
                    'file': file  # Store the file for future download
                })

        return "Resumes uploaded successfully!" if uploaded_resumes else "No valid resumes uploaded."

    except Exception as e:
        logging.exception("An exception occurred during resume upload.")
        return f"An error occurred: {str(e)}"


def grade_candidate(response_content, essential_skills):
    """
    This function assigns a grade based on how well the response content matches the job description,
    prioritizing essential skills.
    """
    # Normalize the text to lowercase for easier keyword search
    response_content = response_content.lower()

    # Initialize a score for the job description match
    total_score = 0
    essential_skill_penalty = 0

    # Check for essential skills (like engineering) and add penalties if missing
    for skill in essential_skills:
        if skill.lower() not in response_content:
            essential_skill_penalty += 2  # Heavy penalty for missing essential skills

    # Check for secondary skills (e.g., leadership) and give partial scores
    if "meets the educational requirement" in response_content or "satisfies the educational requirement" in response_content:
        total_score += 1

    if "relevant experience" in response_content or "aligned with job requirements" in response_content:
        total_score += 1

    if "strong fit" in response_content or "good match" in response_content:
        total_score += 1

    # Adjust final score based on essential skill penalty
    total_score = max(0, total_score - essential_skill_penalty)

    # Assign grades based on final score
    if total_score >= 3:
        return "5"  # Excellent match
    elif total_score == 2:
        return "4"  # Good match
    elif total_score == 1:
        return "3"  # Partial match
    elif total_score == 0:
        return "2"  # Minimal match
    else:
        return "1"  # Poor or no match


def evaluate_candidates(job_description, essential_skills, min_grade):
    global uploaded_resumes
    results = []
    matching_candidates = []  # Store candidates that match the criteria

    # Define grade hierarchy for comparison
    grade_hierarchy = ["5", "4", "3", "2", "1"]

    try:
        logging.debug("Starting candidate evaluation.")
        for candidate in uploaded_resumes:
            candidate_text = candidate['text']
            logging.debug(f"Evaluating candidate: {candidate['name']}")

            # Prepare messages for the Azure OpenAI model
            messages = [
                {
                    "role": "system",
                    "content": "You are an assistant that helps employers evaluate candidates based on their resume and job requirements."
                },
                {
                    "role": "user",
                    "content": f"""Job Description: {job_description}
Candidate Resume Text: {candidate_text}

Does this candidate fit the criteria? Please provide a detailed analysis."""
                }
            ]

            # Call the Azure OpenAI model
            response = chat_completion_request(messages)

            logging.debug(f"Received response: {response}")

            # Extract the assistant's reply from the response
            if 'choices' in response and len(response['choices']) > 0:
                assistant_reply = response['choices'][0]['message']['content']

                # Assign a grade based on the analysis and match criteria
                grade = grade_candidate(assistant_reply, essential_skills)

                structured_output = f"""
                **General Info:**
                Candidate: {candidate['name']}
                
                **Experience:**
                {assistant_reply}

                **Grade:**
                {grade}
                """

                # Check if the grade is equal to or higher than the minimum grade specified by HR
                if grade_hierarchy.index(grade) <= grade_hierarchy.index(min_grade):
                    matching_candidates.append(candidate['file'])  # Add the matching candidate's file
                    results.append(structured_output)
            else:
                error_message = response.get('message', 'Unknown error')
                logging.error(f"Error processing {candidate['name']}: {error_message}")
                results.append(f"Error processing {candidate['name']}: {error_message}")
        
        # Combine results for HR view
        evaluation_result = "\n\n---\n\n".join(results)

        # Generate a zip file for downloading matching candidates' resumes
        if matching_candidates:
            zip_filename = os.path.join(tempfile.gettempdir(), 'matching_resumes.zip')
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for candidate in matching_candidates:
                    zipf.write(candidate.name, os.path.basename(candidate.name))

            return evaluation_result, zip_filename
        else:
            return f"{evaluation_result}\n\nNo matching candidates found for the given criteria.", None
    
    except Exception as e:
        logging.exception("An exception occurred during candidate evaluation.")
        return f"An error occurred: {str(e)}", None


# Interface for participant upload
participant_view = gr.Interface(
    fn=participant_upload,
    inputs=[gr.File(file_types=[".pdf", ".docx"], label="Upload Candidate Resumes (PDF or DOCX)", file_count="multiple")],
    outputs="text",
    title="Participant Resume Upload",
    description="Upload your resume here (PDF or DOCX).",
    allow_flagging="never"  # Disable flagging and remove flag buttons
)

# Interface for HR evaluation with slider for minimum grade
hr_view = gr.Interface(
    fn=evaluate_candidates,
    inputs=[
        gr.Textbox(lines=5, placeholder="Enter Job Description", label="Job Description"),
        gr.Textbox(lines=2, placeholder="Enter Essential Skills (comma-separated)", label="Essential Skills"),
        gr.Radio(choices=["5", "4", "3", "2", "1"], value="3", label="Minimum Grade")
    ],
    outputs=["text", "file"],  # Output both the analysis and the zip file
    title="HR Candidate Evaluation",
    description="Evaluate candidates based on job criteria and set a minimum grade for resumes to download.",
    allow_flagging="never"  # Disable flagging and remove flag buttons
)

# Launch both views
gr.TabbedInterface([participant_view, hr_view], ["Participant View", "HR View"]).launch()
