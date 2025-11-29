# from django.shortcuts import render
from django.http import HttpResponse
from django.views import View


class OutBoxMailList(View):

    def get(self, request):
        return HttpResponse("<h1>result<h1/>")
