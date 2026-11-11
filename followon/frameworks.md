# The same agent in a framework

agent.py is forty lines. Frameworks such as LangChain, LlamaIndex, the OpenAI Agents SDK, and Pydantic AI offer the same loop with more features: streaming, memory, retries, tracing, many tool formats. They are worth it when you need those features, and the way to find out is to rebuild Module 4 in one of them and compare.

What to look at: how many lines; how a tool is declared and whether the docstring still does the work; what happens on a tool error; whether you can read the full exchange as plainly as trace.json; and how hard it is to point the whole thing at a different endpoint. Then write down what you got and what you gave up. The question is never which is better; it is which you can still see inside of when it misbehaves at 2 a.m.
