from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import os,base64
import pandas as pd
import time, datetime
from PyPDF2 import PdfReader
import google.generativeai as genai
import pymysql
import re,pickle
os.getenv("API_Key")
genai.configure(api_key=os.getenv("API_Key"))

connection = pymysql.connect(host='localhost', user='root', password='')
cursor = connection.cursor()

def insert_data(timestamp, name, email, pdf, pred, job_d, percent_m):
    DB_table_name = 'applicants_data'
    insert_sql = "insert into " + DB_table_name + """
    values (%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (
    timestamp,name, email, pdf, pred, job_d, percent_m)
    cursor.execute(insert_sql, rec_values)
    connection.commit()

clf = pickle.load(open('clf.pkl', 'rb'))
tfidf = pickle.load(open('tfidf.pkl', 'rb'))

def get_gemini_response(input, pdf_content, prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([input, pdf_content, prompt])
    return response.text

def pdf_setup(uploaded_file):
    if uploaded_file is not None:
        reader = PdfReader(uploaded_file)
        text = ''
        for page in reader.pages:
            text += str(page.extract_text())
        return text
    else:
        st.write("Please upload a PDF file to proceed.")
    
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

if 'show_button' not in st.session_state:
    st.session_state.show_button = True
def toggle_button():
    if uploaded_file is not None and job_d != "" :
        st.session_state.show_button = not st.session_state.show_button
        insert_data(timestamp, name, email, pdf_name, pred, job_d, percent)
    else:
        st.write("Please upload both Resume and Job Description to proceed.")

if 'login_button' not in st.session_state:
    st.session_state.login_button = True
def login(user,pswd):
    if user == 'TeamB3' and pswd == '75A1A509':
        st.session_state.login_button = not st.session_state.login_button

def prediction(txt):
    input_features = tfidf.transform(txt)
    prediction_id = clf.predict(input_features)[0]
    category_mapping = {
            15: "Java Developer",
            23: "Testing",
            8: "DevOps Engineer",
            20: "Python Developer",
            24: "Web Designing",
            12: "HR",
            13: "Hadoop",
            3: "Blockchain",
            10: "ETL Developer",
            18: "Operations Manager",
            6: "Data Science",
            22: "Sales",
            16: "Mechanical Engineer",
            1: "Arts",
            7: "Database",
            11: "Electrical Engineering",
            14: "Health and fitness",
            19: "PMO",
            4: "Business Analyst",
            9: "DotNet Developer",
            2: "Automation Testing",
            17: "Network Security Engineer",
            21: "SAP Developer",
            5: "Civil Engineer",
            0: "Advocate",
        }
    return category_mapping.get(prediction_id, "Unknown")

def percent_match(content,job_d):
    pmprompt="""You are an skilled ATS (Applicant Tracking System) scanner with a deep understanding of ATS functionality,
            your task is to evaluate the resume against the provided job description.
            Give me the percentage of match if the resume matches the job description.
            If the resume doesn't match the job description then the output should be 0%.
            The output should only contain percentage number."""
    percents=[]
    for i in range(0,3):
        per=get_gemini_response(pmprompt,content,job_d)
        percents.append(per)
    percents.sort(reverse=True)
    return percents[0]

def download_report(df, filename, text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

def resume_display(pdf):
    if pdf!="":
        rpath="./UR/"+pdf
        show_pdf(rpath)

# Create the DB
db_sql = """CREATE DATABASE IF NOT EXISTS Resume_Analyzer;"""
cursor.execute(db_sql)
connection.select_db("resume_analyzer")
# Create table
DB_table_name = 'applicants_data'
table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                (Timestamp VARCHAR(50) NOT NULL,
                 Name VARCHAR(50) NOT NULL,
                 Email VARCHAR(50) NOT NULL,
                 Pdf VARCHAR(300) NOT NULL,
                 Predicted_Field VARCHAR(25) NOT NULL,
                 Job_Description VARCHAR(20000) NOT NULL,
                 Percentage_Match VARCHAR(4) NOT NULL,
                 PRIMARY KEY (Timestamp));
                """
cursor.execute(table_sql)
st.set_page_config(page_title="Resume Analyzer")
st.title("Resume Analyser")
st.sidebar.markdown("# Choose User")
activities = ["Normal User", "Admin"]
choice = st.sidebar.selectbox("Choose among the given options:", activities)
if choice == 'Normal User':
    st.session_state.login_button = True
    job_d = st.text_area("Job Description: ", key="input",height=200)
    uploaded_file = st.file_uploader("Upload your Resume(PDF)...", type=["pdf"])
    if uploaded_file is not None:
        pdf_content = pdf_setup(uploaded_file)
        pdf_txt=[pdf_content]
        path = './UR/' + uploaded_file.name
        pdf_name=uploaded_file.name
        if st.session_state.show_button:
            with open(path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            show_pdf(path)
            npromt="""You are an skilled ATS (Applicant Tracking System) scanner with a deep understanding of ATS functionality,
            only display the full name of the applicant."""
            name=get_gemini_response(npromt,pdf_content,"")
            mailp=re.compile(r'[a-zA-Z0-9-\.]+@[a-zA-Z-\.]*\.(com|edu|net)')
            char=mailp.finditer(pdf_content)
            for c in char:
                email=c.group(0)
            percent=percent_match(pdf_content,job_d)
            pred = prediction(pdf_txt)
            ts = time.time()
            cur_date = datetime.datetime.fromtimestamp(ts).strftime('%d-%m-%Y')
            cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
            timestamp = str(cur_date + ' ' + cur_time)
    if st.session_state.show_button:
        st.button('Submit', on_click=toggle_button)
    else:
        col1, col2, col3, col4 = st.columns([0.55,0.75,0.9,0.3])
        with col1:
            change = st.button("Change Resume")
        with col2:
            submit1 = st.button("Tell Me About the Resume")
        with col3:
            submit2 = st.button("How Can I Improvise my Skills")
        col1, col2, col3 = st.columns([1,1.25,2])
        with col1:
            submit3 = st.button("Percentage match")
        with col2:
            submit4 = st.button("Resume Writing Tips")
        col1,col2 = st.columns([2,1])
        with col1:
            input_promp = st.text_input("Query",placeholder="Queries: Feel Free to Ask here",label_visibility="collapsed")
        with col2:
            submit5 = st.button("Answer My Query")
        prompts={
        1:"""You are an experienced Technical Human Resource Manager,
        your task is to review the provided resume against the job description.
        Please share your professional evaluation on whether the candidate's profile aligns with the role.
        Highlight the name, strengths and weaknesses of the applicant in relation to the specified job requirements.""",

        2:"""You are an experienced Technical Human Resource Manager,
        your role is to scrutinize the resume in light of the job description provided. 
        Share your insights on the candidate's suitability for the role from an HR perspective. 
        Additionally, offer advice on enhancing the candidate's skills and identify areas where improvement is needed.""",

        3:"""You are an skilled ATS (Applicant Tracking System) scanner with a deep understanding of data science and ATS functionality,
        your task is to evaluate the resume against the provided job description.
        Give me the percentage of match if the resume matches the job description.
        First the output should come as percentage and then keywords missing and last final thoughts.""",

        4:"""Can you recommend some best youtube videos on resume writing tips.""",
        }
        if change:
            st.session_state.show_button = True
            st.rerun()
        elif submit1:
            if uploaded_file is not None:
                response = get_gemini_response(prompts.get(1, " "), pdf_content, job_d)
                st.subheader("About Your Resume")
                st.write(response)
            else:
                st.write("Please upload a PDF file to proceed.")
        elif submit2:
            if uploaded_file is not None:
                response = get_gemini_response(prompts.get(2, " "), pdf_content, job_d)
                st.subheader("Ways To Improvise Your Skills")
                st.write(response)
            else:
                st.write("Please upload a PDF file to proceed.")
        elif submit3:
            if uploaded_file is not None:
                response = get_gemini_response(prompts.get(3, " "), pdf_content, job_d)
                st.subheader("Percentage Match")
                st.write(response)
            else:
                st.write("Please upload a PDF file to proceed.")
        elif submit4:
            if uploaded_file is not None:
                response = get_gemini_response(prompts.get(4, " "), pdf_content, job_d)
                st.subheader("Recommended Videos")
                st.write(response)
            else:
                st.write("Please upload a PDF file to proceed.")
        elif submit5:
            if uploaded_file is not None:
                response = get_gemini_response(input_promp, pdf_content, job_d)
                st.subheader("The Response is")
                st.write(response)
            else:
                st.write("Please upload a PDF file to proceed.")
else:
    st.session_state.show_button = True
    if st.session_state.login_button:
        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        st.button('Login',on_click=login(ad_user,ad_password))
    else:
        st.success("Welcome ADMIN")
        # Display Data
        cursor.execute('''SELECT * FROM applicants_data''')
        data = cursor.fetchall()
        st.header("**Applicant's Data**")
        df = pd.DataFrame(data, columns=['Timestamp', 'Name', 'Email', 'Resume','Predicted Field', 
                                            'Job Description', 'Match Percentage'])
        st.dataframe(df)
        st.markdown(download_report(df, 'Applicants_Data.csv', 'Download Report'), unsafe_allow_html=True)
        cursor.execute("SELECT DISTINCT pdf FROM applicants_data")
        pdf_v = cursor.fetchall()
        pdf_options = [item[0] for item in pdf_v]
        pdf=st.selectbox("Resume", pdf_options, index=None, placeholder="Choose an Resume", key='pdf')
        if st.button('Display Resume'):
            resume_display(pdf)
        if st.button("Logout"):
            st.session_state.login_button = True
            st.rerun()