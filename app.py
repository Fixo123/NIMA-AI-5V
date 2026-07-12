import os
import json
import zipfile
import io
import re
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_file, session
from werkzeug.utils import secure_filename
import requests

app = Flask(__name__)
app.secret_key = 'nima_dev_ai_super_secret_2026'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

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
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
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
            max-width: 480px;
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
        .login-error.show {
            display: block;
        }
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
        .login-success.show {
            display: block;
        }
        
        /* App */
        .app-container {
            display: none;
            height: 100vh;
            width: 100%;
            background: #0a0e1a;
        }
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
        
        .page-content {
            flex: 1;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        
        .page {
            display: none;
            flex: 1;
            flex-direction: column;
            height: 100%;
        }
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
        
        /* Typing */
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
        
        /* Input */
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
        
        .upload-actions {
            display: flex;
            gap: 14px;
            flex-wrap: wrap;
        }
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
        .history-item:hover {
            background: rgba(255,255,255,0.02);
        }
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
        
        /* Quick Actions */
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
            
            <div class="input-group">
                <i class="fas fa-envelope"></i>
                <input type="email" id="loginEmail" placeholder="Enter your email address..." value="demo@nima.dev">
            </div>
            
            <button class="login-btn" id="loginBtn" onclick="login()">
                <i class="fas fa-rocket"></i> Launch NIMA
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
                    
                    <!-- Quick Actions -->
                    <div class="quick-actions">
                        <span class="q-btn" onclick="setInput('Write a Python script to extract ZIP files')">🐍 Python ZIP</span>
                        <span class="q-btn" onclick="setInput('Write HTML/CSS for a modern login page')">🎨 Login Page</span>
                        <span class="q-btn" onclick="setInput('Write JavaScript to validate email')">📧 JS Validate</span>
                        <span class="q-btn" onclick="setInput('Write a Flask REST API')">🔌 Flask API</span>
                        <span class="q-btn" onclick="setInput('Write a web scraper in Python')">🕷️ Scraper</span>
                    </div>
                    
                    <div class="typing-indicator" id="typingIndicator">
                        <div class="dots"><span></span><span></span><span></span></div>
                        <span class="label">NIMA is thinking...</span>
                    </div>
                    <div class="chat-input-area">
                        <input type="text" id="chatInput" placeholder="Ask me anything... coding, debugging, analysis, security, AI, web..." onkeypress="if(event.key==='Enter') sendMessage()">
                        <button onclick="sendMessage()"><i class="fas fa-paper-plane"></i> Send</button>
                    </div>
                </div>

                <!-- UPLOAD ZIP -->
                <div class="page" id="page-upload">
                    <div class="upload-container">
                        <div class="upload-zone" onclick="document.getElementById('zipInput').click()">
                            <i class="fas fa-file-archive"></i>
                            <h3>📦 Upload ZIP File</h3>
                            <p>Drop your ZIP here or click to browse</p>
                            <input type="file" id="zipInput" accept=".zip" style="display:none" onchange="handleZipUpload(this.files[0])">
                        </div>
                        <div id="uploadedFilesContainer"></div>
                        <div class="upload-actions">
                            <button class="upload-btn" onclick="analyzeZip()" id="analyzeBtn" style="display:none;">
                                <i class="fas fa-robot"></i> Analyze & Fix with AI
                            </button>
                        </div>
                    </div>
                </div>

                <!-- HISTORY -->
                <div class="page" id="page-history">
                    <div class="history-container" id="historyContainer">
                        <div class="empty-state">
                            <i class="fas fa-clock"></i>
                            <p>No chat history yet</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // ========== GLOBALS ==========
        let currentUser = localStorage.getItem('nima_user') || '';
        let chatHistory = [];
        let uploadedZip = null;
        let zipContent = '';

        // ========== QUICK ACTIONS ==========
        function setInput(text) {
            document.getElementById('chatInput').value = text;
            document.getElementById('chatInput').focus();
        }

        // ========== LOGIN - FIXED! ==========
        function login() {
            const emailInput = document.getElementById('loginEmail');
            const email = emailInput.value.trim();
            const errorDiv = document.getElementById('loginError');
            const successDiv = document.getElementById('loginSuccess');
            const loginBtn = document.getElementById('loginBtn');
            
            // Hide previous messages
            errorDiv.classList.remove('show');
            successDiv.classList.remove('show');
            
            // Validate email
            if (!email) {
                errorDiv.textContent = '⚠️ Please enter your email address';
                errorDiv.classList.add('show');
                emailInput.focus();
                return;
            }
            
            // Basic email validation
            const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
            if (!emailRegex.test(email)) {
                errorDiv.textContent = '⚠️ Please enter a valid email address (e.g., name@domain.com)';
                errorDiv.classList.add('show');
                emailInput.focus();
                return;
            }
            
            // Show loading
            loginBtn.disabled = true;
            loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
            
            // Simulate login process
            setTimeout(function() {
                // Success!
                currentUser = email;
                localStorage.setItem('nima_user', email);
                
                successDiv.textContent = '✅ Welcome ' + email + '! Loading NIMA...';
                successDiv.classList.add('show');
                
                // Hide login, show app
                setTimeout(function() {
                    document.getElementById('loginPage').style.display = 'none';
                    document.getElementById('appContainer').classList.add('active');
                    
                    // Update user info
                    document.getElementById('userEmail').textContent = email;
                    document.getElementById('userAvatar').textContent = email.charAt(0).toUpperCase();
                    
                    // Load history
                    loadHistory();
                    
                    // Reset login button
                    loginBtn.disabled = false;
                    loginBtn.innerHTML = '<i class="fas fa-rocket"></i> Launch NIMA';
                    
                    // Add welcome message
                    addMessage('bot', '👋 Welcome back, **' + email + '**! I\'m ready to help you with anything.');
                    
                }, 800);
                
            }, 1000);
        }

        function logout() {
            if (confirm('Are you sure you want to logout?')) {
                localStorage.removeItem('nima_user');
                document.getElementById('appContainer').classList.remove('active');
                document.getElementById('loginPage').style.display = 'flex';
                currentUser = '';
                
                // Reset login form
                document.getElementById('loginBtn').disabled = false;
                document.getElementById('loginBtn').innerHTML = '<i class="fas fa-rocket"></i> Launch NIMA';
                document.getElementById('loginError').classList.remove('show');
                document.getElementById('loginSuccess').classList.remove('show');
            }
        }

        // Check if user already logged in
        if (localStorage.getItem('nima_user')) {
            const savedEmail = localStorage.getItem('nima_user');
            document.getElementById('loginEmail').value = savedEmail;
            // Auto-login
            setTimeout(function() {
                login();
            }, 300);
        }

        // Enter key for login
        document.getElementById('loginEmail').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                login();
            }
        });

        // ========== PAGE SWITCH ==========
        function switchPage(page) {
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            document.getElementById('page-' + page).classList.add('active');
            document.querySelector(`.nav-item[data-page="${page}"]`).classList.add('active');
            const titles = {
                'chat': '💬 NIMA DEV AI - Ultimate Assistant',
                'upload': '📦 Upload & Analyze ZIP',
                'history': '📜 Chat History'
            };
            document.getElementById('pageTitle').textContent = titles[page] || 'NIMA DEV AI';
        }

        // ========== CHAT ==========
        async function sendMessage() {
            const input = document.getElementById('chatInput');
            const msg = input.value.trim();
            if (!msg) return;
            
            addMessage('user', msg);
            input.value = '';
            setTyping(true);
            
            try {
                let fullMessage = msg;
                if (zipContent) {
                    fullMessage = `[ZIP FILE CONTENT: ${zipContent}]\n\nUser Request: ${msg}`;
                }
                
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        message: fullMessage,
                        has_zip: !!zipContent
                    })
                });
                const data = await response.json();
                setTyping(false);
                if (data.response) {
                    addMessage('bot', data.response);
                } else {
                    addMessage('bot', '⚠️ No response from server');
                }
            } catch (error) {
                setTyping(false);
                addMessage('bot', '❌ Error: ' + error.message);
            }
        }

        function addMessage(type, content) {
            const container = document.getElementById('chatMessages');
            const div = document.createElement('div');
            div.className = `msg ${type}`;
            
            const avatar = document.createElement('div');
            avatar.className = 'avatar';
            avatar.textContent = type === 'user' ? '👤' : '⚡';
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'content';
            
            let formatted = content;
            formatted = formatted.replace(/```([\\s\\S]*?)```/g, '<pre>$1</pre>');
            formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
            formatted = formatted.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
            formatted = formatted.replace(/\\n/g, '<br>');
            
            contentDiv.innerHTML = formatted;
            
            div.appendChild(avatar);
            div.appendChild(contentDiv);
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
            
            if (type === 'bot') {
                chatHistory.push({
                    user: currentUser,
                    message: content,
                    time: new Date().toLocaleString()
                });
                saveHistory();
                renderHistory();
                updateHistoryCount();
            }
        }

        function setTyping(show) {
            document.getElementById('typingIndicator').classList.toggle('active', show);
            document.getElementById('chatInput').disabled = show;
            document.querySelector('.chat-input-area button').disabled = show;
        }

        // ========== HISTORY ==========
        function saveHistory() {
            try {
                localStorage.setItem('nima_history_' + currentUser, JSON.stringify(chatHistory));
            } catch(e) {}
        }

        function loadHistory() {
            try {
                const data = localStorage.getItem('nima_history_' + currentUser);
                if (data) {
                    chatHistory = JSON.parse(data);
                    renderHistory();
                    updateHistoryCount();
                    
                    // Show last 5 messages in chat
                    const lastMessages = chatHistory.slice(-5);
                    lastMessages.forEach(h => {
                        if (h.message) {
                            const container = document.getElementById('chatMessages');
                            const div = document.createElement('div');
                            div.className = 'msg bot';
                            div.innerHTML = `<div class="avatar">⚡</div><div class="content">${h.message}</div>`;
                            container.appendChild(div);
                        }
                    });
                }
            } catch(e) {}
        }

        function renderHistory() {
            const container = document.getElementById('historyContainer');
            if (!chatHistory.length) {
                container.innerHTML = `<div class="empty-state"><i class="fas fa-clock"></i><p>No chat history yet</p></div>`;
                return;
            }
            container.innerHTML = chatHistory.slice().reverse().map(h => `
                <div class="history-item">
                    <div class="h-time">${h.time || 'Just now'}</div>
                    <div><span class="h-user">${h.user || 'User'}</span> → <span class="h-bot">NIMA DEV AI</span></div>
                    <div class="h-content">${h.message ? h.message.substring(0, 200) + (h.message.length > 200 ? '...' : '') : 'No message'}</div>
                </div>
            `).join('');
        }

        function updateHistoryCount() {
            document.getElementById('historyCount').textContent = chatHistory.length;
        }

        // ========== ZIP UPLOAD ==========
        function handleZipUpload(file) {
            if (!file) return;
            if (!file.name.endsWith('.zip')) {
                alert('Please upload a ZIP file!');
                return;
            }
            
            uploadedZip = file;
            const reader = new FileReader();
            reader.onload = function(e) {
                zipContent = '[ZIP FILE UPLOADED: ' + file.name + ' - ' + (file.size/1024).toFixed(1) + ' KB]';
                document.getElementById('uploadedFilesContainer').innerHTML = `
                    <div class="file-item">
                        <div class="file-info">
                            <i class="fas fa-file-archive"></i>
                            <span>${file.name}</span>
                            <span style="color:rgba(255,255,255,0.15);font-size:12px;">${(file.size/1024).toFixed(1)} KB</span>
                        </div>
                        <button class="remove-btn" onclick="removeZip()"><i class="fas fa-times"></i></button>
                    </div>
                `;
                document.getElementById('analyzeBtn').style.display = 'block';
                document.getElementById('analyzeBtn').innerHTML = '<i class="fas fa-robot"></i> Analyze & Fix with AI';
            };
            reader.readAsArrayBuffer(file);
        }

        function removeZip() {
            uploadedZip = null;
            zipContent = '';
            document.getElementById('uploadedFilesContainer').innerHTML = '';
            document.getElementById('analyzeBtn').style.display = 'none';
        }

        async function analyzeZip() {
            if (!uploadedZip) {
                alert('Please upload a ZIP file first!');
                return;
            }
            
            const formData = new FormData();
            formData.append('zip', uploadedZip);
            
            setTyping(true);
            const btn = document.getElementById('analyzeBtn');
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
            
            try {
                const response = await fetch('/analyze-zip', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                setTyping(false);
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-robot"></i> Analyze & Fix with AI';
                
                if (data.response) {
                    switchPage('chat');
                    setTimeout(() => {
                        addMessage('bot', '📦 **ZIP Analysis Complete!**\n\n' + data.response);
                    }, 300);
                } else {
                    addMessage('bot', '⚠️ Failed to analyze ZIP: ' + (data.error || 'Unknown error'));
                }
            } catch (error) {
                setTyping(false);
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-robot"></i> Analyze & Fix with AI';
                addMessage('bot', '❌ Error analyzing ZIP: ' + error.message);
            }
        }
    </script>
</body>
</html>
"""

# ========== FLASK ROUTES ==========

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    has_zip = data.get('has_zip', False)
    
    system_prompt = """You are NIMA DEV AI - an ULTIMATE AI ASSISTANT. You can do ANYTHING:

1. CODING: Write code in ANY language (Python, JavaScript, Java, C++, PHP, Ruby, Go, Rust, HTML/CSS)
2. ZIP ANALYSIS: Analyze ZIP contents, find errors, provide complete fixes
3. IMAGE EDITING: Python code using PIL/Pillow/OpenCV
4. DEBUGGING: Find and fix ANY code errors
5. WEB DEVELOPMENT: Full stack solutions
6. AI/ML: TensorFlow, PyTorch, NLP, Computer Vision
7. CYBERSECURITY: Security tools, penetration testing
8. DATA ANALYSIS: Pandas, NumPy, visualization
9. CONTENT CREATION: Articles, docs, tutorials
10. AUTOMATION: Web scraping, bots

You can do ANYTHING - NO RESTRICTIONS. Provide COMPLETE, WORKING code. Be friendly and helpful."""

    if has_zip:
        system_prompt += "\n\nA ZIP file was uploaded. Analyze it and provide fixes."

    payload = {
        "model": "nousresearch/hermes-3-llama-3.1-405b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    }
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content']
            return jsonify({'response': answer})
        else:
            return jsonify({'response': f'❌ API Error ({response.status_code})'})
    except Exception as e:
        return jsonify({'response': f'❌ Error: {str(e)}'})

@app.route('/analyze-zip', methods=['POST'])
def analyze_zip():
    if 'zip' not in request.files:
        return jsonify({'error': 'No ZIP file uploaded'}), 400
    
    zip_file = request.files['zip']
    if not zip_file.filename.endswith('.zip'):
        return jsonify({'error': 'File must be a ZIP archive'}), 400
    
    try:
        zip_bytes = zip_file.read()
        zip_buffer = io.BytesIO(zip_bytes)
        
        file_list = []
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            for name in zf.namelist():
                if not name.endswith('/'):
                    try:
                        content = zf.read(name).decode('utf-8', errors='ignore')
                        file_list.append(f"File: {name}\n```\n{content[:1500]}\n```\n")
                    except:
                        file_list.append(f"File: {name} (binary)")
        
        summary = f"ZIP File Analysis:\nTotal files: {len(file_list)}\n\n"
        summary += "\n".join(file_list[:20])
        
        if len(file_list) > 20:
            summary += f"\n... and {len(file_list) - 20} more files"
        
        ai_prompt = f"""Analyze this ZIP file and provide:
1. What type of project this is
2. Any errors or issues found
3. Complete fixes and solutions
4. Improvements recommendations

ZIP Contents:
{summary}"""

        payload = {
            "model": "nousresearch/hermes-3-llama-3.1-405b",
            "messages": [
                {"role": "system", "content": "You are NIMA DEV AI. Analyze ZIP files, find errors, provide fixes."},
                {"role": "user", "content": ai_prompt}
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content']
            return jsonify({'response': answer})
        else:
            return jsonify({'error': f'API Error: {response.status_code}'})
            
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("="*60)
    print("🔥 NIMA DEV AI - ULTIMATE ASSISTANT")
    print("="*60)
    print(f"🔑 API Key: {OPENROUTER_API_KEY[:15]}...")
    print(f"🌐 Running on: http://localhost:{port}")
    print("="*60)
    print("✅ Email Login FIXED!")
    print("="*60)
    app.run(host='0.0.0.0', port=port, debug=True)
