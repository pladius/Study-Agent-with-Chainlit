from datetime import date, timedelta
import chainlit as cl
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_groq import ChatGroq
from langchain_community.utilities import WikipediaAPIWrapper
from groq import Groq

import os
os.environ["GROQ_API_KEY"] = ""

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)
llm = ChatGroq(
    model_name="openai/gpt-oss-20b",
    temperature=0.0
)



wikipedia = WikipediaAPIWrapper()
@tool
def wikipedia_search (query:str) -> str:
  """Search Wikipedia to explain a topic, concept, person or even the student wants to learn."""
  try:
    return wikipedia.run(query)
  except Exception:
    return Exception


today = date.today()
exam_datesheet = {
    "math" : today + timedelta(days=5),
    "science": today + timedelta (days=9),
    "english":today + timedelta (days = 12),
    "computer science": today + timedelta (days = 15)
}


@tool
def get_exam_info (subject : str) -> str:
  """Get the exam date and the number of days left for a school subject. Use this when the student asks anything about his exam."""
  subject = subject.lower ()
  if subject in exam_datesheet:
    exam_date = exam_datesheet [subject]
    days_left = (exam_date - today).days
    return f"{subject.title()} exam is on {exam_date.strftime("%A %d %B")}, which is {days_left} days from today {today}"


agent = create_agent (
    model = llm,
    tools = [wikipedia_search,get_exam_info],
    system_prompt = """
    You are a Study Buddy, a friendly assistant for school students.
    Rules:
    1. Whenever a student asks about an exam date, exam schedule,
    or days remaining until an exam, ALWAYS use get_exam_info.
    2. Whenever a student asks to learn about a topic, use wikipedia_search
    when external information is needed.
    3. Answer the student's questions clearly and simply.
    4. If a question contains multiple requests, answer all of them.
    """
)
@cl.on_chat_start
async def main():
    cl.user_session.set ("history",[])

@cl.on_message
async def on_message (message: cl.message):
    history = cl.user_session.get("history",[])
    response = agent.invoke(
        {"messages": history + [
            {"role": "user", "content": message.content}
        ]}
    )
    answer = response ["messages"][-1].content
    await cl.Message (content = answer).send()

    history.append({"role": "user", "content": message.content})
    history.append({"role": "assistant", "content": answer})

    cl.user_session.set("history", history)
    print (history)
