import streamlit as st

# NLTK_DATA = "./nltk_data"
# TIKTOKEN_DATA = "./tiktoken_cache"

# from llama_index.llms.azure_openai import AzureOpenAI
#from openai import AzureOpenAI
from pandas import DataFrame
from pymysql import connect
from requests import post

# database credentials
DB_HOST = "tellmoredb.cd24ogmcy170.us-east-1.rds.amazonaws.com"
DB_USER = "admin"
DB_PASS = "2yYKKH8lUzaBvc92JUxW"
DB_PORT = "3306"
DB_NAME = "claires"
#DB_NAME = "retail_panopticon"
CONVO_DB_NAME = "store_questions"

# TellMore IP endpoint
# API_URL = "http://127.0.0.1:5000/response"
# API_URL = "http://tellmore-ip.azurewebsites.net/api/response"

# TellMore Azure OpenAI credentials
# AZURE_OPENAI_KEY = "94173b7e3f284f2c8f8eb1804fa55699"
# AZURE_OPENAI_ENDPOINT = "https://tellmoredemogpt.openai.azure.com/"
# AZURE_OPENAI_ENGINE = "tellmore-demo-gpt35"
# AZURE_OPENAI_MODEL_NAME = "gpt-3.5-turbo-0125"
# AZURE_OPENAI_TYPE = "azure"

# Claire's Accessories' colours
CLAIRE_DEEP_PURPLE = "#553D94"
CLAIRE_MAUVE = "#D2BBFF"

# AzureOpenAI LLM setup
# llm = AzureOpenAI(
#     model=AZURE_OPENAI_MODEL_NAME,
#     engine=AZURE_OPENAI_ENGINE,
#     api_key=AZURE_OPENAI_KEY,
#     azure_endpoint=AZURE_OPENAI_ENDPOINT,
#     api_type=AZURE_OPENAI_TYPE,
#     api_version="2024-03-01-preview",
#     temperature=0.3,
# )

st.set_page_config(
    layout = 'wide', 
    initial_sidebar_state = 'collapsed',
    page_title = 'Store OPS App',
    page_icon = 'claires-logo.svg',
)  # wide mode

# session state variables
if 'history' not in st.session_state:
    st.session_state['history'] = []

if 'display_df_and_nlr' not in st.session_state:
    st.session_state['display_df_and_nlr'] = False

if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ""


# connection to database
def connect_to_db(db_name):
    return connect(
        host = DB_HOST,
        port = int(DB_PORT),
        user = DB_USER,
        password = DB_PASS,
        db = db_name
    )


# get response Azure OpenAI
def get_openai_response(user_input):
    client = AzureOpenAI(
    api_key = AZURE_OPENAI_KEY,
    azure_endpoint = AZURE_OPENAI_ENDPOINT,
    api_version = "2024-03-01-preview",
    )
    response = client.chat.completions.create(
        model = AZURE_OPENAI_ENGINE,
        messages = [{"role": "user", "content": user_input}],
        max_tokens = 50
    )
    return response.choices[0].message.content


# post business query to TellMore IP
def send_message_to_api(message):
    api_url = API_URL
    payload = {
        "database": DB_NAME,
        "query": message
    }
    response = post(api_url, json = payload)
    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            st.error("Error decoding JSON")
            return None
    else:
        st.error(f"Error: HTTP {response.status_code} - {response.text}")
        return None


# execute SQL query
def execute_query(query, connection):
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            getResult = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
        return DataFrame(getResult, columns = columns)
    finally:
        connection.close()


# store business query
def store_question_in_db(question, sql_query):
    connection = connect_to_db(CONVO_DB_NAME)
    query = "INSERT INTO demo_pinned_questions (question, sql_query) VALUES (%s, %s)"
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (question, sql_query))
        connection.commit()
    finally:
        connection.close()


# retrieve business queries
def get_queries_from_db():
    connection = connect_to_db(CONVO_DB_NAME)
    query = "SELECT DISTINCT question, sql_query FROM demo_pinned_questions;"
    df = execute_query(query, connection)
    questions = {"Select a query": None}
    questions.update(dict(zip(df['question'], df['sql_query'])))
    return questions


# custom CSS for Streamlit app
def set_custom_css():
    custom_css = """
    <style>
        .st-emotion-cache-9aoz2h.e1vs0wn30 {
            display: flex;
            justify-content: center; /* Center-align the DataFrame */
        }
        .st-emotion-cache-9aoz2h.e1vs0wn30 table {
            margin: 0 auto; /* Center-align the table itself */
        }

        .button-container {
            display: flex;
            justify-content: flex-end; /* Align button to the right */
            margin-top: 10px;
        }

        .circular-button {
            border-radius: 50%;
            background-color: #553D94; /* Button color */
            color: white;
            border: none;
            padding: 10px 15px; /* Adjust size as needed */
            cursor: pointer;
        }

        .circular-button:hover {
            background-color: #452a7f; /* Slightly darker shade on hover */
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


# Store Ops application
def store_ops_app():
    with open(r'claires-logo.svg', 'r') as image:
        image_data = image.read()
    st.logo(image=image_data)

    st.markdown(f"""
    <h4 style="background-color: {CLAIRE_DEEP_PURPLE}; color: white; padding: 10px;">
        Ask a Question
    </h4>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    st.markdown("""
    <style>
    div.stButton {
        display: flex;
        justify-content: flex-end; /* Align button to the right */
        font-size: 30px; /* Increase font size */
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

    save_button_pressed = st.button('### :material/save:', key='save_button')

    store_questions = {
                "What is the Daily Sales Report (DSR) using our sales records for latest location of store Plzen Olympia on July 31, 2023?":
                    {
                        "sql": "SELECT f.NetSaleLocal, f.NetSaleUSD, f.NetQuantity, c.CalendarDate FROM fact_Sale f JOIN dim_Calendar c ON f.CalendarKey = c.CalendarKey JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'Plzen Olympia' AND c.CalendarDate = '2023-07-31';",
                        "nlr": "On July 31, 2023, the Daily Sales Report (DSR) for the Plzen Olympia store shows a net sale of 8,301.59 in local currency, which is equivalent to 384.29 USD. The total quantity sold was 52 units."
                    },
                "Compare the sales revenue for top five stores?":
                    {
                        "sql": "SELECT f.LocationLatestKey, SUM(f.NetSaleUSD) AS TotalSales FROM fact_Sale f JOIN dim_Calendar d ON f.CalendarKey = d.CalendarKey GROUP BY f.LocationLatestKey ORDER BY TotalSales DESC LIMIT 5;",
                        "nlr": "The sales revenue for the top five stores is as follows: Store located at 2365 generated the highest revenue of approximately $3.53 million, followed closely by the store at 4032 with around $3.44 million. The third store, located at 3693, achieved total sales of about $3.06 million. The fourth store, at location 494, recorded sales of approximately $2.99 million, while the fifth store, located at 4040, had total sales of around $2.52 million."
                    },
                "What is the sum of number of transactions this year compared to last year for latest location of store Plzen Olympia?":
                    {
                        "sql": "SELECT SUM(f.TransactionCountTY) AS TotalTransactionsTY, SUM(f.TransactionCountLY) AS TotalTransactionsLY FROM fact_Basket f JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'Plzen Olympia';",
                        "nlr": "The sum of the number of transactions this year compared to last year for the latest location of the store Plzen Olympia is 14148.0 for this year and 16136.0 for last year."
                    },
                "What were the sales for each store during the 'autumn/winter' season last year for store with latest location ALA MOANA CENTER?":
                    {
                        "sql": "SELECT f.TransactionCountLY, d.LatestLocation FROM fact_Basket f  JOIN dim_Location_Latest d ON f.LocationLatestKey = d.LocationLatestKey JOIN dim_Calendar c ON f.CalendarKey = c.CalendarKey WHERE d.LatestLocation = 'ALA MOANA CENTER' AND c.Season = 'autumn/winter' AND c.FiscalYear = YEAR(CURDATE()) - 1 ORDER BY f.TransactionCountLY DESC;",
                        "nlr": "During the 'autumn/winter' season last year, the sales for the store located at ALA MOANA CENTER were as follows: one transaction count was 142, and another was 165."
                    },
                "What is the year-to-date (YTD) net sales compared to the same period last year for latest location of store S RONCQ?":
                    {
                        "sql": "SELECT f.NetSaleUSD, f.NetSaleUSDLY FROM fact_Sale f JOIN dim_Calendar c ON f.CalendarKey = c.CalendarKey WHERE c.FiscalYear = YEAR(CURRENT_DATE) OR c.FiscalYear = YEAR(CURRENT_DATE) - 1 ORDER BY c.CalendarDate DESC;",
                        "nlr": "The year-to-date (YTD) net sales for the latest location of store S RONCQ is $175.95, compared to $217.96 for the same period last year."
                    },
                "What is the average number of units sold per transaction at the latest location of store ALA MOANA CENTER?":
                    {
                        "sql": "SELECT AVG(f.TransactionCountTY) AS AverageUnitsSold FROM fact_Basket f JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'ALA MOANA CENTER';",
                        "nlr": "The average number of units sold per transaction at the latest location of store ALA MOANA CENTER is approximately 125.30."
                    }
            }

    if save_button_pressed:
        if st.session_state.history:
            last_chat = st.session_state.history[-1]
            store_question_in_db(last_chat['question'], last_chat['sql'])
            st.success("Last conversation stored.")
            st.session_state['user_input'] = ""
            st.session_state['display_df_and_nlr'] = False
            st.session_state['last_result'] = None
            st.session_state['last_nlr'] = None
        else:
            st.warning("No conversation to store.")

    for chat in st.session_state.history:
        st.write(f"**User:** {chat['question']}")
        st.write(f"**Natural Language Response:** {chat['nlr']}")

    st.session_state['user_input'] = st.text_input("Business Question: ", st.session_state['user_input'])

    if st.session_state['user_input'] and not save_button_pressed:
        user_input = st.session_state['user_input']

        # If the user input matches one of the predefined questions
        if user_input in store_questions:
            ip_response = store_questions[user_input]
            st.session_state.history.append({
                "question": user_input,
                "nlr": ip_response["nlr"],
                "sql": ip_response["sql"],
            })
            conn = connect_to_db(DB_NAME)
            result = execute_query(ip_response["sql"], conn)
            st.session_state['display_df_and_nlr'] = True
            st.session_state['last_result'] = result
            st.session_state['last_nlr'] = ip_response["nlr"]
        else:
            st.warning("No matching question found. Please try again.")

    # if st.session_state['user_input'] and not save_button_pressed:
    #     ip_response = send_message_to_api(st.session_state['user_input'])
    #     st.session_state.history.append({
    #         "question": st.session_state['user_input'],
    #         "nlr": ip_response["Engine Response"],
    #         "sql": ip_response["Query SQL"],
    #     })
    #     conn = connect_to_db(DB_NAME)
    #     result = execute_query(ip_response["Query SQL"], conn)
    #     st.session_state['display_df_and_nlr'] = True
    #     st.session_state['last_result'] = result
    #     st.session_state['last_nlr'] = st.session_state.history[-1]["nlr"]

    if st.session_state['display_df_and_nlr']:
        st.dataframe(st.session_state['last_result'], height = 200)
        st.write(st.session_state['last_nlr'])

def delete_query_from_db(query):
    connection = connect_to_db(CONVO_DB_NAME)
    try:
        with connection.cursor() as cursor:
            delete_query = """
            DELETE FROM demo_pinned_questions WHERE question = %s;
            """
            cursor.execute(delete_query, (query,))
        connection.commit()
    finally:
        connection.close()

# Store Manager application
def store_manager_app():
    with open(r'claires-logo.svg', 'r') as image:
        image_data = image.read()
    st.logo(image=image_data)

    store_questions = {
        "Plzen Olympia": {
            "What is the Daily Sales Report (DSR) using our sales records for latest location of store Plzen Olympia on July 31, 2023?":
                {
                    "sql": "SELECT f.NetSaleLocal, f.NetSaleUSD, f.NetQuantity, c.CalendarDate FROM claires.fact_Sale f JOIN claires.dim_Calendar c ON f.CalendarKey = c.CalendarKey JOIN claires.dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'Plzen Olympia' AND c.CalendarDate = '2023-07-31';",
                    "nlr": "On July 31, 2023, the Daily Sales Report (DSR) for the Plzen Olympia store shows a net sale of 8,301.59 in local currency, which is equivalent to 384.29 USD. The total quantity sold was 52 units."
                },
            "Compare the sales revenue for top five stores?":
                {
                    "sql": "SELECT f.LocationLatestKey, SUM(f.NetSaleUSD) AS TotalSales FROM fact_Sale f JOIN dim_Calendar d ON f.CalendarKey = d.CalendarKey GROUP BY f.LocationLatestKey ORDER BY TotalSales DESC LIMIT 5;",
                    "nlr": "The sales revenue for the top five stores is as follows: Store located at 2365 generated the highest revenue of approximately $3.53 million, followed closely by the store at 4032 with around $3.44 million. The third store, located at 3693, achieved total sales of about $3.06 million. The fourth store, at location 494, recorded sales of approximately $2.99 million, while the fifth store, located at 4040, had total sales of around $2.52 million.",
                },
            "What is the sum of number of transactions this year compared to last year for latest location of store Plzen Olympia?":
                {
                    "sql": "SELECT SUM(f.TransactionCountTY) AS TotalTransactionsTY, SUM(f.TransactionCountLY) AS TotalTransactionsLY FROM fact_Basket f JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'Plzen Olympia';",
                    "nlr": "The sum of the number of transactions this year compared to last year for the latest location of the store Plzen Olympia is 14148.0 for this year and 16136.0 for last year.",
                },
            "What were the sales for each store during the 'autumn/winter' season last year for store with latest location ALA MOANA CENTER?":
                {
                    "sql": "SELECT f.TransactionCountLY, d.LatestLocation FROM fact_Basket f  JOIN dim_Location_Latest d ON f.LocationLatestKey = d.LocationLatestKey JOIN dim_Calendar c ON f.CalendarKey = c.CalendarKey WHERE d.LatestLocation = 'Plzen Olympia' AND c.Season = 'autumn/winter' AND c.FiscalYear = YEAR(CURDATE()) - 1 ORDER BY f.TransactionCountLY DESC;",
                    "nlr": "During the 'autumn/winter' season last year, the sales for the store located at Plzen Olympia were as follows: one transaction count was 26, and another was 22",
                },
            "What is the average number of units sold per transaction at the latest location of store ALA MOANA CENTER?":
                {
                    "sql": "SELECT AVG(f.TransactionCountTY) AS AverageUnitsSold FROM fact_Basket f JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'Plzen Olympia'",
                    "nlr": "The average number of units sold per transaction at the latest location of store Plzen Olympia is approximately 25.8647.",
                },


        },
        "ALA MOANA CENTER": {
            "What is the Daily Sales Report (DSR) using our sales records for latest location of store Plzen Olympia on July 31, 2023?":
                {
                    "sql": "SELECT f.NetSaleLocal, f.NetSaleUSD, f.NetQuantity, c.CalendarDate FROM claires.fact_Sale f JOIN claires.dim_Calendar c ON f.CalendarKey = c.CalendarKey JOIN claires.dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'ALA MOANA CENTER' AND c.CalendarDate = '2023-07-31';",
                    "nlr": "On July 31, 2023, the Daily Sales Report (DSR) for the ALA MOANA CENTER store shows a net sale of 8,301.59 in local currency, which is equivalent to 384.29 USD. The total quantity sold was 52 units."
                },
            "Compare the sales revenue for top five stores?":
                {
                    "sql": "SELECT f.LocationLatestKey, SUM(f.NetSaleUSD) AS TotalSales FROM fact_Sale f JOIN dim_Calendar d ON f.CalendarKey = d.CalendarKey GROUP BY f.LocationLatestKey ORDER BY TotalSales DESC LIMIT 5;",
                    "nlr": "The sales revenue for the top five stores is as follows: Store located at 2365 generated the highest revenue of approximately $3.53 million, followed closely by the store at 4032 with around $3.44 million. The third store, located at 3693, achieved total sales of about $3.06 million. The fourth store, at location 494, recorded sales of approximately $2.99 million, while the fifth store, located at 4040, had total sales of around $2.52 million.",
                },
            "What is the sum of number of transactions this year compared to last year for latest location of store Plzen Olympia?":
                {
                    "sql": "SELECT SUM(f.TransactionCountTY) AS TotalTransactionsTY, SUM(f.TransactionCountLY) AS TotalTransactionsLY FROM fact_Basket f JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'ALA MOANA CENTER';",
                    "nlr": "The sum of the number of transactions this year compared to last year for the latest location of the store ALA MOANA CENTER is 62029 for this year and 68664 for last year.",
                },
            "What were the sales for each store during the 'autumn/winter' season last year for store with latest location ALA MOANA CENTER?":
                {
                    "sql": "SELECT f.TransactionCountLY, d.LatestLocation FROM fact_Basket f  JOIN dim_Location_Latest d ON f.LocationLatestKey = d.LocationLatestKey JOIN dim_Calendar c ON f.CalendarKey = c.CalendarKey WHERE d.LatestLocation = 'ALA MOANA CENTER' AND c.Season = 'autumn/winter' AND c.FiscalYear = YEAR(CURDATE()) - 1 ORDER BY f.TransactionCountLY DESC;",
                    "nlr": "During the 'autumn/winter' season last year, the sales for the store located at ALA MOANA CENTER were as follows: one transaction count was 142, and another was 165",
                },
            "What is the average number of units sold per transaction at the latest location of store ALA MOANA CENTER?":
                {
                    "sql": "SELECT AVG(f.TransactionCountTY) AS AverageUnitsSold FROM fact_Basket f JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'ALA MOANA CENTER'",
                    "nlr": "The average number of units sold per transaction at the latest location of store ALA MOANA CENTER is approximately 125.30.",
                },
        },
    }

    store_list = ["Store ID", "Plzen Olympia", "ALA MOANA CENTER"]

    dynamic_queries = get_queries_from_db()

    filtered_store_questions = {}
    for store, questions in store_questions.items():
        store_dynamic_queries = dynamic_queries.get(store, {})
        filtered_store_questions[store] = {
            q: details for q, details in questions.items() if q in store_dynamic_queries
        }

    if 'queries' not in st.session_state:
        st.session_state['queries'] = {}

    st.markdown(f"""
    <h4 style="background-color: {CLAIRE_DEEP_PURPLE}; color: white; padding: 10px;">
        Simulate a Store
    </h4>
    """, unsafe_allow_html=True)

    store_name_id_placeholder = st.markdown(f"""
    <h4 style="background-color: {CLAIRE_MAUVE}; color: black; padding: 10px;">
    </h4>
    """, unsafe_allow_html=True)

    st.markdown("""
        <style>
        div.stButton {
            display: flex;
            justify-content: flex-end; /* Align button to the right */
            font-size: 30px; /* Increase font size */
            margin-top: 10px;
        }
        </style>
        """, unsafe_allow_html=True)

    unpin_button_pressed = st.button('### :material/delete:', key='unpin_button')

    selected_store = st.selectbox("Select a Store", store_list)

    if selected_store != "Store ID":
        store_name = {
            "Store 1": "Plzen Olympia",
            "Store 2": "ALA MOANA CENTER"
        }.get(selected_store, "")

        store_name_id_placeholder.markdown(f"""
        <h4 style="background-color: {CLAIRE_MAUVE}; color: black; padding: 10px;">
            {store_name}, {selected_store}
        </h4>
        """, unsafe_allow_html=True)

    queries_for_store = store_questions.get(selected_store, {})
    query_options = list(queries_for_store.keys())
    selected_query = st.selectbox("Select a query", query_options if query_options else ["Select a query"])

    if unpin_button_pressed and selected_query != "Select a query":
        queries_for_store.pop(selected_query, None)
        delete_query_from_db(selected_query)
        st.success(f"Query '{selected_query}' has been removed.")
    elif unpin_button_pressed:
        st.warning("Select a query to unpin.")

    if selected_query and selected_query != "Select a query":
        sql_query = queries_for_store[selected_query]["sql"]
        conn = connect_to_db(DB_NAME)
        cur = conn.cursor()
        cur.execute(sql_query)
        getDataTable = cur.fetchall()

        st.dataframe(getDataTable)

        nlr = queries_for_store[selected_query]["nlr"]
        st.write(nlr)

    # if selected_store and selected_store != "Store ID" and selected_query and selected_query != "Select a query" and not unpin_button_pressed:
    #     conn = connect_to_db(DB_NAME)
    #     cur = conn.cursor()
    #     cur.execute(st.session_state["queries"][selected_store][selected_query])
    #     getDataTable = cur.fetchall()
    #     language_prompt = f"""
    #         following is a business question: {selected_query}\n
    #         columns from an enterprise database schema were identified to answer this question\n
    #         upon querying the columns, the following SQL data table was returned: {getDataTable}\n
    #         generate a natural language response explaining the data table that was
    #         returned, with the business question as context\n
    #         respond only with the natural language explanation of the data table output, do not explain the
    #         business question or how the columns were selected and queried\n
    #     """
    #     ans = get_openai_response(language_prompt)
    #     st.markdown(ans)


# main application setup
set_custom_css()
persona = st.sidebar.radio("", ("Ask a Question", "Simulate a Store"))  # sidebar toggle

if persona == "Ask a Question":
    store_ops_app()

elif persona == "Simulate a Store":
    store_manager_app()
