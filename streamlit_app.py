import streamlit as st
import pandas as pd
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
import base64
import utils

# Constants
PAGES = [
    "Anleitung",
    "Daten hochladen",
    "Produkte Anzeigen",
    "Beschreibungen generieren",
    "Trendanalyse",
    "Chat Bot",
    "Dokumente verbinden",
    "Daten herunterladen",
]

# change favicon and title
st.set_page_config(
    page_title="Oswald KI App",
    page_icon="https://oswald-online.de/wp-content/uploads/2023/10/Oswald_Logo_rot_schwarz.png",
)


def check_password(password):
    """Check if the provided password matches the stored password."""
    return password == st.secrets["password"]


@st.cache_data
def convert_df(df):
    """Convert a DataFrame to CSV format."""
    return df.to_csv().encode("utf-8")


# Data Handling Functions
def upload_excel_file(uploaded_file):
    """Upload and process an Excel file."""
    try:
        dataframe = pd.read_excel(uploaded_file)
        dataframe["Beschreibung"] = ""
        dataframe["Jahr"] = (
            dataframe["Jahr"].apply(lambda x: int(str(x).replace(",", ""))).astype(int)
        )
        return dataframe
    except Exception as e:
        st.error(f"Error uploading file: {e}")
        return None


# UI Components
def display_sidebar():
    """Display the sidebar for the Streamlit app."""
    st.sidebar.title("Oswald KI App")
    st.session_state.password = st.sidebar.text_input("Password", type="password")


def handle_file_upload():
    """Handle file upload and store the uploaded DataFrame in session state."""
    st.write("## Daten hochladen")
    uploaded_file = st.file_uploader("Wähle eine Datei")
    if uploaded_file is not None:
        df = upload_excel_file(uploaded_file)
        if df is not None:
            st.session_state.uploaded_df = df
    if st.button("Hochgeladene Daten löschen"):
        st.session_state.uploaded_df = None


def display_page():
    """Display the selected page based on user input from the sidebar."""
    option = st.sidebar.selectbox("Seite auswählen", PAGES)
    if option == "Anleitung":
        show_instructions()
    elif option == "Daten hochladen":
        handle_file_upload()
    elif option == "Beschreibungen generieren":
        if st.session_state.uploaded_df is not None:
            evaluate_images(st.session_state.uploaded_df)
        else:
            st.write("Bisher keine Daten hochgeladen")
    elif option == "Produkte Anzeigen":
        if st.session_state.uploaded_df is not None:
            display_data(st.session_state.uploaded_df)
        else:
            st.write("Bisher keine Daten hochgeladen")
    elif option == "Trendanalyse":
        if st.session_state.uploaded_df is not None:
            trend_analysis(st.session_state.uploaded_df)
        else:
            st.write("Bisher keine Daten hochgeladen")
    elif option == "Chat Bot":
        chat_bot()
    elif option == "Dokumente verbinden":
        connect_documents()
    else:
        if st.session_state.uploaded_df is not None:
            download_data()
        else:
            st.write("Bisher keine Daten hochgeladen")


def show_instructions():
    """Display instructions on how to use the Streamlit app."""
    st.image(
        "https://oswald-online.de/wp-content/uploads/2023/10/Oswald_Logo_rot_schwarz.png",
        width=200,
    )
    # row 1
    st.write("# Oswald KI App")
    st.write("## Anleitung")
    st.write(
        "Willkommen zur Oswald KI App. Hier können Sie Daten hochladen, Produkte anzeigen, Beschreibungen generieren, eine Trendanalyse durchführen, einen Chat Bot verwenden und Dokumente verbinden."
    )

    st.write("### Schritte")
    col1, col2 = st.columns(2)
    with col1:
        st.write(
            "1. Generieren Sie einen API Key und geben Sie diesen in der Sidebar ein. Speichern Sie diesen API Key gut ab, da sie ihn nur einmal anzeigen lassen können"
        )
    with col2:
        st.link_button(
            "API Key generieren", "https://platform.openai.com/account/api-keys"
        )
    st.write(
        "2. Wählen Sie auf der linken Seite in der Sidebar eine der Kategorien aus"
    )
    st.write("3. Laden Sie den Datensatz von Temu hoch")
    st.write(
        "4. Lassen Sie sich mithilfe von KI Beschreibungen für die Produkte des Datensatzes erzeugen oder eine Trendanalyse durchführen"
    )


def display_data(df):
    """Display the uploaded data and some key metrics."""
    st.write("## Datensatz")
    st.write("### Informationen zum hochgeladenen Datensatz")
    cols = st.columns(4)
    with cols[0]:
        st.metric("Kategorien", df["Kategorie"].nunique())
    with cols[1]:
        st.metric("Anzahl von Produkten", len(df))
    with cols[2]:
        st.metric("Anzahl von Unique Produkten", df["Produktname"].nunique())
    with cols[3]:
        st.metric("Anzahl von Beschreibungen", len(df[df["Beschreibung"] != ""]))
    with cols[0]:
        st.metric(
            "Avg Preis",
            f"{format(df["Produktpreis"].mean(), ".2f")} €",
        )
    with cols[1]:
        st.metric(
            "Avg Ranking",
            f"{format(df["Durchschnittliche Produktbewertung (1=schlechteste Note, 5=beste Note)"].mean(), ".2f")}",
        )
    with cols[2]:
        st.metric(
            "Avg Abverkaufsmenge",
            f"{format(df["Abverkaufsmenge"].mean(), ".2f")}",
        )
    st.divider()
    show_products(df)


def show_products(df):
    """Display products based on the selected category."""
    if df is not None:
        category = st.selectbox(
            "Kategorie",
            ["Alle"] + list(df["Kategorie"].unique()),
        )
        if category == "Alle":
            display_all_categories(df)
        else:
            display_category(df, category)
    else:
        st.write("Bisher keine Daten hochgeladen")


def display_all_categories(df):
    """Display all categories and their top products."""
    categories = df["Kategorie"].unique()
    for category in categories:
        st.write(f"### {category} Top 3")
        category_df = df[df["Kategorie"] == category]
        top_ranked = category_df[
            category_df["Ranking in der Kategorie"].isin([1, 2, 3])
        ]
        display_images(top_ranked)
    st.write(df)


def display_category(df, category):
    """Display top products for a specific category."""
    category_df = df[df["Kategorie"] == category]
    num = st.slider("Wie viele Produkte sollen angezeigt werden?", 1, len(category_df), 10)
    top_ranked = category_df[category_df["Ranking in der Kategorie"].isin(range(1, num+1))]
    st.write(f"### {category} Top {num}")
    display_images(top_ranked)
    st.write(top_ranked)


def display_images(df):
    """Display images of products in a DataFrame."""
    cols = st.columns(3)
    for i, row in df.iterrows():
        with cols[i % 3]:
            st.markdown(
                f"""<a href="{row['Produkt URL']}" target="_blank">![{row['Produktname']}]({row['Produktbild URL']})</a>""",
                unsafe_allow_html=True,
            )
            st.write(f"**{row['Produktname']}**")


# Main Logic
def main():
    """Main function to run the Streamlit app."""
    st.logo(
        "https://oswald-online.de/wp-content/uploads/2023/10/Oswald_Logo_rot_schwarz.png"
    )
    if "uploaded_df" not in st.session_state:
        st.session_state.uploaded_df = None
    display_sidebar()
    if check_password(st.session_state.password):
        # input for api key
        api_key_input = st.sidebar.text_input("API Key", type="password")
        if st.sidebar.button("API Key sichern"):
            if api_key_input.startswith("sk-"):
                st.session_state.api_key = api_key_input
            else:
                st.session_state.api_key = None
                st.sidebar.warning("Please enter a valid API Key")
        display_page()
    else:
        st.sidebar.warning("Please enter valid password")


# Additional Functionalities
def evaluate_images(df):
    """Evaluate images and generate descriptions using OpenAI."""
    st.write("## Beschreibungen generieren")
    if "api_key" not in st.session_state or st.session_state.api_key is None:
        st.warning("Bitte zuerst API Key eingeben")
        return
    client = OpenAI(api_key=st.session_state.api_key)

    st.write(
        "Hier können Beschreibungen für die hochgeladenen Produkte generiert werden."
    )
    if st.button("Beschreibungen generieren"):
        progress_text = "Generating descriptions for images..."
        my_bar = st.progress(0, progress_text)
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(
                    generate_description, client, row["Produktbild URL"], index
                )
                for index, row in df.iterrows()
                if row["Ranking in der Kategorie"] in range(1, 6)
            ]
            for i, future in enumerate(futures):
                st.session_state.uploaded_df.at[future.result()[0], "Beschreibung"] = (
                    future.result()[1]
                )
                my_bar.progress((i + 1) / len(futures))
        my_bar.progress(1.0)
        st.success("Beschreibungen wurden generiert")
        st.rerun()
    st.write("### Beschreibungen der Top 20 Produkte")
    if st.button("Beschreibungen anzeigen"):
        cols = st.columns(3)
        products_with_descriptions = df[df["Beschreibung"] != ""]
        for i, row in products_with_descriptions.iterrows():
            with cols[i % 3]:
                st.markdown(
                    f"""<a href="{row['Produkt URL']}" target="_blank">![{row['Produktname']}]({row['Produktbild URL']})</a>""",
                    unsafe_allow_html=True,
                )
                st.write(f"**{row['Produktname']}**")
                st.write(row["Beschreibung"])


def generate_description(client, img_url, index):
    """Generate a description for an image using OpenAI."""
    messages = [
        {
            "role": "system",
            "content": "Du bist ein nützlicher Assistent, der dabei hilft Produkte und deren Verpackungen zu beschreiben. Bei der Beschreibung ist zu unterscheiden zwischen der Beschreibung der Verpackung und dem Produkt selbst. Für die Beschreibung der Verpackung sind folgende Dimensionen wichtig: Form der Verpackung, Farbe, ggf. Muster/Bildelemente, die auf der Verpackung (und nicht auf dem Produkt) zu sehen sind, Anzahl der Produkte pro Verpackung. Für die Beschreibung des Produkts sind folgende Dimensionen wichtig: Form des Produkts, Farbe, ggf. Muster/Bildelemente des Produkts, andere besondere Details des Produkts (z.B. Perlen etc.) können genannt werden. Bitte bleibe sachlich und beschreibe nur das, was auf dem Bild zu sehen ist.",
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Was ist auf dem Bild zu sehen?"},
                {"type": "image_url", "image_url": {"url": img_url}},
            ],
        },
    ]
    completion = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return index, completion.choices[0].message.content, img_url


def trend_analysis(df):
    """Perform trend analysis on the uploaded data."""
    st.write("## Trendanalyse")
    if "api_key" not in st.session_state or st.session_state.api_key is None:
        st.warning("Bitte zuerst API Key eingeben")
        return
    client = OpenAI(api_key=st.session_state.api_key)

    st.write(
        "Hier kann eine Trendanalyse der hochgeladenen Produkte durchgeführt werden."
    )
    if "trend_analysis" in st.session_state:
        st.write("Trendanalyse wurde bereits durchgeführt")
        cat = st.selectbox(
            "Kategorie",
            ["Alle"] + list(st.session_state.trend_analysis["Kategorie"].unique()),
        )
        if cat == "Alle":
            for i, row in st.session_state.trend_analysis.iterrows():
                st.write(f"### {row['Kategorie']}")
                st.write(row["Trends"])
                st.divider()
        else:
            st.write(f"### {cat}")
            st.write(
                st.session_state.trend_analysis[
                    st.session_state.trend_analysis["Kategorie"] == cat
                ]["Trends"].values[0]
            )
    elif df is None:
        st.write("Bitte zuerst Daten hochladen")
    else:
        if st.button("Analyse starten"):
            trend_analysis = pd.DataFrame()
            st.success("Analyse wird durchgeführt")
            progress_text = "Analysiere Trends..."
            my_bar = st.progress(0, progress_text)
            i = 0
            df_trend = df[df["Ranking in der Kategorie"].isin(range(1, 6))]
            trends_per_category = {
                category: df_trend[df_trend["Kategorie"] == category]
                for category in df_trend["Kategorie"].unique()
            }
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [
                    executor.submit(generate_trend, client, category, category_df)
                    for category, category_df in trends_per_category.items()
                ]
                for future in futures:
                    i += 1
                    my_bar.progress(i / len(futures))
                    trend_analysis = pd.concat(
                        [
                            trend_analysis,
                            pd.DataFrame(
                                {
                                    "Kategorie": [future.result()[0]],
                                    "Trends": [future.result()[1]],
                                }
                            ),
                        ]
                    )
            my_bar.progress(1.0)
            st.session_state.trend_analysis = trend_analysis
            st.success("Analyse abgeschlossen")
            st.rerun()


def generate_trend(client, category, category_df):
    """Generate trends for a category using OpenAI."""
    messages = [
        {
            "role": "system",
            "content": f"Stellen Sie sich vor, Sie sind Trendscout und auf der Suche nach aktuellen Markttrends, um Produktinnovationen voranzutreiben. Als Datengrundlage erhalten Sie Informationen über die Top-Produkte auf temu. Trends sind für mich Eigenschaften, die in vielen (d.h. mindestens zwei) der meistverkauften Produkte vorkommen. Um dies zu erkennen, konzentrieren Sie sich am besten auf die Spalten Produktname und Beschreibung im hochgeladenen Datensatz. Bitte analysieren Sie den Trend anhand der folgenden Dimensionen für die Kategorie {category} Text: Produktname, Produktkategorie/-art (was für ein Produkt ist es), Zielgruppe, Benefits; Bild: Farbpalette, Muster, Bildelemente; Form: Produktabmessungen, Produktgewicht, Silhouette/ Form; Komponente: Textilkomponente oder andere Komponente; Verpackung: Verpackungsabmessungen, Anzahl der Einheiten pro Verpackung, Verpackungskomponenten; Verkauf: Abverkaufsdaten, Listung, Preisanalyse. Bitte geben Sie DREI Trends für jede Dimension an. Bitte untermauern Sie diese Trends mit so vielen konkreten Beispielen wie möglich. Bitte arbeiten Sie nur mit den Produkten, die ich hochgeladen habe.",
        },
        {
            "role": "user",
            "content": category_df["Beschreibung"].to_json(),
        },
    ]
    completion = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return category, completion.choices[0].message.content


def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
    

def chat_bot():
    """Chat bot functionality using OpenAI."""
    st.write("## Chat Bot")
    if "api_key" not in st.session_state or st.session_state.api_key is None:
        st.warning("Bitte zuerst API Key eingeben")
        return
    if "chat" not in st.session_state:
        st.session_state.chat = []

    messages = st.container(height=300)
    uploaded_image = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])

    if uploaded_image is not None:
        base64_image = encode_image(uploaded_image)
        input2 = "Beschreibe das Produkt auf dem Bild"
    else:
        input = st.chat_input("Nachricht eingegeben...")

    if input2:
        client = OpenAI(api_key=st.session_state.api_key)
        messages_to_send = [
            {
                "role": "system",
                "content": "Du bist ein nützlicher Assistent, der dabei hilft Produkte und deren Verpackungen zu beschreiben. Bei der Beschreibung ist zu unterscheiden zwischen der Beschreibung der Verpackung und dem Produkt selbst. Für die Beschreibung der Verpackung sind folgende Dimensionen wichtig: Form der Verpackung, Farbe, ggf. Muster/Bildelemente, die auf der Verpackung (und nicht auf dem Produkt) zu sehen sind, Anzahl der Produkte pro Verpackung. Für die Beschreibung des Produkts sind folgende Dimensionen wichtig: Form des Produkts, Farbe, ggf. Muster/Bildelemente des Produkts, andere besondere Details des Produkts (z.B. Perlen etc.) können genannt werden. Bitte bleibe sachlich und beschreibe nur das, was auf dem Bild zu sehen ist.",
            },
            {
                "role": "user",
                "content": [
                    {
                      "type": "text",
                      "text": input,
                    },
                    {
                      "type": "image_url",
                      "image_url": {
                        "url":  f"data:image/jpeg;base64,{base64_image}"
                      },
                    },
                  ],
            },
        ]
        completion = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages_to_send
        )
        st.session_state.chat.append(
            {"role": "user", "content": input, "timestamp": "now"}
        )
        st.session_state.chat.append(
            {"role": "system", "content": completion.choices[0].message.content}
        )

    if input:
        client = OpenAI(api_key=st.session_state.api_key)
        messages_to_send = [
            {
                "role": "system",
                "content": "Du bist ein nützlicher Assistent, der dabei hilft Produkte und deren Verpackungen zu beschreiben. Bei der Beschreibung ist zu unterscheiden zwischen der Beschreibung der Verpackung und dem Produkt selbst. Für die Beschreibung der Verpackung sind folgende Dimensionen wichtig: Form der Verpackung, Farbe, ggf. Muster/Bildelemente, die auf der Verpackung (und nicht auf dem Produkt) zu sehen sind, Anzahl der Produkte pro Verpackung. Für die Beschreibung des Produkts sind folgende Dimensionen wichtig: Form des Produkts, Farbe, ggf. Muster/Bildelemente des Produkts, andere besondere Details des Produkts (z.B. Perlen etc.) können genannt werden. Bitte bleibe sachlich und beschreibe nur das, was auf dem Bild zu sehen ist.",
            },
            {
                "role": "user",
                "content": [
                    {
                      "type": "text",
                      "text": input,
                    },
                  ],
            },
        ]
        completion = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages_to_send
        )
        st.session_state.chat.append(
            {"role": "user", "content": input, "timestamp": "now"}
        )
        st.session_state.chat.append(
            {"role": "system", "content": completion.choices[0].message.content}
        )

    for message in st.session_state.chat:
        if message["role"] == "system":
            messages.write(message["content"], unsafe_allow_html=True)
        else:
            messages.write(f"**Du:** {message['content']}")

    if uploaded_image is not None:
        uploaded_image.close()


def connect_documents():
    """Functionality to connect documents."""
    st.write("## Dokumente verbinden")
    st.write("Hier können Dokumente miteinander verbunden werden.")

    # Here we can upload 7 Documents which are getting stiched afterwards
    document_names = [
        "Material Allgemein",
        "Material ME Eigenschaften",
        "Materialkomponenten",
        "Textilkomponenten",
        "Verpackung",
        "Zusatzinformationen NEU 2",
        "Zusatzinformationen",
    ]

    st.session_state.uploaded_files = []
    cols = st.columns(3)
    for i in range(7):
        with cols[i % 3]:
            uploaded_file = st.file_uploader(f"{document_names[i]}", type=["xml"])
            if uploaded_file is not None:
                st.session_state.uploaded_files.append(uploaded_file)

    if len(st.session_state.uploaded_files) == 7:
        st.success("Alle Dokumente wurden hochgeladen")
        if st.button("Dokumente verbinden"):
            st.write("Dokumente werden verbunden")
            stitched_doc = stitch_documents(st.session_state.uploaded_files)


def stitch_documents(doc_list):
    # First of all we need to read the content of the uploaded files
    document_content = []
    for index, doc in enumerate(doc_list):
        utils.extract_docs(index, doc)


def download_data():
    st.write("## Daten herunterladen")
    st.write("Fertige Datensets herunterladen")
    csv_data = convert_df(st.session_state.uploaded_df)
    csv_trends = convert_df(st.session_state.trend_analysis) 
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Datensatz als csv herunterladen",
            data=csv_data,
            file_name="data.csv",
            mime="text/csv",
        )
    with col2:
        st.download_button(
            label="Trendanalyse als csv herunterladen",
            data=csv_trends,
            file_name="trends.csv",
            mime="text/csv",
        )  


if __name__ == "__main__":
    main()
