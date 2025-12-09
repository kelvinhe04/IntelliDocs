import pickle
import os
import faiss
import numpy as np
from vector_store import VectorStore
from embeddings import EmbeddingGenerator

print("Loading VectorStore...")
vs = VectorStore()
print(f"Index total: {vs.index.ntotal}")
print(f"Metadata len: {len(vs.metadata)}")

if vs.index.ntotal != len(vs.metadata):
    print("CRITICAL WARNING: Index and Metadata size mismatch!")

print("\n--- Testing Search for 'Kelvin' ---")
embedder = EmbeddingGenerator()
query_vec = embedder.generate("Kelvin")
results = vs.search(query_vec, k=10)

print(f"Found {len(results)} results:")
for r in results:
    meta = r['metadata']
    print(f" - {meta['filename']} (Score: {r['distance']:.4f})")

print("\n--- Inspecting Index 22 (CV) ---")
if len(vs.metadata) > 22:
    m = vs.metadata[22]
    print(f"Filename: {m['filename']}")
    print(f"Summary: {m.get('summary', 'NO SUMMARY')}")
    print(f"Path: {m['path']}")
else:
    print("Index 22 not found")

