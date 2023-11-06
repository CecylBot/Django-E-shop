from elasticsearch_dsl import Q
from ..models import *
import re
def results(query):
    
    if "tshirt" in query:
        query = re.sub(r'tshirt', 't-shirt', query, flags=re.IGNORECASE)
    # Tokenize the query into individual words
    print(query)
    tokens = query.split()

    # Create a query that matches any of the tokens in the name or keywords fields
    search_query = Q()
    for i, token in enumerate(tokens):
        for j, other_token in enumerate(tokens):
            if i != j:
                search_query |= (Q(name__icontains=token) & Q(category__name__icontains=other_token))
    results = Products.objects.filter(search_query)
    if len(results)==0:
        for token in tokens:
            search_query |= Q(name__icontains=token)
        results = Products.objects.filter(search_query)
    # Perform the search
   
    
    return results

