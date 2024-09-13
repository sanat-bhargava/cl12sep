import streamlit as st

# NLTK_DATA = "./nltk_data"
# TIKTOKEN_DATA = "./tiktoken_cache"

# from llama_index.llms.azure_openai import AzureOpenAI
#from openai import AzureOpenAI
import pandas as pd
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
# def get_openai_response(user_input):
#     client = AzureOpenAI(
#     api_key = AZURE_OPENAI_KEY,
#     azure_endpoint = AZURE_OPENAI_ENDPOINT,
#     api_version = "2024-03-01-preview",
#     )
#     response = client.chat.completions.create(
#         model = AZURE_OPENAI_ENGINE,
#         messages = [{"role": "user", "content": user_input}],
#         max_tokens = 50
#     )
#     return response.choices[0].message.content


# post business query to TellMore IP
# def send_message_to_api(message):
#     api_url = API_URL
#     payload = {
#         "database": DB_NAME,
#         "query": message
#     }
#     response = post(api_url, json = payload)
#     if response.status_code == 200:
#         try:
#             return response.json()
#         except ValueError:
#             st.error("Error decoding JSON")
#             return None
#     else:
#         st.error(f"Error: HTTP {response.status_code} - {response.text}")
#         return None


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
                "What is the net sales on July 31, 2023 compared to the same period last year for store VILLAGE CROSSING?":
                {
                    "sql": "SELECT f.NetSaleLocal, f.NetSaleLocalLY FROM fact_Sale f JOIN dim_Calendar c ON f.CalendarKey = c.CalendarKey JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'VILLAGE CROSSING' AND c.CalendarDate = '2023-07-31';",
                    "nlr": "On July 31, 2023, the net sales for the latest location of the store Village Crossing were as follows: 448.98, 49.98, and 40.00. In comparison, there were no net sales recorded for the same period last year."
                },
                "What is the sum of number of transactions this year compared to last year for store VILLAGE CROSSING?":
                {
                    "sql": "SELECT SUM(f.TransactionCountTY) AS TotalTransactionsTY, SUM(f.TransactionCountLY) AS TotalTransactionsLY FROM fact_Basket f JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'VILLAGE CROSSING';",
                    "nlr": "The data table returned indicates that the total number of transactions for the latest location of the store VILLAGE CROSSING this year is 5,285, while the number of transactions from last year is 0. This suggests that the store either did not operate last year or had no recorded transactions during that time, resulting in a significant increase in activity this year.",
                },
                "What are the net margins in USD for store VILLAGE CROSSING?":
                {
                    "sql": "SELECT f.NetExVATUSDPlan FROM Fact_Store_Plan f JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'VILLAGE CROSSING';",
                    "nlr": "The data table returned consists of a series of net margin values in USD for the store located at VILLAGE CROSSING. The values represent individual entries of net margins, with some figures appearing multiple times, indicating that there may be repeated measurements or records for certain time periods or transactions.\n\nThe margins range from a low of 0.0 USD, which suggests instances where there was no profit, to a high of 17,703.0 USD, indicating significant profitability in some cases. Most values fall within a relatively consistent range, with several margins clustered around the 6,000 to 10,000 USD mark.\n\nThis data provides a comprehensive view of the store's financial performance, highlighting both the variability and consistency in net margins over the observed period. The presence of multiple identical values suggests that certain margins were likely recorded under similar conditions or timeframes.",
                },
                "What is the Daily Sales Report (DSR) using our sales records for store VILLAGE CROSSING on July 31, 2023?":
                {
                    "sql": "SELECT f.NetSaleLocal, f.NetSaleUSD, f.NetQuantity, c.CalendarDate FROM fact_Sale f JOIN dim_Calendar c ON f.CalendarKey = c.CalendarKey JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'VILLAGE CROSSING' AND c.CalendarDate = '2023-07-31';",
                    "nlr": "On July 31, 2023, the Daily Sales Report (DSR) for the Village Crossing store shows the following sales records: The total net sales in the local currency amounted to 448.98 USD, with a total of 82 items sold. Additionally, there were sales of 49.98 USD from 2 items and 40.00 USD from another 2 items.",
                },
                "Compare the average sales revenue for the store VILLAGE CROSSING with the average sales revenue for all stores in USA.":
                {
                    "sql": "SELECT AVG(fs.NetSaleUSD) AS AverageSalesRevenue FROM fact_Sale fs JOIN dim_Location_Latest dl ON fs.LocationLatestKey = dl.LocationLatestKey WHERE dl.LatestLocation = 'VILLAGE CROSSING' \nGROUP BY dl.LatestCountry\nUNION\nSELECT AVG(fs.NetSaleUSD) AS AverageSalesRevenue FROM fact_Sale fs JOIN dim_Location_Latest dl ON fs.LocationLatestKey = dl.LocationLatestKey WHERE dl.LatestCountry = 'USA';",
                    "nlr": "The average sales revenue for the store located at VILLAGE CROSSING is approximately 319.77, while the average sales revenue for all stores in the USA is approximately 471.99.",
                },
                "What were the sales during the 'Autumn/Winter' season for store VILLAGE CROSSING?":
                {
                    "sql": "SELECT dll.LatestLocation,SUM(f.NetSaleUSD) as TotalSales, d.Season, d.FiscalMonthName, d.FiscalYear \nFROM fact_Sale f JOIN dim_Calendar d ON f.CalendarKey = d.CalendarKey JOIN dim_Location_Latest dll ON f.LocationLatestKey =dll.LocationLatestKey WHERE d.Season = 'Autumn/Winter' AND f.LocationLatestKey = (SELECT LocationLatestKey FROM dim_Location_Latest dll WHERE dll.LatestLocation = 'VILLAGE CROSSING') GROUP BY d.FiscalMonthName, d.FiscalYear ORDER BY d.FiscalYear DESC, d.FiscalMonthName;",
                    "nlr": "The sales during the 'Autumn/Winter' season for the store located at VILLAGE CROSSING were as follows: In August 2023, the sales totaled 1,235.49 USD; in December 2022, the sales amounted to 29,932.37 USD; and in January 2022, the sales were 18,783.33 USD.",
                },
                "What is the average number of units sold per transaction at store VILLAGE CROSSING?":
                {
                    "sql": "SELECT AVG(f.TransactionCountTY) AS AverageUnitsSold FROM fact_Basket f\nJOIN dim_Location_Latest d ON f.LocationLatestKey = d.LocationLatestKey\nWHERE d.LatestLocation = 'VILLAGE CROSSING';",
                    "nlr": "The average number of units sold per transaction at the latest location of store VILLAGE CROSSING is approximately 22.78.",
                },

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
            if user_input== "Compare the average sales revenue for the store VILLAGE CROSSING with the average sales revenue for all stores in USA.":
                result = pd.read_sql(ip_response["sql"], conn)
                transposed_df = result.transpose()
                transposed_df.columns = ["VILLAGE CROSSING", "Average for all stores in USA"]
                result = transposed_df
                height = None
            else:
                result = pd.read_sql(ip_response["sql"], conn)
                height = 200
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
        st.dataframe(st.session_state['last_result'], height = height,hide_index=True)
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
        "VILLAGE CROSSING": {
            "What is the net sales on July 31, 2023 compared to the same period last year for store VILLAGE CROSSING?":
                {
                    "sql": "SELECT f.NetSaleLocal, f.NetSaleLocalLY FROM fact_Sale f JOIN dim_Calendar c ON f.CalendarKey = c.CalendarKey JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'VILLAGE CROSSING' AND c.CalendarDate = '2023-07-31';",
                    "nlr": "On July 31, 2023, the net sales for the latest location of the store Village Crossing were as follows: 448.98, 49.98, and 40.00. In comparison, there were no net sales recorded for the same period last year."
                },
            "What is the sum of number of transactions this year compared to last year for store VILLAGE CROSSING?":
                {
                    "sql": "SELECT SUM(f.TransactionCountTY) AS TotalTransactionsTY, SUM(f.TransactionCountLY) AS TotalTransactionsLY FROM fact_Basket f JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'VILLAGE CROSSING';",
                    "nlr": "The data table returned indicates that the total number of transactions for the latest location of the store VILLAGE CROSSING this year is 5,285, while the number of transactions from last year is 0. This suggests that the store either did not operate last year or had no recorded transactions during that time, resulting in a significant increase in activity this year.",
                },
            "What are the net margins in USD for store VILLAGE CROSSING?":
                {
                    "sql": "SELECT f.NetExVATUSDPlan FROM Fact_Store_Plan f JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'VILLAGE CROSSING';",
                    "nlr": "The data table returned consists of a series of net margin values in USD for the store located at VILLAGE CROSSING. The values represent individual entries of net margins, with some figures appearing multiple times, indicating that there may be repeated measurements or records for certain time periods or transactions.\n\nThe margins range from a low of 0.0 USD, which suggests instances where there was no profit, to a high of 17,703.0 USD, indicating significant profitability in some cases. Most values fall within a relatively consistent range, with several margins clustered around the 6,000 to 10,000 USD mark.\n\nThis data provides a comprehensive view of the store's financial performance, highlighting both the variability and consistency in net margins over the observed period. The presence of multiple identical values suggests that certain margins were likely recorded under similar conditions or timeframes.",
                },
            "What is the Daily Sales Report (DSR) using our sales records for store VILLAGE CROSSING on July 31, 2023?":
                {
                    "sql": "SELECT f.NetSaleLocal, f.NetSaleUSD, f.NetQuantity, c.CalendarDate FROM fact_Sale f JOIN dim_Calendar c ON f.CalendarKey = c.CalendarKey JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'VILLAGE CROSSING' AND c.CalendarDate = '2023-07-31';",
                    "nlr": "On July 31, 2023, the Daily Sales Report (DSR) for the Village Crossing store shows the following sales records: The total net sales in the local currency amounted to 448.98 USD, with a total of 82 items sold. Additionally, there were sales of 49.98 USD from 2 items and 40.00 USD from another 2 items.",
                },
            "Compare the average sales revenue for the store VILLAGE CROSSING with the average sales revenue for all stores in USA.":
                {
                    "sql": "SELECT AVG(fs.NetSaleUSD) AS AverageSalesRevenue FROM fact_Sale fs JOIN dim_Location_Latest dl ON fs.LocationLatestKey = dl.LocationLatestKey WHERE dl.LatestLocation = 'VILLAGE CROSSING' \nGROUP BY dl.LatestCountry\nUNION\nSELECT AVG(fs.NetSaleUSD) AS AverageSalesRevenue FROM fact_Sale fs JOIN dim_Location_Latest dl ON fs.LocationLatestKey = dl.LocationLatestKey WHERE dl.LatestCountry = 'USA';",
                    "nlr": "The average sales revenue for the store located at VILLAGE CROSSING is approximately 319.77, while the average sales revenue for all stores in the USA is approximately 471.99.",
                },
            "What were the sales during the 'Autumn/Winter' season for store VILLAGE CROSSING?":
                {
                    "sql": "SELECT dll.LatestLocation,SUM(f.NetSaleUSD) as TotalSales, d.Season, d.FiscalMonthName, d.FiscalYear \nFROM fact_Sale f JOIN dim_Calendar d ON f.CalendarKey = d.CalendarKey JOIN dim_Location_Latest dll ON f.LocationLatestKey =dll.LocationLatestKey WHERE d.Season = 'Autumn/Winter' AND f.LocationLatestKey = (SELECT LocationLatestKey FROM dim_Location_Latest dll WHERE dll.LatestLocation = 'VILLAGE CROSSING') GROUP BY d.FiscalMonthName, d.FiscalYear ORDER BY d.FiscalYear DESC, d.FiscalMonthName;",
                    "nlr": "The sales during the 'Autumn/Winter' season for the store located at VILLAGE CROSSING were as follows: In August 2023, the sales totaled 1,235.49 USD; in December 2022, the sales amounted to 29,932.37 USD; and in January 2022, the sales were 18,783.33 USD.",
                },
            "What is the average number of units sold per transaction at the store VILLAGE CROSSING?":
                {
                    "sql": "SELECT AVG(f.TransactionCountTY) AS AverageUnitsSold FROM fact_Basket f\nJOIN dim_Location_Latest d ON f.LocationLatestKey = d.LocationLatestKey\nWHERE d.LatestLocation = 'VILLAGE CROSSING';",
                    "nlr": "The average number of units sold per transaction at the latest location of store VILLAGE CROSSING is approximately 22.78.",
                },
        },
        "THE PIKE OUTLETS": {
            "What is the net sales on July 31, 2023 compared to the same period last year for store THE PIKE OUTLETS?":
                {
                    "sql": "SELECT f.NetSaleLocal, f.NetSaleLocalLY FROM fact_Sale f JOIN dim_Calendar c ON f.CalendarKey = c.CalendarKey JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'THE PIKE OUTLETS' AND c.CalendarDate = '2023-07-31';",
                    "nlr": "On July 31, 2023, the net sales for the latest location of the store THE PIKE OUTLETS were as follows: 65, 242.96, and 1197.18. In comparison, there were no net sales recorded for the same period last year."
                },
            "What is the sum of number of transactions this year compared to last year for store THE PIKE OUTLETS?":
                {
                    "sql": "SELECT SUM(f.TransactionCountTY) AS TotalTransactionsTY, SUM(f.TransactionCountLY) AS TotalTransactionsLY FROM fact_Basket f JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'THE PIKE OUTLETS';",
                    "nlr": "The data table returned indicates that for the latest location of the store, THE PIKE OUTLETS, there were a total of 7,213 transactions this year, while there were no transactions recorded last year. This suggests a significant increase in activity at this location compared to the previous year.",
                },
            "What are the net margins in USD for store THE PIKE OUTLETS?":
                {
                    "sql": "SELECT f.NetExVATUSDPlan FROM Fact_Store_Plan f JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'THE PIKE OUTLETS';",
                    "nlr": "The data table returned consists of a series of net margin values in USD for the store located at THE PIKE OUTLETS. The values are presented in a single column, with some margins appearing multiple times, indicating that there may be repeated entries for certain periods or transactions.\n\nThe margins range from as low as 0.0 to as high as 16,700.54, suggesting a significant variation in performance. Notably, there are several entries with a value of 0.0, which may indicate periods of no profit or data not being recorded. The presence of multiple identical values, such as 10,975.71 and 12,232.21, could imply consistent performance during specific timeframes.\n\nOverall, this data provides a snapshot of the financial performance of the store, highlighting both profitable and unprofitable periods."
                },
            "What is the Daily Sales Report (DSR) using our sales records for the store THE PIKE OUTLETS on July 31, 2023?": {
                "sql": "SELECT f.NetSaleLocal, f.NetSaleUSD, f.NetQuantity, c.CalendarDate FROM fact_Sale f JOIN dim_Calendar c ON f.CalendarKey = c.CalendarKey JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'THE PIKE OUTLETS' AND c.CalendarDate = '2023-07-31';",
                "nlr": "The data table returned provides a summary of sales transactions for the store at THE PIKE OUTLETS on July 31, 2023. Each row represents a distinct sales record for that day.\n\nThe first row indicates a total sales amount of USD 65.00, with a quantity of 4 items sold. The second row shows sales of USD 242.96, also with a quantity of 4 items sold. The third row reflects a significantly higher total sales amount of USD 1,197.18, with a quantity of 153 items sold.\n\nAll entries are dated July 31, 2023, suggesting that these transactions occurred on the same day. This data illustrates the range of sales activity at the store, highlighting both lower and higher sales volumes for that date.",
            },
            "Compare the average sales revenue for the store THE PIKE OUTLETS with the average sales revenue for all stores in USA.": {
                "sql": "SELECT AVG(fs.NetSaleUSD) AS AverageSalesRevenue FROM fact_Sale fs JOIN dim_Location_Latest dl ON fs.LocationLatestKey = dl.LocationLatestKey WHERE dl.LatestLocation = 'THE PIKE OUTLETS' \nGROUP BY dl.LatestCountry\nUNION\nSELECT AVG(fs.NetSaleUSD) AS AverageSalesRevenue FROM fact_Sale fs JOIN dim_Location_Latest dl ON fs.LocationLatestKey = dl.LocationLatestKey WHERE dl.LatestCountry = 'USA';",
                "nlr": "The data table returned two values representing average sales revenue. The first value, approximately 450.18, corresponds to the average sales revenue for the store located at THE PIKE OUTLETS. The second value, approximately 471.99, represents the average sales revenue for all stores located in the USA. This comparison indicates that the average sales revenue for THE PIKE OUTLETS is lower than the average for all stores in the country.",
            },
            "What were the sales during the 'Autumn/Winter' season for the store THE PIKE OUTLETS?": {
                "sql": "SELECT dll.LatestLocation,SUM(f.NetSaleUSD) as TotalSales, d.Season, d.FiscalMonthName, d.FiscalYear \nFROM fact_Sale f JOIN dim_Calendar d ON f.CalendarKey = d.CalendarKey JOIN dim_Location_Latest dll ON f.LocationLatestKey =dll.LocationLatestKey WHERE d.Season = 'Autumn/Winter' AND f.LocationLatestKey = (SELECT LocationLatestKey FROM dim_Location_Latest dll WHERE dll.LatestLocation = 'THE PIKE OUTLETS') GROUP BY d.FiscalMonthName, d.FiscalYear ORDER BY d.FiscalYear DESC, d.FiscalMonthName;",
                "nlr": "The data table returned provides sales figures for the 'Autumn/Winter' season at the store located at THE PIKE OUTLETS. It shows two entries: the first entry indicates that in August 2023, the store achieved sales of USD 4,105.16 during the Autumn/Winter season. The second entry reveals that in January 2022, the store recorded sales of USD 3,522.25 for the same season. This data highlights the sales performance of THE PIKE OUTLETS during the Autumn/Winter season across two different years.",
            },
            "What is the average number of units sold per transaction at the store THE PIKE OUTLETS?": {
                "sql": "SELECT AVG(f.TransactionCountTY) AS AverageUnitsSold FROM fact_Basket f\nJOIN dim_Location_Latest d ON f.LocationLatestKey = d.LocationLatestKey\nWHERE d.LatestLocation = 'THE PIKE OUTLETS';",
                "nlr": "The data table returned indicates that the average number of units sold per transaction at the latest location of store THE PIKE OUTLETS is approximately 38.37. This figure suggests that, on average, each transaction at this location involves the sale of around 38 units.",
            },
        },

        "FIVE POINTS PLAZA": {
            "What is the net sales on July 31, 2023 compared to the same period last year for store FIVE POINTS PLAZA?":
                {
                    "sql": "SELECT f.NetSaleLocal, f.NetSaleLocalLY FROM fact_Sale f JOIN dim_Calendar c ON f.CalendarKey = c.CalendarKey JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'FIVE POINTS PLAZA' AND c.CalendarDate = '2023-07-31';",
                    "nlr": "On July 31, 2023, the net sales for the latest location of the store FIVE POINTS PLAZA were as follows: 80, 196.96, and 484.48. In comparison, there were no net sales recorded for the same period last year."
                },
            "What is the sum of number of transactions this year compared to last year for store FIVE POINTS PLAZA?":
                {
                    "sql": "SELECT SUM(f.TransactionCountTY) AS TotalTransactionsTY, SUM(f.TransactionCountLY) AS TotalTransactionsLY FROM fact_Basket f JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'FIVE POINTS PLAZA';",
                    "nlr": "The data table returned indicates that the total number of transactions for the latest location of the store, FIVE POINTS PLAZA, this year is 5,188, while the number of transactions from last year is 0. This suggests that the store has either just opened this year or has not recorded any transactions in the previous year.",
                },
            "What are the net margins in USD for store FIVE POINTS PLAZA?":
                {
                    "sql": "SELECT f.NetExVATUSDPlan FROM Fact_Store_Plan f JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'FIVE POINTS PLAZA';",
                    "nlr": "The data table returned consists of a series of net margin values in USD for the store located at FIVE POINTS PLAZA. Each value represents a recorded net margin, with some values appearing multiple times, indicating that these margins may have been recorded on different occasions or under different conditions.\n\nThe margins range from 0.0 to 11,009.72 USD, showcasing a variety of performance levels. Notably, several entries are zero, suggesting instances where the store may not have generated a profit. The highest recorded net margin is 11,009.72 USD, while the lowest is 0.0 USD, reflecting a significant variance in profitability.\n\nOverall, this data provides a snapshot of the financial performance of the store, highlighting both successful and challenging periods."
                },
            "What is the Daily Sales Report (DSR) using our sales records for the store FIVE POINTS PLAZA on July 31, 2023?": {
                "sql": "SELECT f.NetSaleLocal, f.NetSaleUSD, f.NetQuantity, c.CalendarDate FROM fact_Sale f JOIN dim_Calendar c ON f.CalendarKey = c.CalendarKey JOIN dim_Location_Latest l ON f.LocationLatestKey = l.LocationLatestKey WHERE l.LatestLocation = 'FIVE POINTS PLAZA' AND c.CalendarDate = '2023-07-31';",
                "nlr": "The data table returned contains sales information for the store at FIVE POINTS PLAZA on July 31, 2023. Each row represents a different sales transaction or summary for that day.\n\nThe first column shows the total sales amount for each transaction, with values of 80.0, 196.96, and 484.48. These figures indicate the revenue generated from individual sales. The second column mirrors the first, confirming the sales amounts are consistent.\n\nThe third column indicates the number of transactions that contributed to each sales amount, all of which are 4 for the first two rows and 64 for the last row. This suggests that the first two sales amounts were generated from a smaller number of transactions compared to the last one, which had a significantly higher volume of sales.\n\nThe final column provides the date of the transactions, confirming that all entries are from July 31, 2023. Overall, this data reflects the sales performance of the store on that specific day, highlighting both the total sales and the number of transactions contributing to those totals.",
            },
            "Compare the average sales revenue for the store FIVE POINTS PLAZA with the average sales revenue for all stores in USA.": {
                "sql": "SELECT AVG(fs.NetSaleUSD) AS AverageSalesRevenue FROM fact_Sale fs JOIN dim_Location_Latest dl ON fs.LocationLatestKey = dl.LocationLatestKey WHERE dl.LatestLocation = 'FIVE POINTS PLAZA' \nGROUP BY dl.LatestCountry\nUNION\nSELECT AVG(fs.NetSaleUSD) AS AverageSalesRevenue FROM fact_Sale fs JOIN dim_Location_Latest dl ON fs.LocationLatestKey = dl.LocationLatestKey WHERE dl.LatestCountry = 'USA';",
                "nlr": "The data table returned two values representing average sales revenue. The first value, approximately 370.23, corresponds to the average sales revenue for the store located in FIVE POINTS PLAZA. The second value, approximately 471.99, represents the average sales revenue for all stores located in the USA. This comparison indicates that the average sales revenue for the store in FIVE POINTS PLAZA is lower than the average sales revenue for the stores across the entire country.",
            },
            "What were the sales during the 'Autumn/Winter' season for the store FIVE POINTS PLAZA?": {
                "sql": "SELECT dll.LatestLocation,SUM(f.NetSaleUSD) as TotalSales, d.Season, d.FiscalMonthName, d.FiscalYear \nFROM fact_Sale f JOIN dim_Calendar d ON f.CalendarKey = d.CalendarKey JOIN dim_Location_Latest dll ON f.LocationLatestKey =dll.LocationLatestKey WHERE d.Season = 'Autumn/Winter' AND f.LocationLatestKey = (SELECT LocationLatestKey FROM dim_Location_Latest dll WHERE dll.LatestLocation = 'FIVE POINTS PLAZA') GROUP BY d.FiscalMonthName, d.FiscalYear ORDER BY d.FiscalYear DESC, d.FiscalMonthName;",
                "nlr": "The data table returned indicates the sales figures for the 'Autumn/Winter' season at the store located in FIVE POINTS PLAZA. It shows two entries: the first entry reflects sales of $1,852.68 for the month of August in 2023, while the second entry reports sales of $8,446.11 for January in 2022. This information highlights the sales performance during the specified season across different months and years.",
            },
            "What is the average number of units sold per transaction at the store FIVE POINTS PLAZA?": {
                "sql": "SELECT AVG(f.TransactionCountTY) AS AverageUnitsSold FROM fact_Basket f\nJOIN dim_Location_Latest d ON f.LocationLatestKey = d.LocationLatestKey\nWHERE d.LatestLocation = 'FIVE POINTS PLAZA';",
                "nlr": "The data table returned indicates that the average number of units sold per transaction at the latest location of store FIVE POINTS PLAZA is approximately 27.02. This figure suggests that, on average, each transaction at this location involves the sale of just over 27 units.",
            },
        },
    }

    store_list = ["Store ID", "VILLAGE CROSSING", "THE PIKE OUTLETS", "FIVE POINTS PLAZA"]

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
            "VILLAGE CROSSING": "VILLAGE CROSSING",
            "THE PIKE OUTLETS": "THE PIKE OUTLETS",
            "FIVE POINTS PLAZA": "FIVE POINTS PLAZA"
        }.get(selected_store, "")

        store_name_id_placeholder.markdown(f"""
        <h4 style="background-color: {CLAIRE_MAUVE}; color: black; padding: 10px;">
            {store_name}
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
        if selected_query == f"Compare the average sales revenue for the store {store_name} with the average sales revenue for all stores in USA.":
            getDataTable = pd.read_sql(sql_query,conn)
            getDataTable = getDataTable.transpose()
            getDataTable.columns = [store_name, "Average for all stores in USA"]
            getDataTable = getDataTable
        else:
            getDataTable = pd.read_sql(sql_query, conn)
        st.dataframe(getDataTable,hide_index=True)

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
