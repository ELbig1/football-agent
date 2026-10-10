"""
Agentic Loop: Groq + Tools
============================
الملف ده فيه المنطق العام للـ agent بس (الحلقة اللي بتكلم Groq،
بتاخد قراره، بتنفذ الأداة، وبترجعله النتيجة). كل تفاصيل أدوات
الكورة نفسها موجودة في football_tools.py.

لو عايز تعمل agent لموضوع تاني، تقدر تعمل ملف زي football_tools.py
(مثلاً crypto_tools.py) وتغيّر الـ import بس من غير ما تلمس الملف ده.
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI

from football_tools import TOOLS, TOOL_EXECUTORS

load_dotenv()

groq_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

MODEL_NAME = "qwen/qwen3.8-27b"


SYSTEM_PROMPT = (
    """You are a football (soccer) assistant. 
    Always answer in English, direct and concise, no extra suggestions 
    or side information - answer exactly what was asked. 
    Exception: if the user's message is just a greeting (e.g. 'السلام 
    عليكم', 'hi', 'hello') with no actual football question in it, 
    reply to the greeting in the same language they greeted in. 
    You have 4 tools: 
    calculate_standings to compute points and standings from match 
    results, days_until_match to count days until a known date, 
    get_next_match to find a team's next upcoming fixture (when the 
    user asks when a team plays next but no date is given), and 
    get_match_result to find a team's most recent result. 
    If the user asks about an upcoming match and wants to know how 
    many days are left, call get_next_match first to get the date, 
    then days_until_match to compute the countdown. 
    If a team isn't found in the database, say so clearly. 
    Don't call the same tool more than twice for the same purpose."""
)


def run_agent(
    user_message: str,
    verbose: bool = True,
    max_iterations: int = 4,
    on_step=None,
    conversation_history: list | None = None,
):
    """
    max_iterations: أقصى عدد مرات ممكن الموديل يطلب فيها أداة قبل ما نوقفه
    بالإجابة اللي وصل لها لحد دلوقتي.

    on_step: دالة اختيارية بتتنادى مع كل خطوة (dict فيها "type" و"data")
    عشان أي واجهة (زي Streamlit) تقدر تعرض تقدم الـ agent لايف.

    conversation_history: قايمة بالأسئلة والإجابات اللي فاتت في نفس
    المحادثة (كل عنصر {"role": "user"/"assistant", "content": ...})
    عشان السؤال الجديد "يفتكر" اللي اتكلمنا عنه قبل كده. لو من غير
    كده (None)، الـ agent بيتعامل مع السؤال كأنه أول مرة.

    الدالة بترجع tuple: (الإجابة، تاريخ المحادثة المحدّث) - خزّن
    التاريخ المحدّث ده وابعته تاني في المرة الجاية.
    """
    if conversation_history is None:
        conversation_history = []

    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + conversation_history
        + [{"role": "user", "content": user_message}]
    )

    def emit(step_type: str, **data):
        if on_step:
            on_step({"type": step_type, **data})

    def finish(answer: str):
        updated_history = conversation_history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": answer},
        ]
        return answer, updated_history

    for iteration in range(max_iterations):
        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOLS,
        )
        choice = response.choices[0]
        message = choice.message

        if not message.tool_calls:
            emit("final_answer", content=message.content)
            return finish(message.content)

        messages.append(message.model_dump(exclude_none=True))

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            if verbose:
                print(f"🤖 Groq decided to call: {tool_name}({args})")
            emit("tool_call", tool_name=tool_name, args=args, iteration=iteration + 1)

            executor = TOOL_EXECUTORS.get(tool_name)
            if executor:
                tool_output = executor(args)
            else:
                tool_output = f"أداة غير معروفة: {tool_name}"

            emit("tool_result", tool_name=tool_name, content=tool_output)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_output,
                }
            )

    if verbose:
        print(f"⚠️ وصلنا لأقصى عدد محاولات ({max_iterations})، هطلب إجابة نهائية بس")
    emit("max_iterations_reached", max_iterations=max_iterations)

    final_response = groq_client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages + [
            {
                "role": "user",
                "content": "لخّص أفضل إجابة ممكنة من المعلومات اللي عندك دلوقتي، من غير ما تطلب أداة تانية.",
            }
        ],
    )
    final_answer = final_response.choices[0].message.content
    emit("final_answer", content=final_answer)
    return finish(final_answer)


if __name__ == "__main__":
    test_queries = [
        "احسبلي ترتيب الأهلي والزمالك: الأهلي فاز 5 مرات وتعادل مرتين وخسر مرة، سجل 15 هدف واستقبل 5. الزمالك فاز 4 مرات وتعادل 3 وخسر مرة، سجل 12 هدف واستقبل 6",
        "امتى مباراة Al Ahly الجاية؟",
        "إيه آخر نتيجة لـ Zamalek؟",
    ]

    query = test_queries[1]
    print(f"\n📝 السؤال: {query}\n" + "-" * 60)
    answer, history = run_agent(query)
    print("\n✅ الإجابة النهائية:\n" + answer)