from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.core import serializers
import json
from .models import *
from .serializers import *

# 작성자 정보를 가져오기 위한 복호화 모듈
from rest_framework_simplejwt.tokens import AccessToken
from jwt import exceptions

# APIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404

from rest_framework.permissions import *

from config.permissions import IsProtected

# Create your views here.

def get_user_from_token(token):
    try:
        decoded_token = AccessToken(token, verify=False)
        user_id = decoded_token.payload["user_id"]
        return user_id
    except exceptions.DecodeError:
        return None

class imageView(APIView):
    
    def post(self, request):
        serializer = ImageSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({
                'status' : 200,
                'message' : '이미지 업로드 성공',
                'result' : serializer.data
            })
        else:
            return JsonResponse({
                'status' : 400,
                'message' : '유효하지 않은 데이터',
                'result' : None
            })

class get_recently_title(APIView):
    
    permission_classes = [IsAuthenticated]
    
    RECENT_POST_COUNT = 3
    
    def get(self, request):
        posts = Post.objects.all()
        post_list = []
        recent_modified_list = []

        for post in posts:
            title = post.title
            update_day = post.updated_at
            post_list.append([title, update_day])

        print(post_list)
        
        post_list.sort(key=lambda x : x[1], reverse=True)
        
        print(post_list)
        
        for i in range(self.RECENT_POST_COUNT):
            recent_modified_list.append(post_list[i][0])
            
        return JsonResponse({
            "status" : 200,
            "message" : "최신 수정 페이지 타이틀 조회 성공",
            "result" : recent_modified_list
        })    

class get_all_title(APIView):
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        posts = Post.objects.all()
        title_list = []

        for post in posts:
            title = post.title
            title_list.append(title)

        return JsonResponse({
            "status" : 200,
            "message" : "타이틀 조회 성공",
            "result" : title_list
        })    

class PostList(APIView):
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, format=None):
        user_id = get_user_from_token(request.META['HTTP_AUTHORIZATION'].split()[1])
        writer = get_object_or_404(Member, id=user_id)
        request.data["last_modified_by"] = writer.id
        
        serializer = PostSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({
                'status' : 200,
                'message' : '생성 성공',
                'result' : serializer.data,
                'wirter' : writer.username
            })
        else:
            return JsonResponse({
                'status' : 400,
                'message' : '유효하지 않은 데이터',
                'result' : None
            })

class PostDetail(APIView):
    
    permission_classes = [IsAuthenticated, IsProtected]
    
    def get_object(self, title):
        post = get_object_or_404(Post, title=title)
        self.check_object_permissions(self.request, post)
        return post
    
    def get(self, request, title):
        post = self.get_object(title = title)
        serializers = PostSerializer(post)
        
        member = get_object_or_404(Member, id=serializers.data['last_modified_by'])
        
        writer = member.username
        return JsonResponse({
            'status' : 200,
            'message' : '조회 성공',
            'result' : serializers.data,
            'writer' : writer
        })
    
    def patch(self, request, title):
        post = self.get_object(title = title)
        request.data["title"] = title
        
        user_id = get_user_from_token(request.META['HTTP_AUTHORIZATION'].split()[1])
        writer = get_object_or_404(Member, id=user_id) 
        request.data["last_modified_by"] = writer.id
        
        serializers = PostSerializer(post, data=request.data)
        if serializers.is_valid():
            serializers.save()
            return JsonResponse({
            'status' : 200,
            'message' : '수정 성공',
            'result' : serializers.data,
            'writer' : writer.username
        })
        else:
            return JsonResponse({
                'status' : 400,
                'message' : '유효하지 않은 데이터',
                'result' : None
            })
    
    def delete(self, request, title):
        post = self.get_object(title = title)
        post.delete()
        return JsonResponse({
            'status' : 200,
            'message' : '삭제 성공',
            'result' : None
        })
        
# 오류 처리
    
def handler404(request, exception):
    return JsonResponse({
        'status' : 404,
        'message' : '404 Not Found Error',
        'result' : None
    })