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
    #"Dokumente verbinden",
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
            #trend_analyse_self()
    elif option == "Chat Bot":
        chat_bot()
    #elif option == "Dokumente verbinden":
    #    connect_documents()
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
        "Willkommen zur Oswald KI App. Hier können Sie die XPLN temu Daten hochladen, Produkte anzeigen, Beschreibungen generieren und mit einem Chat-Bot interagieren."
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
    if "api_key" not in st.session_state or st.session_state.api_key is None:
        st.error("Bisher kein API Key eingegeben")
    else:
        st.success("API Key wurde eingegeben")
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
    with st.expander("Informationen anzeigen"):
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
        display_images(top_ranked, True)
    st.write(df)


def display_category(df, category):
    """Display top products for a specific category."""
    category_df = df[df["Kategorie"] == category]
    num = st.slider(
        "Wie viele Produkte sollen angezeigt werden?", 1, len(category_df), 10
    )
    top_ranked = category_df[
        category_df["Ranking in der Kategorie"].isin(range(1, num + 1))
    ]
    st.write(f"### {category} Top {num}")
    with st.expander("Informationen anzeigen"):
        cols = st.columns(3)
        with cols[0]:
            st.metric(
                "Avg Preis",
                f"{format(top_ranked["Produktpreis"].mean(), ".2f")} €",
            )
        with cols[1]:
            st.metric(
                "Avg Ranking",
                f"{format(top_ranked["Durchschnittliche Produktbewertung (1=schlechteste Note, 5=beste Note)"].mean(), ".2f")}",
            )
        with cols[2]:
            st.metric(
                "Avg Abverkaufsmenge",
                f"{format(top_ranked["Abverkaufsmenge"].mean(), ".2f")}",
            )
    st.divider()
    display_images(top_ranked, False)
    st.write(top_ranked)


def display_images(df, cat):
    """Display images of products in a DataFrame."""
    cols = st.columns(3)
    for i, row in df.iterrows():
        with cols[i % 3]:
            st.markdown(
                f"""<a href="{row['Produkt URL']}" target="_blank">![{row['Produktname']}]({row['Produktbild URL']})</a>""",
                unsafe_allow_html=True,
            )
            st.write(f"**{row['Produktname']}**")
            if cat:
                st.metric(label="Preis", value=f"{row['Produktpreis']}€", delta="0,2 €")


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
                st.sidebar.warning("Bitte gültigen API Key eingeben")
        display_page()
    else:
        st.sidebar.warning("Bitte gültiges Passwort eingeben")


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
                if row["Ranking in der Kategorie"] in range(1, 10)
            ]
            for i, future in enumerate(futures):
                st.session_state.uploaded_df.at[future.result()[0], "Beschreibung"] = (
                    future.result()[1]
                )
                my_bar.progress((i + 1) / len(futures))
        my_bar.progress(1.0)
        st.success("Beschreibungen wurden generiert")
        st.rerun()
    st.write("### Beschreibungen der Top 100 Produkte")
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
                with st.expander("Beschreibung"):
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

    st.write("Hallo")

    if "api_key" not in st.session_state or st.session_state.api_key is None:
        st.warning("Bitte zuerst API Key eingeben")
        return
    client = OpenAI(api_key=st.session_state.api_key)

    


    st.write(
        "Hier kann eine Trendanalyse der hochgeladenen Produkte durchgeführt werden."
    )
    if "trend_analysis" in st.session_state:
        st.success("Trendanalyse wurde bereits durchgeführt")
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


def trend_analyse_self():
    st.write("## Trendanalyse")

    if "api_key" not in st.session_state or st.session_state.api_key is None:
        st.warning("Bitte zuerst API Key eingeben")
        return
    client = OpenAI(api_key=st.session_state.api_key)
    
    if "api_key" not in st.session_state or st.session_state.api_key is None:
        st.warning("Bitte zuerst API Key eingeben")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Wie kann ich Dir helfen?"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Get response from OpenAI
        response = openai(client, prompt)

        # Display OpenAI response in chat message container
        st.chat_message("bot").markdown(response)

        # Add OpenAI response to chat history
        st.session_state.messages.append({"role": "bot", "content": response})


def generate_trend(client, category, category_df):
    """Generate trends for a category using OpenAI."""
    messages = [
        {
            "role": "system",
            "content": f"""
                Du bist Theresa, der Trendscout. Bitte führen Sie eine personalisierte Trendanalyse der Produktdaten des Nutzers durch.

                Nach einer Begrüßung befolge die folgenden Schritte, um die vom Nutzer hochgeladenen produktbezogenen Daten zu analysieren und Trends zu identifizieren. 

                # Schritte 

                - Analyse der Produkte ausschließlich basierend auf den bereitgestellten Beschreibungen aus der Kategorie: {category}.
                - Trends in den folgenden Dimensionen identifizieren und beschreiben: Produkt, Bild, Form, Komponente, Verpackung und Verkauf.

                # Trendanalyse-Dimensionen

                1. **Produkt:** Art, Zielgruppe, Benefits
                2. **Bild:** Farbpalette, Muster, Bildelemente
                3. **Form:** Abmessungen, Gewicht, Silhouette/Form
                4. **Komponente:** Textil- oder andere Komponenten
                5. **Verpackung:** Abmessungen, Anzahl der Einheiten, Komponenten
                6. **Verkauf:** Preis, Abverkaufsmenge und Wiederkauf

                Für jede Dimension werden drei Trends identifiziert und mit konkreten Beispielen aus den analysierten Produkten illustriert. Zusätzlich werden drei innovative Produkte hervorgehoben, die sich signifikant von den normalen Produkten der Kategorie unterscheiden.

                # Output Format

                Die Ergebnisse sollten in natürlicher Sprache verfasst und in folgender Struktur präsentiert werden:

                - **Einleitung:** Persönliche Begrüßung und Überblick.
                - **Trendergebnisse:** Drei detaillierte Trendbeschreibungen pro Dimension mit Beispielen.
                - **Innovative Produkte:** Auflistung von drei neuen und sich unterscheidenden Produkten der Kategorie.

                # Beispiele

                **Beispiel:**

                **Einleitung:** "Hallo, willkommen zur Trendanalyse!"

                **Trendergebnisse:**
                - **Produkt:** 
                - Trend 1: [Beschreibung und Beispiele]
                - Trend 2: [Beschreibung und Beispiele]
                - Trend 3: [Beschreibung und Beispiele]

                **Innovative Produkte:**
                - Produkt A: [Beschreibung]
                - Produkt B: [Beschreibung]
                - Produkt C: [Beschreibung]

                # Notes

                - Theresa verwendet keine zusätzlichen Quellen außer den vom Nutzer bereitgestellten Produktbeschreibungen.
                - Alle Trends werden in mindestens drei detaillierten Zeilen beschrieben.
                - Vermeiden Sie es, eigene Recherchen oder Wissen hinzuzufügen.
            """
        },
        {
            "role": "user",
            "content": category_df["Beschreibung"].to_json(),
        },
    ]
    completion = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return category, completion.choices[0].message.content


def openai(client, message: str):
    client = client

    if "assistant_id" not in st.session_state:
        st.session_state.assistant_id = st.secrets["assistant_id"]

    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    message = client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id, role="user", content=message
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=st.session_state.thread_id, assistant_id=st.session_state.assistant_id
    )

    if run.status == "completed":
        return (
            client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
            .data[0]
            .content[0]
            .text.value
        )


def chat_bot():
    """Chat bot functionality using OpenAI."""
    st.write("## Chat Bot")
    if "api_key" not in st.session_state or st.session_state.api_key is None:
        st.warning("Bitte zuerst API Key eingeben")
        return
    if "chat" not in st.session_state:
        st.session_state.chat = []

    option = st.selectbox(
        "Wählen Sie einen Chatbot",
        ("Bild hochladen", "Text zu Bild"),
        )

    if option == "Bild hochladen":
        messages = st.container(height=300)
        uploaded_image = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
    
        if uploaded_image is not None:
            uploaded_image_64 = base64.b64encode(uploaded_image.read()).decode("utf-8")
            chat_input = "Was ist auf dem Bild zu sehen?"
            input = {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Was ist auf dem Bild zu sehen?",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{uploaded_image_64}"},
                    },
                ],
            }
        
        
            client = OpenAI(api_key=st.session_state.api_key)
            messages_to_send = [
                {
                    "role": "system",
                    "content": "Du bist ein nützlicher Assistent, der dabei hilft Produkte und deren Verpackungen zu beschreiben. Bei der Beschreibung ist zu unterscheiden zwischen der Beschreibung der Verpackung und dem Produkt selbst. Für die Beschreibung der Verpackung sind folgende Dimensionen wichtig: Form der Verpackung, Farbe, ggf. Muster/Bildelemente, die auf der Verpackung (und nicht auf dem Produkt) zu sehen sind, Anzahl der Produkte pro Verpackung. Für die Beschreibung des Produkts sind folgende Dimensionen wichtig: Form des Produkts, Farbe, ggf. Muster/Bildelemente des Produkts, andere besondere Details des Produkts (z.B. Perlen etc.) können genannt werden. Bitte bleibe sachlich und beschreibe nur das, was auf dem Bild zu sehen ist.",
                }
            ]
            messages_to_send.append(input)
            completion = client.chat.completions.create(
                model="gpt-4o-mini", messages=messages_to_send
            )
            st.session_state.chat.append(
                {"role": "user", "content": chat_input, "timestamp": "now"}
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
            st.image(uploaded_image, width=200)
    
        if uploaded_image is not None:
            uploaded_image.close()

    if option == "Text zu Bild":
        input = st.text_input("Was wollen Sie für ein Bild generieren?")

        if input:
            client = OpenAI(api_key=st.session_state.api_key)
            response = client.images.generate(
                model="dall-e-3",
                prompt=input,
                size="1024x1024",
                quality="standard",
                n=1,
            )

            image_url = response.data[0].url

            st.image(image_url)


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
