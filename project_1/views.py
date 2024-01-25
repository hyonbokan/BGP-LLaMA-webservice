from django.shortcuts import render, redirect

def INDEX(request):
    print('this is request pack',request.GET)
    return render(request, 'single_pjt.html')

def SINGLE(request):
    return render(request, 'single_page.html')

def ASSEMBLED(request):
    return render(request, 'assembled_page.html')

def PAGE_NOT_FOUND(request):
    return render(request, '404.html')
