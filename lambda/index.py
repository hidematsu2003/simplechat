# lambda/index.py
import json
import os
import re
import requests  # ← ここを追加（requestsモジュールで外部APIアクセス）
from botocore.exceptions import ClientError

# 外部エンドポイント（FastAPI公開サーバー）
FASTAPI_ENDPOINT = "https://27d5-34-125-177-143.ngrok-free.app/"

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))
        
        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")
        
        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])
        
        print("Processing message:", message)
        
        # 会話履歴を使用
        messages = conversation_history.copy()
        
        # ユーザーメッセージを追加
        messages.append({
            "role": "user",
            "content": message
        })
        
        # 外部API（FastAPIサーバー）にリクエスト送信
        request_payload = {
            "message": message,
            "conversationHistory": conversation_history
        }
        
        print("Calling FastAPI endpoint with payload:", json.dumps(request_payload))
        
        response = requests.post(FASTAPI_ENDPOINT, json=request_payload)
        response.raise_for_status()  # 失敗時は例外を投げる
        
        response_body = response.json()
        print("FastAPI response:", json.dumps(response_body, default=str))
        
        if not response_body.get('success'):
            raise Exception(f"FastAPI returned error: {response_body.get('error')}")
        
        assistant_response = response_body['response']
        updated_conversation_history = response_body['conversationHistory']
        
        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": updated_conversation_history
            })
        }
        
    except Exception as error:
        print("Error:", str(error))
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
