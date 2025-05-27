examples = [
    {
        "input": "Write GMV, customers, qty, and customers split by business_unit for the first week of April",
        "query": """
        SELECT
            date,
            business_unit,
            SUM(gmv) AS gmv,
            SUM(qty) AS qty,
            COUNT(DISTINCT order_created_by) AS customers,
            COUNT(DISTINCT device_id) AS users
        FROM user_activity
        WHERE DATE_FORMAT(date, '%Y%m%d') BETWEEN '20250401' AND '20250407'
        GROUP BY date, business_unit;
        """
    },
    {
        "input": "Calculate GMV per session and per user across marketing channels for February 2025",
        "query": """
        WITH rev AS (
            SELECT date,
                   marketing_channel,
                   SUM(gmv) AS gmv
            FROM user_activity
            WHERE DATE_FORMAT(date, '%Y%m') = '202502'
            GROUP BY date, marketing_channel
        ),
        sess AS (
            SELECT date,
                   marketing_channel,
                   COUNT(DISTINCT session_id) AS sessions,
                   COUNT(DISTINCT device_id) AS users
            FROM user_activity
            WHERE DATE_FORMAT(date, '%Y%m') = '202502'
            GROUP BY date, marketing_channel
        )
        SELECT sess.date,
               sess.marketing_channel,
               gmv,
               sessions,
               users,
               gmv / sessions AS gmv_per_session,
               gmv / users AS gmv_per_user
        FROM sess
        LEFT JOIN rev ON rev.date = sess.date AND rev.marketing_channel = sess.marketing_channel;
        """
    },
    {
        "input": "Calculate qty per user across product premiumness for March 2025",
        "query": """
        WITH qty_data AS (
            SELECT date,
                   product_premiumness,
                   SUM(qty) AS total_qty
            FROM user_activity
            WHERE DATE_FORMAT(date, '%Y%m') = '202503'
            GROUP BY date, product_premiumness
        ),
        user_data AS (
            SELECT date,
                   COUNT(DISTINCT device_id) AS unique_users
            FROM user_activity
            WHERE DATE_FORMAT(date, '%Y%m') = '202503'
            GROUP BY date
        )
        SELECT qty_data.date,
               qty_data.product_premiumness,
               total_qty,
               unique_users,
               total_qty / unique_users AS qty_per_user
        FROM qty_data
        LEFT JOIN user_data ON qty_data.date = user_data.date;
        """
    },
    {
        "input": "Find top 3 brands by GMV, quantity sold, and user engagement for Q1 2025",
        "query": """
        SELECT
            brand,
            SUM(gmv) AS total_gmv,
            SUM(qty) AS total_qty,
            COUNT(DISTINCT device_id) AS users
        FROM user_activity
        WHERE DATE_FORMAT(date, '%Y%m') BETWEEN '202501' AND '202503'
        GROUP BY brand
        ORDER BY total_gmv DESC
        LIMIT 3;
        """
    },
    {
        "input": "Get total sessions, customers, and users across marketing channels for January 2025",
        "query": """
        WITH session_data AS (
            SELECT
                date,
                marketing_channel,
                COUNT(DISTINCT session_id) AS sessions
            FROM user_activity
            WHERE DATE_FORMAT(date, '%Y%m') = '202501'
            GROUP BY date, marketing_channel
        ),
        customer_data AS (
            SELECT
                date,
                marketing_channel,
                COUNT(DISTINCT order_created_by) AS customers,
                COUNT(DISTINCT device_id) AS users
            FROM user_activity
            WHERE DATE_FORMAT(date, '%Y%m') = '202501'
            GROUP BY date, marketing_channel
        )
        SELECT session_data.date,
               session_data.marketing_channel,
               sessions,
               customers,
               users
        FROM session_data
        LEFT JOIN customer_data ON session_data.date = customer_data.date AND session_data.marketing_channel = customer_data.marketing_channel;
        """
    },
    {
        "input": "Track daily GMV and add_to_cart across user journey with users for the last 15 days",
        "query": """
        WITH revenue AS (
            SELECT date,
                   journey,
                   SUM(gmv) AS gmv
            FROM user_activity
            WHERE date >= CURDATE() - INTERVAL 15 DAY
            GROUP BY date, journey
        ),
        cart_data AS (
            SELECT date,
                   journey,
                   SUM(add_to_cart) AS atc
            FROM user_activity
            WHERE date >= CURDATE() - INTERVAL 15 DAY
            GROUP BY date, journey
        ),
        user_data AS (
            SELECT date,
                   journey,
                   COUNT(DISTINCT device_id) AS users
            FROM user_activity
            WHERE date >= CURDATE() - INTERVAL 15 DAY
            GROUP BY date, journey
        )
        SELECT revenue.date,
               revenue.journey,
               gmv,
               atc,
               users
        FROM revenue
        LEFT JOIN cart_data ON revenue.date = cart_data.date AND revenue.journey = cart_data.journey
        LEFT JOIN user_data ON revenue.date = user_data.date AND revenue.journey = user_data.journey;
        """
    },
    {
        "input": "Calculate sessions per user for Q2 2025",
        "query": """
        WITH sessions AS (
            SELECT date,
                   COUNT(DISTINCT session_id) AS total_sessions
            FROM user_activity
            WHERE DATE_FORMAT(date, '%Y%m') BETWEEN '202504' AND '202506'
            GROUP BY date
        ),
        users AS (
            SELECT date,
                   COUNT(DISTINCT device_id) AS unique_users
            FROM user_activity
            WHERE DATE_FORMAT(date, '%Y%m') BETWEEN '202504' AND '202506'
            GROUP BY date
        )
        SELECT sessions.date,
               total_sessions,
               unique_users,
               total_sessions / unique_users AS sessions_per_user
        FROM sessions
        LEFT JOIN users ON sessions.date = users.date;
        """
    },
    {
        "input": "Calculate revenue per user for the last 30 days",
        "query": """
        WITH revenue AS (
            SELECT date,
                   SUM(gmv) AS total_gmv
            FROM user_activity
            WHERE date >= CURDATE() - INTERVAL 30 DAY
            GROUP BY date
        ),
        users AS (
            SELECT date,
                   COUNT(DISTINCT device_id) AS unique_users
            FROM user_activity
            WHERE date >= CURDATE() - INTERVAL 30 DAY
            GROUP BY date
        )
        SELECT revenue.date,
               total_gmv,
               unique_users,
               total_gmv / unique_users AS revenue_per_user
        FROM revenue
        LEFT JOIN users ON revenue.date = users.date;
        """
    }
]


from langchain.prompts.example_selector import SemanticSimilarityExampleSelector
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
import streamlit as st
example_selector = SemanticSimilarityExampleSelector.from_examples(
        examples,
        OpenAIEmbeddings(),
        Chroma,
        k=2,
        input_keys=["input"],
    )
@st.cache_resource
def get_example_selector():
   
    return example_selector