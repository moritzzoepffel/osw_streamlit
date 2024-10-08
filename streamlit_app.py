import os
import streamlit as st
import pandas as pd
import requests
from PIL import Image
import openai

from streamlit_ace import st_ace

# Your OpenAI API Key
openai.api_key = "YOUR OPENAPI KEY"


# Routes
PAGES = ["Upload", "View Data", "Image Evaluation", "Trend Analysis"]

# Authentication
def check_password(password):
    if password == "YOUR PASSWORD":
        return True
    return False

def main():
    password = st.sidebar.text_input("Password", type='password')
    if check_password(password):
        option = st.sidebar.selectbox("Select Page", PAGES)
        if option == "Upload":
            df = upload_excel_file()
            if df is not None:
                process_uploaded_file(df)
        elif option == "View Data":
            display_data()
        elif option == "Image Evaluation":
            evaluate_images()
        else:
            st.write("Trend Analysis page to be populated")
    else:
        st.sidebar.warning("Please enter valid password")

# Handlers
@st.cache
def download_image(url):
    try:
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))
        image.save(os.path.join("tmp", url.split("/")[-1]))
    except Exception as e:
        print(f"Error: {e}")
        return "No data"
    return os.path.join("tmp", url.split("/")[-1])

def upload_excel_file():
    uploaded_file = st.sidebar.file_uploader("Choose a file")
    if uploaded_file is not None:
        dataframe = pd.read_excel(uploaded_file)
        return dataframe
    return None

def process_uploaded_file(df):
    st.cache(df)
    st.write(df)

def display_data():
    # Assumes that data is stored as df.csv
    df = pd.read_csv('df.csv')
    st.write(df)

def evaluate_images(df):
    # Iterate over the dataframe
    for index, row in df.iterrows():
        # Download the image and attach the filepath to dataframe
        image = download_image(row['Image'])
        df.at[index, 'Image_filepath'] = image

        # Describe the image and attach the description to dataframe
        result = openai.ImageCompletion.create(image, max_tokens=60)
        df.at[index, 'Image_description'] = result.choices[0].text.strip()

    # Save updated dataframe
    df.to_csv('df.csv', index=False)

if __name__ == "__main__":
    main()
