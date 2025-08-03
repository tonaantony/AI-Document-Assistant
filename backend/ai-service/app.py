from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import numpy as np
import faiss
import os

app = Flask(__name__)

# Configure your Gemini API key
api_key=os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise EnvironmentError("GOOGLE_API_KEY not found")
genai.configure(api_key=api_key)
# genai.configure(api_key="")  # Replace with your actual key

# Load embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")  # 384-dim vectors

# FAISS index
index = faiss.IndexFlatL2(384)
doc_chunks = []

@app.route('/embed', methods=['POST'])
def embed():
    text = request.form['text']
    chunks = [chunk.strip() for chunk in text.split('.') if chunk.strip()]
    embeddings = embedder.encode(chunks)

    global doc_chunks
    doc_chunks = chunks
    index.reset()
    index.add(np.array(embeddings).astype('float32'))

    return jsonify({"status": "ok", "chunks": len(chunks)})

@app.route('/query', methods=['GET'])
def query():
    q = request.args.get('q')
    if not q:
        return jsonify({"error": "Missing query param 'q'"}), 400

    # Find top chunks
    q_embed = embedder.encode([q]).astype('float32')
    D, I = index.search(q_embed, k=3)
    top_chunks = [doc_chunks[i] for i in I[0]]
    context = "\n".join(top_chunks)

    # Create Gemini prompt
    prompt = f"""You are an assistant helping analyze coding test papers.

Use the following context to answer the question clearly.

Context:
{context}

Question:
{q}

Answer:"""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        answer = response.text.strip()
    except Exception as e:
        return jsonify({"error": "Gemini API call failed", "details": str(e)}), 500

    return jsonify({
        "answer": answer,
        "context": context,
        "model": "gemini-1.5-flash"
    })

if __name__ == '__main__':
    app.run(debug=True)
