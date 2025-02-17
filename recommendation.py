!pip install langchain
!pip install langchain_community

!pip install networkx
!pip install rdflib

import pandas as pd

import networkx as nx
import rdflib
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS

import requests
from langchain.llms.base import LLM
from typing import Optional, List, Mapping, Any

from langchain import PromptTemplate, LLMChain

df_movies = pd.read_csv('/content/tmdb_5000_movies.csv')

df_movies

df_credits = pd.read_csv('/content/tmdb_5000_credits.csv')

df_credits

df = pd.merge(df_movies, df_credits, on='title')

df

# Defining a namespace for the knowledge graph
movie_ns = Namespace("Movie_data/")

# Creating an RDF graph
graph = Graph()

# Iterating through the entire DataFrame and adding triples to the graph
for index, row in df.iterrows():
    movie_uri = movie_ns[str(row['title']).replace(" ", "_")]

    graph.add((movie_uri, RDF.type, movie_ns['Movie']))
    graph.add((movie_uri, movie_ns['title'], Literal(row['title'])))
    graph.add((movie_uri, movie_ns['release_date'], Literal(row['release_date'])))
    graph.add((movie_uri, movie_ns['overview'], Literal(row['overview'])))
    graph.add((movie_uri, movie_ns['popularity'], Literal(row['popularity'])))
    graph.add((movie_uri, movie_ns['genres'], Literal(row['genres'])))
    graph.add((movie_uri, movie_ns['production_companies'], Literal(row['production_companies'])))
    graph.add((movie_uri, movie_ns['spoken_languages'], Literal(row['spoken_languages'])))
    graph.add((movie_uri, movie_ns['keywords'], Literal(row['keywords'])))
    graph.add((movie_uri, movie_ns['cast'], Literal(row['cast'])))
    graph.add((movie_uri, movie_ns['crew'], Literal(row['crew'])))

# Converting the RDF graph to a NetworkX graph for visualization
nx_graph = nx.Graph()
for s, p, o in graph:
    nx_graph.add_edge(s, o, label=p)

# Create a list to store the triples
triples = []

# Iterate through the RDF graph and extract subject, predicate, and object
for s, p, o in graph:
    triples.append([s, p, o])

# Create a Pandas DataFrame from the triples
df_kg = pd.DataFrame(triples, columns=['Subject', 'Predicate', 'Object'])

# Export the DataFrame to a CSV file
df_kg.to_csv('knowledge_graph.csv', index=False)

def main_function(input_data):
  user_prompt = f'''
<|begin_of_text|><|start_header_id|>system<|end_header_id|>
<|eot_id|>
<|start_header_id|>user<|end_header_id|>

required_input: {input_data}
<|eot_id|>'''

  API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
  #API_URL = "https://api-inference.huggingface.co/models/google/gemma-7b-it"
  headers = {"Authorization": "Bearer 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"}

  def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

  output = query({
    "inputs": user_prompt,
    "parameters": {"return_full_text": False,
                   "max_new_tokens": 512}
  })
  return output[0]['generated_text']

class CustomLLM(LLM):

    @property
    def _llm_type(self) -> str:
        return "custom"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        response = main_function(prompt)
        return response

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {}

df_kg = pd.read_csv('/content/knowledge_graph.csv')

llm = CustomLLM()

def get_similar_movies(movie_title):
    # Define prompt template with embedded knowledge
    prompt_template = f"""
    Find movies similar to "{movie_title}" based on shared attributes like genre, keywords, cast, and crew.

    For example:
    * Movies with shared cast or crew members could also be considered similar.
    * Consider keywords associated with the movie to identify related themes and topics.

    Based on these criteria, suggest a few movies that are similar to "{movie_title}".
    """

    prompt = PromptTemplate(
        input_variables=["movie_title"],
        template=prompt_template,
    )

    chain = LLMChain(llm=llm, prompt=prompt)

    # Run the chain
    response = chain.run({"movie_title": movie_title})
    return response

# Example usage
movie_title = "The Avengers"
similar_movies = get_similar_movies(movie_title)
print(similar_movies)
