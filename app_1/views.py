from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
from .models import *
from .model_loader import ModelContainer
from .serializer import *

# Create your views here.

def BOOK_DATA(request):
    books = list(Book.objects.values())
    print(books)

    return JsonResponse(books, safe=False)

def DATASET(request):
    titles = ['Knowledge', 'BGP Analysis Base', 'BGP Real Case Analysis', 'BGP Real-Time Analysis']
    return render(request, 'dataset.html', {'titles': titles})

# def BGP_LLaMA(request):
#     model_pipeline = ModelContainer.load_model()
#     # llm = HuggingFacePipeline(pipeline=model_pipeline)
    
#     queries = Userquery.objects.all().order_by('id')[:5]
    
#     query = request.GET['query']
#     print(f"\n{query}\n")
    
#     model_out = model_pipeline(query)
#     print(f"\n model output: {model_out}\n")
    
#     output = model_out[0]['generated_text']
    
#     print(f"\n parsing the output : {output}\n")
    
    
#     #saving the query and output to database
#     query_data = Userquery(
#         query=query,
#         reply=model_out
#     )
#     query_data.save() 
#     context = {
#         'queries':queries,
#         'query':query,
#         'output':output
#     }

#     return render(request, 'ai_page.html', context)

def BGP_LLaMA(request):
    if 'query' in request.GET:
        model_pipeline = ModelContainer.load_model()
        query = request.GET['query']
        
        model_out = model_pipeline(query)
        output = model_out[0]['generated_text']
        print(f"\n Model Output: {output}\n")
        # Saving the query and output to the database
        query_data = Userquery(query=query, reply=output)
        query_data.save()
        
        latest_queries = Userquery.objects.all().order_by('-id')[:5]
        queries_data = [{'query': q.query, 'reply': q.reply} for q in latest_queries]
        data = {'output': output, 'queries': queries_data}
        # data = {'output': 'some_output', 'queries': ['query1', 'query2']}
        print(f"\nRequest: {request.GET}\n")
        print(f"\nData: {data}\n")
        return JsonResponse(data)
    else:
        return JsonResponse({'error': 'No query provided'}, status=400)

def AI_PAGE(request):
    queries = Userquery.objects.all().order_by('-id')[:5]
    context = {
        "queries":queries
    }
    return render(request, 'ai_page.html', context)

def CHAT_PAGE(request):
    queries = Userquery.objects.all().order_by('-id')[:5]
    context = {
        "queries":queries
    }
    return render(request, 'ai_text_box.html', context)
