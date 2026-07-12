import os
import json
import zipfile
import io
import re
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_file, session, redirect, url_for
from werkzeug.utils import secure_filename
import requests
import base64
import hashlib
import hmac
import time
import secrets

app = Flask(__name__)
app.secret_key = 'nima_dev_ai_super_secret_key_2026'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

# ===== YOUR API KEY =====
OPENROUTER_API_KEY = "sk-c0c35c4c5024457aa36bd912c2e92747"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

os.makedirs('temp_uploads', exist_ok=True)

# ============ HTML TEMPLATE ============
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NIMA DEV AI - Ultimate Assistant</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0e1a;
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            color: #e0e0e0;
        }
        
        /* Login */
        .login-page {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
            background: #0a0e1a;
            position: relative;
            overflow: hidden;
        }
        .login-page::before {
            content: '';
            position: absolute;
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(0,150,255,0.05), transparent 70%);
            top: -200px;
            right: -200px;
            border-radius: 50%;
        }
        .login-page::after {
            content: '';
            position: absolute;
            width: 500px;
            height: 500px;
            background: radial-gradient(circle, rgba(123,47,252,0.05), transparent 70%);
            bottom: -200px;
            left: -200px;
            border-radius: 50%;
        }
        .login-card {
            background: rgba(15, 20, 45, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 30px;
            padding: 50px 45px;
            max-width: 440px;
            width: 100%;
            border: 1px solid rgba(0, 150, 255, 0.1);
            box-shadow: 0 40px 100px rgba(0, 0, 0, 0.6);
            text-align: center;
            position: relative;
            z-index: 1;
        }
        .login-card .logo {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #00d4ff, #7b2ffc);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
            margin: 0 auto 20px;
            box-shadow: 0 0 60px rgba(0, 150, 255, 0.2);
        }
        .login-card h1 {
            font-size: 28px;
            font-weight: 900;
            background: linear-gradient(135deg, #00d4ff, #7b2ffc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .login-card p {
            color: rgba(255,255,255,0.3);
            font-size: 14px;
            margin: 5px 0 20px;
        }
        .login-card .features-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            margin-bottom: 25px;
        }
        .login-card .features-grid .tag {
            font-size: 11px;
            color: rgba(255,255,255,0.2);
            background: rgba(255,255,255,0.03);
            padding: 6px 8px;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.03);
            text-align: center;
        }
        
        /* Gmail Login Button */
        .gmail-btn {
            width: 100%;
            padding: 15px;
            background: #ffffff;
            border: none;
            border-radius: 14px;
            color: #1a1a2e;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            margin-top: 8px;
        }
        .gmail-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(255,255,255,0.15);
        }
        .gmail-btn i {
            font-size: 22px;
        }
        .gmail-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .divider {
            display: flex;
            align-items: center;
            margin: 20px 0;
            color: rgba(255,255,255,0.1);
            font-size: 12px;
        }
        .divider::before, .divider::after {
            content: '';
            flex: 1;
            height: 1px;
            background: rgba(255,255,255,0.05);
        }
        .divider::before { margin-right: 15px; }
        .divider::after { margin-left: 15px; }
        
        /* Email Input */
        .login-card .input-group {
            position: relative;
            margin-bottom: 12px;
        }
        .login-card .input-group i {
            position: absolute;
            left: 16px;
            top: 50%;
            transform: translateY(-50%);
            color: rgba(255,255,255,0.15);
            font-size: 16px;
        }
        .login-card input {
            width: 100%;
            padding: 15px 20px 15px 48px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 14px;
            color: #fff;
            font-size: 15px;
            outline: none;
            transition: all 0.3s ease;
        }
        .login-card input:focus {
            border-color: rgba(0, 150, 255, 0.3);
            background: rgba(255,255,255,0.07);
        }
        .login-card input::placeholder {
            color: rgba(255,255,255,0.2);
        }
        .login-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #00d4ff, #7b2ffc);
            border: none;
            border-radius: 14px;
            color: #fff;
            font-size: 17px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 8px;
        }
        .login-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 0 50px rgba(0, 150, 255, 0.3);
        }
        .login-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        .login-error {
            color: #ff4060;
            font-size: 13px;
            margin-top: 10px;
            display: none;
            background: rgba(255,0,64,0.05);
            padding: 10px;
            border-radius: 10px;
            border: 1px solid rgba(255,0,64,0.1);
        }
        .login-error.show { display: block; }
        .login-success {
            color: #00ff88;
            font-size: 13px;
            margin-top: 10px;
            display: none;
            background: rgba(0,255,136,0.05);
            padding: 10px;
            border-radius: 10px;
            border: 1px solid rgba(0,255,136,0.1);
        }
        .login-success.show { display: block; }
        
        /* App */
        .app-container { display: none; height: 100vh; width: 100%; background: #0a0e1a; }
        .app-container.active { display: flex; }
        
        /* Sidebar */
        .sidebar {
            width: 280px;
            background: rgba(12, 16, 35, 0.98);
            border-right: 1px solid rgba(255,255,255,0.04);
            padding: 20px;
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }
        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: 14px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.04);
            margin-bottom: 20px;
        }
        .sidebar-brand .logo {
            width: 42px;
            height: 42px;
            background: linear-gradient(135deg, #00d4ff, #7b2ffc);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            color: #fff;
            box-shadow: 0 0 30px rgba(0, 150, 255, 0.15);
        }
        .sidebar-brand h2 {
            font-size: 20px;
            font-weight: 800;
            background: linear-gradient(135deg, #00d4ff, #7b2ffc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.2;
        }
        .sidebar-brand small {
            font-size: 9px;
            color: rgba(255,255,255,0.15);
            text-transform: uppercase;
            letter-spacing: 3px;
            display: block;
        }
        
        .sidebar-nav { flex: 1; overflow-y: auto; }
        .sidebar-nav .nav-item {
            padding: 13px 18px;
            border-radius: 12px;
            color: rgba(255,255,255,0.4);
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 14px;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 2px;
        }
        .sidebar-nav .nav-item:hover {
            background: rgba(255,255,255,0.04);
            color: #fff;
        }
        .sidebar-nav .nav-item.active {
            background: rgba(0, 150, 255, 0.08);
            color: #00d4ff;
        }
        .sidebar-nav .nav-item i { width: 22px; text-align: center; font-size: 16px; }
        .sidebar-nav .nav-item .badge {
            margin-left: auto;
            font-size: 9px;
            background: rgba(0,150,255,0.1);
            padding: 2px 10px;
            border-radius: 20px;
            color: rgba(255,255,255,0.2);
        }
        
        .sidebar-user {
            padding-top: 16px;
            border-top: 1px solid rgba(255,255,255,0.04);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .sidebar-user .user-info { display: flex; align-items: center; gap: 12px; }
        .sidebar-user .avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: linear-gradient(135deg, #00d4ff, #7b2ffc);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-weight: 700;
            font-size: 14px;
            box-shadow: 0 0 20px rgba(0, 150, 255, 0.1);
        }
        .sidebar-user .user-email {
            color: #e0e0e0;
            font-size: 13px;
            font-weight: 500;
            max-width: 120px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .sidebar-user .logout-btn {
            background: none;
            border: none;
            color: rgba(255,255,255,0.2);
            cursor: pointer;
            font-size: 18px;
            transition: all 0.3s ease;
            padding: 5px;
        }
        .sidebar-user .logout-btn:hover { color: #ff0040; }
        
        /* Main */
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: #0d1225;
            overflow: hidden;
        }
        .chat-header {
            padding: 18px 35px;
            border-bottom: 1px solid rgba(255,255,255,0.04);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(10, 14, 26, 0.8);
        }
        .chat-header h3 {
            font-size: 17px;
            font-weight: 600;
            color: #e8e8e8;
        }
        .chat-header .status {
            display: flex;
            align-items: center;
            gap: 10px;
            color: rgba(255,255,255,0.25);
            font-size: 12px;
        }
        .chat-header .status .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #00ff88;
            animation: blink 1.5s ease-in-out infinite;
            box-shadow: 0 0 15px rgba(0,255,136,0.2);
        }
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.2; }
        }
        
        .page-content { flex: 1; overflow: hidden; display: flex; flex-direction: column; }
        .page { display: none; flex: 1; flex-direction: column; height: 100%; }
        .page.active { display: flex; }
        
        /* Chat Messages */
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 30px 40px;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }
        .chat-messages .msg {
            display: flex;
            gap: 16px;
            max-width: 88%;
            animation: fadeIn 0.4s ease;
        }
        .chat-messages .msg.user {
            align-self: flex-end;
            flex-direction: row-reverse;
        }
        .chat-messages .msg .avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            flex-shrink: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            font-weight: 700;
        }
        .chat-messages .msg.user .avatar {
            background: linear-gradient(135deg, #00d4ff, #7b2ffc);
            color: #fff;
            box-shadow: 0 0 25px rgba(0, 150, 255, 0.15);
        }
        .chat-messages .msg.bot .avatar {
            background: rgba(255,255,255,0.05);
            color: #7b2ffc;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .chat-messages .msg .content {
            padding: 16px 22px;
            border-radius: 18px;
            font-size: 15px;
            line-height: 1.8;
            white-space: pre-wrap;
            word-wrap: break-word;
            max-width: 100%;
        }
        .chat-messages .msg.user .content {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(123, 47, 252, 0.1));
            border: 1px solid rgba(0, 150, 255, 0.06);
            color: #c8e0ff;
        }
        .chat-messages .msg.bot .content {
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.04);
            color: #e8e8e8;
        }
        .chat-messages .msg .content pre {
            background: rgba(0,0,0,0.5);
            padding: 16px;
            border-radius: 12px;
            overflow-x: auto;
            font-size: 13px;
            margin: 10px 0;
            border: 1px solid rgba(255,255,255,0.04);
            color: #d4d4d4;
            font-family: 'Courier New', monospace;
        }
        .chat-messages .msg .content code {
            background: rgba(0,0,0,0.3);
            padding: 2px 10px;
            border-radius: 6px;
            font-size: 13px;
            font-family: 'Courier New', monospace;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .typing-indicator {
            display: none;
            align-self: flex-start;
            gap: 14px;
            padding: 14px 22px;
            background: rgba(255,255,255,0.02);
            border-radius: 18px;
            border: 1px solid rgba(255,255,255,0.04);
            margin: 0 40px 10px 40px;
            align-items: center;
        }
        .typing-indicator.active { display: flex; }
        .typing-indicator .dots { display: flex; gap: 5px; align-items: center; }
        .typing-indicator .dots span {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #00d4ff;
            animation: typingAnim 1.4s ease-in-out infinite;
        }
        .typing-indicator .dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator .dots span:nth-child(3) { animation-delay: 0.4s; }
        .typing-indicator .label {
            color: rgba(255,255,255,0.2);
            font-size: 13px;
            font-weight: 500;
        }
        @keyframes typingAnim {
            0%, 60%, 100% { transform: translateY(0); opacity: 0.3; }
            30% { transform: translateY(-8px); opacity: 1; }
        }
        
        .chat-input-area {
            padding: 18px 35px 28px;
            border-top: 1px solid rgba(255,255,255,0.04);
            display: flex;
            gap: 14px;
            background: rgba(10, 14, 26, 0.8);
        }
        .chat-input-area input {
            flex: 1;
            padding: 15px 22px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 16px;
            color: #fff;
            font-size: 15px;
            outline: none;
            transition: all 0.3s ease;
        }
        .chat-input-area input:focus {
            border-color: rgba(0, 150, 255, 0.2);
            background: rgba(255,255,255,0.06);
        }
        .chat-input-area input::placeholder {
            color: rgba(255,255,255,0.15);
        }
        .chat-input-area button {
            padding: 15px 35px;
            background: linear-gradient(135deg, #00d4ff, #7b2ffc);
            border: none;
            border-radius: 16px;
            color: #fff;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 15px;
            box-shadow: 0 0 30px rgba(0, 150, 255, 0.1);
            white-space: nowrap;
        }
        .chat-input-area button:hover {
            transform: scale(1.03);
            box-shadow: 0 0 50px rgba(0, 150, 255, 0.2);
        }
        .chat-input-area button:disabled {
            opacity: 0.4;
            cursor: not-allowed;
            transform: none;
        }
        
        /* Upload */
        .upload-container {
            padding: 30px 40px;
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .upload-zone {
            border: 2px dashed rgba(0, 150, 255, 0.1);
            border-radius: 24px;
            padding: 60px 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.4s ease;
            background: rgba(0,0,0,0.15);
        }
        .upload-zone:hover {
            border-color: rgba(0, 150, 255, 0.25);
            background: rgba(0, 150, 255, 0.02);
        }
        .upload-zone i { font-size: 56px; color: rgba(0, 150, 255, 0.15); margin-bottom: 18px; display: block; }
        .upload-zone h3 { color: #e0e0e0; font-size: 19px; font-weight: 600; }
        .upload-zone p { color: rgba(255,255,255,0.15); font-size: 14px; margin-top: 6px; }
        
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 20px;
            background: rgba(255,255,255,0.02);
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.03);
        }
        .file-item .file-info { display: flex; align-items: center; gap: 14px; color: #e0e0e0; font-size: 14px; }
        .file-item .file-info i { color: #00d4ff; font-size: 20px; }
        .file-item .remove-btn {
            background: none;
            border: none;
            color: rgba(255,255,255,0.15);
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 18px;
        }
        .file-item .remove-btn:hover { color: #ff0040; }
        
        .upload-actions { display: flex; gap: 14px; flex-wrap: wrap; }
        .upload-btn {
            padding: 14px 40px;
            background: linear-gradient(135deg, #00d4ff, #7b2ffc);
            border: none;
            border-radius: 14px;
            color: #fff;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 15px;
        }
        .upload-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 0 40px rgba(0, 150, 255, 0.15);
        }
        .upload-btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
            transform: none;
        }
        
        /* History */
        .history-container {
            padding: 20px 40px;
            flex: 1;
            overflow-y: auto;
        }
        .history-item {
            padding: 16px 22px;
            background: rgba(255,255,255,0.01);
            border-radius: 14px;
            margin-bottom: 10px;
            border: 1px solid rgba(255,255,255,0.02);
            transition: all 0.3s ease;
        }
        .history-item:hover { background: rgba(255,255,255,0.02); }
        .history-item .h-time { color: rgba(255,255,255,0.1); font-size: 11px; }
        .history-item .h-user { color: #00d4ff; font-weight: 600; }
        .history-item .h-bot { color: #7b2ffc; font-weight: 600; }
        .history-item .h-content { color: #a0a0a0; margin-top: 6px; font-size: 14px; line-height: 1.6; }
        
        .empty-state {
            text-align: center;
            color: rgba(255,255,255,0.08);
            padding: 80px 0;
        }
        .empty-state i { font-size: 48px; display: block; margin-bottom: 20px; opacity: 0.3; }
        .empty-state p { font-size: 15px; }
        
        .quick-actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            padding: 0 40px 10px 40px;
        }
        .quick-actions .q-btn {
            padding: 8px 18px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 20px;
            color: rgba(255,255,255,0.3);
            font-size: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .quick-actions .q-btn:hover {
            background: rgba(0, 150, 255, 0.05);
            color: #fff;
            border-color: rgba(0, 150, 255, 0.1);
        }
        
        @media (max-width: 768px) {
            .sidebar { width: 200px; padding: 15px; }
            .chat-messages { padding: 20px; }
            .chat-messages .msg { max-width: 95%; }
            .upload-container { padding: 20px; }
            .history-container { padding: 15px 20px; }
            .chat-input-area { padding: 12px 16px 18px; }
            .chat-header { padding: 14px 20px; }
            .quick-actions { padding: 0 20px 10px 20px; }
        }
        @media (max-width: 600px) {
            .sidebar { width: 60px; padding: 10px; }
            .sidebar-brand h2, .sidebar-brand small, .sidebar-nav .nav-item span, .sidebar-user .user-email { display: none; }
            .sidebar-nav .nav-item { justify-content: center; padding: 12px; }
            .sidebar-nav .nav-item .badge { display: none; }
            .sidebar-brand .logo { margin: 0 auto; }
            .sidebar-user { flex-direction: column; gap: 8px; }
            .chat-messages { padding: 12px; }
            .chat-messages .msg .content { font-size: 14px; padding: 12px 16px; }
            .login-card { padding: 30px 20px; }
            .login-card .features-grid { grid-template-columns: repeat(2, 1fr); }
            .quick-actions { display: none; }
        }
        
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(0, 150, 255, 0.15); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(0, 150, 255, 0.3); }
    </style>
</head>
<body>

    <!-- LOGIN PAGE -->
    <div class="login-page" id="loginPage">
        <div class="login-card">
            <div class="logo">⚡</div>
            <h1>NIMA DEV AI</h1>
            <p>Ultimate Developer Intelligence</p>
            <div class="features-grid">
                <span class="tag">💻 Coding</span>
                <span class="tag">📦 ZIP Analysis</span>
                <span class="tag">🎨 Images</span>
                <span class="tag">🔧 Debugging</span>
                <span class="tag">🌐 Web Dev</span>
                <span class="tag">🤖 AI/ML</span>
                <span class="tag">🔐 Security</span>
                <span class="tag">📊 Data</span>
                <span class="tag">📝 Content</span>
            </div>
            
            <!-- GMAIL LOGIN BUTTON -->
            <button class="gmail-btn" onclick="loginWithGmail()" id="gmailBtn">
                <i class="fab fa-google" style="color:#4285F4;"></i>
                Sign in with Gmail
            </button>
            
            <div class="divider">OR</div>
            
            <div class="input-group">
                <i class="fas fa-envelope"></i>
                <input type="email" id="loginEmail" placeholder="Enter any email address..." value="demo@nima.dev">
            </div>
            
            <button class="login-btn" id="loginBtn" onclick="loginWithEmail()">
                <i class="fas fa-rocket"></i> Continue with Email
            </button>
            
            <div class="login-error" id="loginError">
                <i class="fas fa-exclamation-circle"></i> Please enter a valid email address
            </div>
            <div class="login-success" id="loginSuccess">
                <i class="fas fa-check-circle"></i> Login successful! Loading...
            </div>
        </div>
    </div>

    <!-- MAIN APP -->
    <div class="app-container" id="appContainer">
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="sidebar-brand">
                <div class="logo">⚡</div>
                <div>
                    <h2>NIMA DEV AI</h2>
                    <small>v4.0 Ultimate</small>
                </div>
            </div>
            <div class="sidebar-nav">
                <div class="nav-item active" data-page="chat" onclick="switchPage('chat')">
                    <i class="fas fa-comment-dots"></i><span>Chat</span>
                    <span class="badge">AI</span>
                </div>
                <div class="nav-item" data-page="upload" onclick="switchPage('upload')">
                    <i class="fas fa-upload"></i><span>Upload ZIP</span>
                    <span class="badge">Analyze</span>
                </div>
                <div class="nav-item" data-page="history" onclick="switchPage('history')">
                    <i class="fas fa-history"></i><span>History</span>
                    <span class="badge" id="historyCount">0</span>
                </div>
            </div>
            <div class="sidebar-user">
                <div class="user-info">
                    <div class="avatar" id="userAvatar">N</div>
                    <div class="user-email" id="userEmail">user@email.com</div>
                </div>
                <button class="logout-btn" onclick="logout()"><i class="fas fa-sign-out-alt"></i></button>
            </div>
        </div>

        <!-- Main -->
        <div class="main-content">
            <div class="chat-header">
                <h3 id="pageTitle">💬 NIMA DEV AI - Ultimate Assistant</h3>
                <div class="status"><span class="dot"></span><span>Active</span></div>
            </div>

            <div class="page-content">
                <!-- CHAT -->
                <div class="page active" id="page-chat">
                    <div class="chat-messages" id="chatMessages">
                        <div class="msg bot">
                            <div class="avatar">⚡</div>
                            <div class="content">
                                <strong>🔥 Welcome to NIMA DEV AI!</strong><br><br>
                                I'm your <strong>ultimate AI assistant</strong> - like DeepSeek/ChatGPT but better! 🚀<br><br>
                                
                                <strong>💪 What I can do for you:</strong><br><br>
                                • 💻 <strong>Coding</strong> - Python, JS, Java, C++, HTML/CSS, PHP, Ruby, Go, Rust<br>
                                • 🔧 <strong>Debugging</strong> - Find & fix errors, optimize code<br>
                                • 📦 <strong>ZIP Analysis</strong> - Analyze code, find errors, provide fixes<br>
                                • 🎨 <strong>Images</strong> - PIL, OpenCV, image editing scripts<br>
                                • 🌐 <strong>Web Dev</strong> - Full stack apps, APIs, databases<br>
                                • 🤖 <strong>AI/ML</strong> - TensorFlow, PyTorch, NLP, CV<br>
                                • 🔐 <strong>Security</strong> - Penetration testing, encryption<br>
                                • 📊 <strong>Data</strong> - Pandas, NumPy, visualization<br>
                                • 📝 <strong>Content</strong> - Articles, docs, tutorials<br>
                                • 🔄 <strong>Automation</strong> - Web scraping, bots<br><br>
                                
                                <em>Just type anything below! I can handle it all. 💪</em>
                            </div>
                        </div>
                    </div>
                    
                    <div class="quick-actions">
