```cmd 
docker run -p 6333:6333 -v $(pwd)/qdrant_data:/qdrant/storage qdrant/qdrant
```

| Approach                                                  | How it works                                                                                                                                                                                                                                                                                      | When it shines                                                                                                                                                            | Caveats                                                                                                                                                                                  |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Prompt-only (“copy-paste”)**                            | Put the most relevant rule excerpts directly into the *system* or *user* prompt every time you ask a question.                                                                                                                                                                                    | Small rulebooks (a few thousand tokens) and infrequent queries.  Zero setup cost.                                                                                         | Limited by context window; you must remember to paste the right passages every time; can get expensive if the text is large.                                                             |
| **Retrieval-Augmented Generation (RAG)**                  | 1) Split rules into chunks (e.g. 200-400 words). 2) Embed chunks with a model (e.g. `text-embedding-3-small`). 3) Store embeddings in a vector DB (Pinecone, Weaviate, FAISS, etc.). 4) At query time, retrieve the 3-5 most relevant chunks and insert them into the prompt before the question. | Medium-to-large rulebooks (tens or hundreds of pages) that are updated occasionally.  Keeps prompts short and automatically brings in only the rules that matter.         | Requires some engineering: chunking, embedding, hosting a vector store, and a retrieval pipeline.  The model hasn’t *memorized* the rules; if retrieval fails, it can still hallucinate. |
| **Fine-tuning**                                           | Create a training set of **scenario → correct ruling** pairs (and optional rationales).  Fine-tune an existing model (OpenAI, Mistral, Llama-3, etc.) on those pairs so the weights encode typical decisions.                                                                                     | When you have lots of adjudication examples (hundreds+) and the rulings follow consistent patterns.  After training, inference is fast and you don’t need a vector store. | Model can’t store an entire rulebook word-for-word; if rules change you must re-train.  Needs careful data curation and can still hallucinate rule citations.                            |
| **Hybrid: RAG + Fine-tune**                               | Fine-tune the model on *how* to reason about rulings, while RAG injects the *authoritative text*.                                                                                                                                                                                                 | Large or evolving rulebooks where you also want the model to explain itself with direct quotes.                                                                           | More moving parts (training + retrieval + orchestration).                                                                                                                                |
| **External rule engine / function calling**               | Encode core rules (or edge-case tables) in a deterministic program or API.  Let the LLM “decide” whether to call the function and then translate the result into natural language.                                                                                                                | When certain calculations must be 100 % correct (e.g. combat math).  Combines symbolic exactness with LLM fluency.                                                        | You must implement & host the rule engine and expose a schema the model can call.                                                                                                        |
| **Knowledge graph or JSON rules with structured queries** | Turn rules into triplets or JSON objects (subject/action/condition/effect).  LLM crafts a query; back-end returns matching rules; LLM explains verdict.                                                                                                                                           | Highly formal rulebooks or when you want explainability with citations.                                                                                                   | Up-front cost to structure the knowledge; retrieval quality depends on schema design.                                                                                                    |



Prompt to use
You are answering as a Level-3 Magic : The Gathering judge whose goal is 100 % Comprehensive-Rules accuracy.

Obligations  
1. **Primary source** – treat the most recent Comprehensive Rules (CR) and Oracle text as authoritative.  
2. **Cite precisely** – whenever you rely on a rule, cite it in “CR ###.###” form. Quote verbatim only the clauses you need.  
3. **Stack & priority** – for timing or interaction questions, lay out the exact priority sequence (117.3–117.5) and the stack order (601, 608).  
4. **Step-by-step** – give numbered steps that mirror the game’s turn/phase structure where relevant.  
5. **Card texts** – reproduce any referenced Oracle text in full before analysing it.  
6. **Minimise speculation** – if information is missing, list the assumptions you must make; if multiple outcomes exist, analyse each separately.  
7. **No house rules** – answer strictly under sanctioned tournament rules (unless the user explicitly says otherwise).  
8. **Conciseness** – once the ruling is clear, stop. Avoid flavour, anecdotes and unrelated strategy tips.  
9. **Uncertainty** – if a new set or rules update released after June 8 2025 might change the outcome, say so plainly.  
10. **Formatting** – use:  

   • *Italic* for card names  
   • **Bold** for headings (“Step 1 – Cast the spell”)  
   • `CR 608.2b` inline for rule codes  
   • Bullet lists only for parallel possibilities; otherwise numbered lists.

Output template  
────────────────
**Oracle text** (only the cards involved)

**Ruling**  
Step 1 – …  
Step 2 – …

**Key rules cited**  
• CR ###.### – «quoted sentence»  
• CR ###.### – «quoted sentence»

**Result** (one-sentence bottom line)
────────────────

Now analyse the following scenario:
[PASTE THE ACTUAL QUESTION HERE]
