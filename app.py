import os
import json
import zipfile
import io
import tempfile
import shutil
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_file, session
from werkzeug.utils import secure_filename
import requests
import base64

app = Flask(__name__)
app.secret_key = 'nima_dev_ai_secret_key_2026'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# ===== YOUR API KEY =====
OPENROUTER_API_KEY = "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"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Create temp folder for uploads
os.makedirs('temp_uploads', exist_ok=True)

# ============ HTML TEMPLATE ============
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NIMA DEV AI - ChatGPT Style</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
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
        }
        .login-card {
            background: rgba(20, 25, 45, 0.95);
            border-radius: 24px;
            padding: 50px 40px;
            max-width: 420px;
            width: 100%;
            border: 1px solid rgba(0, 150, 255, 0.15);
            box-shadow: 0 20px 80px rgba(0, 0, 0, 0.5);
            text-align: center;
        }
        .login-card .logo {
            width: 70px;
            height: 70px;
            background: linear-gradient(135deg, #00d4ff, #7b2ffc);
            border-radius: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            margin: 0 auto 20px;
            box-shadow: 0 0 40px rgba(0, 150, 255, 0.2);
        }
        .login-card h1 {
            font-size: 26px;
            font-weight: 800;
            background: linear-gradient(135deg, #00d4ff, #7b2ffc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .login-card p {
            color: rgba(255,255,255,0.3);
            font-size: 14px;
            margin: 5px 0 25px;
        }
        .login-card input {
            width: 100%;
            padding: 14px 18px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            color: #fff;
            font-size: 15px;
            outline: none;
            transition: all 0.3s ease;
        }
        .login-card input:focus {
            border-color: rgba(0, 150, 255, 0.4);
        }
        .login-btn {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #00d4ff, #7b2ffc);
            border: none;
            border-radius: 12px;
            color: #fff;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 12px;
        }
        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 0 40px rgba(0, 150, 255, 0.3);
        }
        
        /* App */
        .app-container {
            display: none;
            height: 100vh;
            width: 100%;
            background: #0a0e1a;
        }
        .app-container.active { display: flex; }
        
        /* Sidebar - ChatGPT Style */
        .sidebar {
            width: 260px;
            background: rgba(15, 20, 40, 0.98);
            border-right: 1px solid rgba(255,255,255,0.05);
            padding: 20px;
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }
        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            margin-bottom: 20px;
        }
        .sidebar-brand .logo {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #00d4ff, #7b2ffc);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            color: #fff;
        }
        .sidebar-brand h2 {
            font-size: 18px;
            font-weight: 700;
            background: linear-gradient(135deg, #00d4ff, #7b2ffc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .sidebar-brand small {
            font-size: 9px;
            color: rgba(255,255,255,0.2);
            text-transform: uppercase;
            letter-spacing: 2px;
            display: block;
        }
        
        .sidebar-nav { flex: 1; }
        .sidebar-nav .nav-item {
            padding: 12px 16px;
            border-radius: 10px;
            color: rgba(255,255,255,0.5);
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 2px;
        }
        .sidebar-nav .nav-item:hover {
            background: rgba(255,255,255,0.05);
            color: #fff;
        }
        .sidebar-nav .nav-item.active {
            background: rgba(0, 150, 255, 0.1);
            color: #00d4ff;
        }
        .sidebar-nav .nav-item i { width: 20px; }
        
        .sidebar-user {
            padding-top: 16px;
            border-top: 1px solid rgba(255,255,255,0.05);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .sidebar-user .user-info { display: flex; align-items: center; gap: 10px; }
        .sidebar-user .avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: linear-gradient(135deg, #00d4ff, #7b2ffc);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-weight: 700;
            font-size: 12px;
        }
        .sidebar-user .user-email {
            color: #fff;
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
            color: rgba(255,255,255,0.3);
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        .sidebar-user .logout-btn:hover { color: #ff0040; }
        
        /* Main - ChatGPT Style */
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: #0d1225;
            overflow: hidden;
        }
        
        .chat-header {
            padding: 16px 30px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(10, 14, 26, 0.8);
        }
        .chat-header h3 {
            font-size: 16px;
            font-weight: 600;
            color: #e0e0e0;
        }
        .chat-header .status {
            display: flex;
            align-items: center;
            gap: 8px;
            color: rgba(255,255,255,0.3);
            font-size: 12px;
        }
        .chat-header .status .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #00ff88;
            animation: blink 1.5s ease-in-out infinite;
        }
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
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
        
        /* ===== CHAT PAGE - ChatGPT Style ===== */
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 30px 40px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        .chat-messages .msg {
            display: flex;
            gap: 16px;
            max-width: 85%;
            animation: fadeIn 0.4s ease;
        }
        .chat-messages .msg.user {
            align-self: flex-end;
            flex-direction: row-reverse;
        }
        .chat-messages .msg .avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            flex-shrink: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: 700;
        }
        .chat-messages .msg.user .avatar {
            background: linear-gradient(135deg, #00d4ff, #7b2ffc);
            color: #fff;
        }
        .chat-messages .msg.bot .avatar {
            background: rgba(255,255,255,0.08);
            color: #7b2ffc;
        }
        .chat-messages .msg .content {
            padding: 14px 20px;
            border-radius: 16px;
            font-size: 15px;
            line-height: 1.7;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .chat-messages .msg.user .content {
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.12), rgba(123, 47, 252, 0.12));
            border: 1px solid rgba(0, 150, 255, 0.08);
            color: #c8e0ff;
        }
        .chat-messages .msg.bot .content {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.05);
            color: #e8e8e8;
        }
        .chat-messages .msg .content pre {
            background: rgba(0,0,0,0.4);
            padding: 14px;
            border-radius: 10px;
            overflow-x: auto;
            font-size: 13px;
            margin: 8px 0;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .chat-messages .msg .content code {
            background: rgba(0,0,0,0.3);
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 13px;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .chat-input-area {
            padding: 16px 30px 24px;
            border-top: 1px solid rgba(255,255,255,0.05);
            display: flex;
            gap: 12px;
            background: rgba(10, 14, 26, 0.8);
        }
        .chat-input-area input {
            flex: 1;
            padding: 14px 20px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 14px;
            color: #fff;
            font-size: 15px;
            outline: none;
            transition: all 0.3s ease;
        }
        .chat-input-area input:focus {
            border-color: rgba(0, 150, 255, 0.3);
            background: rgba(255,255,255,0.07);
        }
        .chat-input-area input::placeholder {
            color: rgba(255,255,255,0.2);
        }
        .chat-input-area button {
            padding: 14px 28px;
            background: linear-gradient(135deg, #00d4ff, #7b2ffc);
            border: none;
            border-radius: 14px;
            color: #fff;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 14px;
        }
        .chat-input-area button:hover {
            transform: scale(1.02);
            box-shadow: 0 0 30px rgba(0, 150, 255, 0.2);
        }
        .chat-input-area button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        /* Upload Area */
        .upload-container {
            padding: 30px 40px;
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        .upload-zone {
            border: 2px dashed rgba(0, 150, 255, 0.15);
            border-radius: 20px;
            padding: 60px 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            background: rgba(0,0,0,0.2);
        }
        .upload-zone:hover {
            border-color: rgba(0, 150, 255, 0.3);
            background: rgba(0, 150, 255, 0.02);
        }
        .upload-zone i { font-size: 50px; color: rgba(0, 150, 255, 0.2); margin-bottom: 16px; }
        .upload-zone h3 { color: #fff; font-size: 18px; font-weight: 600; }
        .upload-zone p { color: rgba(255,255,255,0.2); font-size: 14px; margin-top: 6px; }
        
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 18px;
            background: rgba(255,255,255,0.03);
            border-radius: 10px;
            margin-top: 8px;
            border: 1px solid rgba(255,255,255,0.03);
        }
        .file-item .file-info { display: flex; align-items: center; gap: 12px; color: #e0e0e0; font-size: 14px; }
        .file-item .file-info i { color: #00d4ff; }
        .file-item .remove-btn {
            background: none;
            border: none;
            color: rgba(255,255,255,0.2);
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .file-item .remove-btn:hover { color: #ff0040; }
        
        .upload-btn {
            margin-top: 20px;
            padding: 14px 40px;
            background: linear-gradient(135deg, #00d4ff, #7b2ffc);
            border: none;
            border-radius: 12px;
            color: #fff;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 15px;
            align-self: flex-start;
        }
        .upload-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 0 40px rgba(0, 150, 255, 0.2);
        }
        
        /* History */
        .history-container {
            padding: 20px 40px;
            flex: 1;
            overflow-y: auto;
        }
        .history-item {
            padding: 14px 20px;
            background: rgba(255,255,255,0.02);
            border-radius: 12px;
            margin-bottom: 10px;
            border: 1px solid rgba(255,255,255,0.03);
        }
        .history-item .h-time { color: rgba(255,255,255,0.15); font-size: 11px; }
        .history-item .h-user { color: #00d4ff; font-weight: 600; }
        .history-item .h-bot { color: #7b2ffc; font-weight: 600; }
        .history-item .h-content { color: #c0c0c0; margin-top: 4px; font-size: 14px; }
        
        .empty-state {
            text-align: center;
            color: rgba(255,255,255,0.15);
            padding: 60px 0;
        }
        .empty-state i { font-size: 40px; display: block; margin-bottom: 16px; opacity: 0.3; }
        
        @media (max-width: 768px) {
            .sidebar { width: 200px; padding: 15px; }
            .chat-messages { padding: 20px; }
            .chat-messages .msg { max-width: 95%; }
            .upload-container { padding: 20px; }
            .history-container { padding: 15px 20px; }
            .chat-input-area { padding: 12px 16px 18px; }
        }
        @media (max-width: 600px) {
            .sidebar { width: 60px; padding: 10px; }
            .sidebar-brand h2, .sidebar-brand small, .sidebar-nav .nav-item span, .sidebar-user .user-email { display: none; }
            .sidebar-nav .nav-item { justify-content: center; padding: 12px; }
            .sidebar-brand .logo { margin: 0 auto; }
            .sidebar-user { flex-direction: column; gap: 8px; }
            .chat-messages { padding: 12px; }
            .chat-messages .msg .content { font-size: 14px; padding: 12px 16px; }
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(0, 150, 255, 0.2); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(0, 150, 255, 0.4); }
        
        /* Typing indicator */
        .typing-indicator {
            display: none;
            align-self: flex-start;
            gap: 12px;
            padding: 12px 20px;
            background: rgba(255,255,255,0.03);
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .typing-indicator.active { display: flex; }
        .typing-indicator .dots { display: flex; gap: 4px; align-items: center; }
        .typing-indicator .dots span {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #00d4ff;
            animation: typingAnim 1.4s ease-in-out infinite;
        }
        .typing-indicator .dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator .dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typingAnim {
            0%, 60%, 100% { transform: translateY(0); opacity: 0.3; }
            30% { transform: translateY(-6px); opacity: 1; }
        }
    </style>
</head>
<body>

    <!-- LOGIN -->
    <div class="login-page" id="loginPage">
        <div class="login-card">
            <div class="logo">⚡</div>
            <h1>NIMA DEV AI</h1>
            <p>Advanced Developer Intelligence</p>
            <input type="email" id="loginEmail" placeholder="Enter your email..." value="demo@nima.dev">
            <button class="login-btn" onclick="login()">🚀 Continue</button>
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
                    <small>v3.0 Pro</small>
                </div>
            </div>
            <div class="sidebar-nav">
                <div class="nav-item active" data-page="chat" onclick="switchPage('chat')">
                    <i class="fas fa-comment-dots"></i><span>Chat</span>
                </div>
                <div class="nav-item" data-page="upload" onclick="switchPage('upload')">
                    <i class="fas fa-upload"></i><span>Upload ZIP</span>
                </div>
                <div class="nav-item" data-page="history" onclick="switchPage('history')">
                    <i class="fas fa-history"></i><span>History</span>
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
                <h3 id="pageTitle">💬 Chat with NIMA DEV AI</h3>
                <div class="status"><span class="dot"></span><span>Active</span></div>
            </div>

            <div class="page-content">
                <!-- CHAT -->
                <div class="page active" id="page-chat">
                    <div class="chat-messages" id="chatMessages">
                        <div class="msg bot">
                            <div class="avatar">⚡</div>
                            <div class="content">
                                <strong>Welcome to NIMA DEV AI!</strong><br><br>
                                I'm your AI developer assistant. I can help you with:<br>
                                • 💻 Coding & debugging<br>
                                • 📦 Analyzing ZIP files<br>
                                • 🎨 Creating code for images/editing<br>
                                • 🔧 Fixing errors in your code<br><br>
                                Upload a ZIP file or ask me anything!
                            </div>
                        </div>
                    </div>
                    <div class="typing-indicator" id="typingIndicator">
                        <div class="dots"><span></span><span></span><span></span></div>
                        <span style="color:rgba(255,255,255,0.2);font-size:13px;">NIMA is thinking...</span>
                    </div>
                    <div class="chat-input-area">
                        <input type="text" id="chatInput" placeholder="Ask me anything..." onkeypress="if(event.key==='Enter') sendMessage()">
                        <button onclick="sendMessage()">Send</button>
                    </div>
                </div>

                <!-- UPLOAD ZIP -->
                <div class="page" id="page-upload">
                    <div class="upload-container">
                        <div class="upload-zone" onclick="document.getElementById('zipInput').click()">
                            <i class="fas fa-file-archive"></i>
                            <h3>Upload ZIP File</h3>
                            <p>Click to select a .zip file or drag & drop</p>
                            <input type="file" id="zipInput" accept=".zip" style="display:none" onchange="handleZipUpload(this.files[0])">
                        </div>
                        <div id="uploadedFilesContainer"></div>
                        <button class="upload-btn" onclick="analyzeZip()" id="analyzeBtn" style="display:none;">
                            <i class="fas fa-robot"></i> Analyze with AI
                        </button>
                    </div>
                </div>

                <!-- HISTORY -->
                <div class="page" id="page-history">
                    <div class="history-container" id="historyContainer">
                        <div class="empty-state">
                            <i class="fas fa-clock"></i>
                            No chat history yet
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

        // ========== LOGIN ==========
        function login() {
            const email = document.getElementById('loginEmail').value.trim();
            if (!email || !email.includes('@')) {
                alert('Please enter a valid email');
                return;
            }
            currentUser = email;
            localStorage.setItem('nima_user', email);
            document.getElementById('loginPage').style.display = 'none';
            document.getElementById('appContainer').classList.add('active');
            document.getElementById('userEmail').textContent = email;
            document.getElementById('userAvatar').textContent = email.charAt(0).toUpperCase();
            loadHistory();
        }

        function logout() {
            localStorage.removeItem('nima_user');
            document.getElementById('appContainer').classList.remove('active');
            document.getElementById('loginPage').style.display = 'flex';
            currentUser = '';
        }

        if (localStorage.getItem('nima_user')) {
            document.getElementById('loginEmail').value = localStorage.getItem('nima_user');
            login();
        }

        // ========== PAGE SWITCH ==========
        function switchPage(page) {
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            document.getElementById('page-' + page).classList.add('active');
            document.querySelector(`.nav-item[data-page="${page}"]`).classList.add('active');
            const titles = {
                'chat': '💬 Chat with NIMA DEV AI',
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
                    fullMessage = `[ZIP FILE CONTENT: ${zipContent}]\n\nUser: ${msg}`;
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
            contentDiv.innerHTML = content.replace(/\\n/g, '<br>');
            
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
                    chatHistory.forEach(h => {
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
                container.innerHTML = `<div class="empty-state"><i class="fas fa-clock"></i>No chat history yet</div>`;
                return;
            }
            container.innerHTML = chatHistory.slice().reverse().map(h => `
                <div class="history-item">
                    <div class="h-time">${h.time || 'Just now'}</div>
                    <div><span class="h-user">${h.user || 'User'}</span> → <span class="h-bot">NIMA DEV AI</span></div>
                    <div class="h-content">${h.message || 'No message'}</div>
                </div>
            `).join('');
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
                            <span style="color:rgba(255,255,255,0.2);font-size:12px;">${(file.size/1024).toFixed(1)} KB</span>
                        </div>
                        <button class="remove-btn" onclick="removeZip()"><i class="fas fa-times"></i></button>
                    </div>
                `;
                document.getElementById('analyzeBtn').style.display = 'block';
                
                // Auto analyze
                analyzeZip();
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
            document.getElementById('analyzeBtn').disabled = true;
            
            try {
                const response = await fetch('/analyze-zip', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                setTyping(false);
                document.getElementById('analyzeBtn').disabled = false;
                
                if (data.response) {
                    switchPage('chat');
                    setTimeout(() => {
                        addMessage('bot', data.response);
                    }, 300);
                } else {
                    addMessage('bot', '⚠️ Failed to analyze ZIP: ' + (data.error || 'Unknown error'));
                }
            } catch (error) {
                setTyping(false);
                document.getElementById('analyzeBtn').disabled = false;
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
    
    system_prompt = """You are NIMA DEV AI, a professional developer assistant like ChatGPT. You help with:

1. **Code Analysis & Debugging**: When users upload ZIP files, analyze the code inside and fix errors
2. **Image/Graphics Code**: When users ask for image editing, provide Python code using PIL/Pillow
3. **File Analysis**: Read and understand file contents from ZIP archives
4. **Development Help**: Provide practical coding solutions

Always give detailed, helpful responses with code examples when relevant. Be friendly and professional.

IMPORTANT: 
- When users mention ZIP files, you've already received the file content
- Provide complete, working code solutions
- Explain your fixes clearly
- Be thorough and helpful"""

    if has_zip:
        system_prompt += "\n\nA ZIP file was uploaded. Analyze its contents and help the user with their request."

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
            error_msg = response.text[:200]
            return jsonify({'response': f'❌ API Error: {response.status_code}'})
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
        # Read ZIP contents
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
        summary += "\n".join(file_list[:20])  # Limit to 20 files
        
        if len(file_list) > 20:
            summary += f"\n... and {len(file_list) - 20} more files"
        
        # Send to AI for analysis
        ai_prompt = f"""Analyze this ZIP file content and provide:
1. What type of project this is
2. Any errors or issues found
3. Fixes and recommendations
4. Complete solution if needed

ZIP Contents:
{summary}

Provide a detailed, helpful response with fixes."""

        payload = {
            "model": "nousresearch/hermes-3-llama-3.1-405b",
            "messages": [
                {"role": "system", "content": "You are NIMA DEV AI. Analyze ZIP files and provide fixes, solutions, and detailed explanations. Be thorough and professional."},
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
    print("🚀 NIMA DEV AI - ChatGPT Style")
    print(f"🔑 API Key: {OPENROUTER_API_KEY[:20]}...")
    app.run(host='0.0.0.0', port=port, debug=False)
