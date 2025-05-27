import os
from dotenv import load_dotenv

load_dotenv()

db_user = os.getenv("db_user")
db_password = os.getenv("db_password")
db_host = os.getenv("db_host")
db_name = os.getenv("db_name")


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")

from langchain_community.utilities.sql_database import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_openai import ChatOpenAI
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain.memory import ChatMessageHistory

from operator import itemgetter
from sqlalchemy import create_engine, inspect


from langchain_core.output_parsers import StrOutputParser

from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from table_details import table_chain as select_table
from prompts import final_prompt, answer_prompt

import streamlit as st
# @st.cache_resource
# def get_chain():
#     print("Creating chain")
#     db = SQLDatabase.from_uri(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}")    
#     llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
#     print('llm')
#     generate_query = create_sql_query_chain(llm, db,final_prompt) 
#     execute_query = QuerySQLDataBaseTool(db=db)
#     print('execute_query')
#     rephrase_answer = answer_prompt | llm | StrOutputParser()
#     # chain = generate_query | execute_query
#     chain = (
#     # RunnablePassthrough.assign(table_names_to_use=select_table) |
#     RunnablePassthrough.assign(query=generate_query).assign(
#         result=itemgetter("query") | execute_query
#     )
#     | rephrase_answer
# )

#     return chain

# def create_history(messages):
#     history = ChatMessageHistory()
#     for message in messages:
#         if message["role"] == "user":
#             history.add_user_message(message["content"])
#         else:
#             history.add_ai_message(message["content"])
#     return history

# def invoke_chain(question,messages):
#     chain = get_chain()
#     history = create_history(messages)
#     response = chain.invoke({"question": question,"top_k":3,"messages":history.messages})
#     history.add_user_message(question)
#     history.add_ai_message(response)
#     return response

# @st.cache_resource
def get_chain():
    try:
        print("Initializing SQL Database connection...")
        db = SQLDatabase.from_uri(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
                                   )
        
        engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}")

        # Use Inspector to get table names
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        print(table_names)

        print("Database connection established.")

        print("Initializing LLM...")
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        print("LLM initialized.")

        print("Creating query generation chain...")
        generate_query = create_sql_query_chain(llm, db, final_prompt)
        
        print("Initializing Query Execution Tool...")
        execute_query = QuerySQLDataBaseTool(db=db, include_tables=["user_activity"])

        print("Creating rephrase answer chain...")
        rephrase_answer = answer_prompt | llm | StrOutputParser()

        print("Building final chain...")
        chain = (
            # RunnablePassthrough.assign(table_names_to_use=select_table) |
            RunnablePassthrough.assign(query=generate_query).assign(
                result=itemgetter("query") | execute_query
            )
            | rephrase_answer
        )

        print("Chain successfully created.")
        
        
        return chain
    except Exception as e:
        print(f"Error in get_chain: {e}")
        return None  # Return None if an error occurs

def create_history(messages):
    try:
        print(f"Creating history from messages: {messages}")
        history = ChatMessageHistory()
        
        if not messages:
            print("Warning: No messages provided, history will be empty.")

        for message in messages:
            if message["role"] == "user":
                history.add_user_message(message["content"])
            else:
                history.add_ai_message(message["content"])
                
        print("Chat history created.")
        return history
    except Exception as e:
        print(f"Error in create_history: {e}")
        return None  # Return None if an error occurs

def invoke_chain(question, messages):
    try:
        print(f"Invoking chain with question: {question}")
        
        chain = get_chain()
        # print('printing chain')
        # print(chain)
        if chain is None:
            print("Error: Chain creation failed.")
            return "Error: Could not initialize chain."

        history = create_history(messages)
        if history is None:
            print("Error: Failed to create message history.")
            return "Error: Could not initialize chat history."

        print("Invoking chain with parameters...")
        response = chain.invoke({
    "question": question, 
    "messages": history.messages, 
    "table_names": ["user_activity"]
        })

        print(history.messages)
        
        print(f"Response received: {response}")

        history.add_user_message(question)
        history.add_ai_message(response)
        
        print('-------------------------------------')

        return response
    except Exception as e:
        print(f"Error in invoke_chain: {e}")
        return f"Error: {str(e)}"

