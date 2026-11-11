# Search by meaning instead of by keyword

search_records matches a substring. It misses "cardiac" when the record says "heart". An embedding turns a text into a vector so that similar meanings land near each other, and search becomes "the five records nearest the question".

Most OpenAI-compatible endpoints also serve /v1/embeddings; ask the endpoint which embedding models it lists. The recipe: embed every record's title plus main_claim once and save the vectors next to the table; embed the query; rank by cosine similarity; return the top five records exactly as search_records does. Nothing in agent.py changes, which is the point: a tool's interface is strings in, string out, and the model does not care what is inside.

Keep the keyword tool too and give the agent both. Watch which one it picks for which question.
