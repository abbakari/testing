// static/js/chat.js
document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const startCallButton = document.getElementById('start-call');
    const callModal = document.getElementById('call-modal');
    const closeModal = document.querySelector('.close-modal');
    const callOptions = document.querySelectorAll('.call-option');
    
    let lastMessageId = LAST_MESSAGE_ID;
    let isTyping = false;
    let typingTimer;
    
    // Initialize WebSocket connection
    const socketProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const socketUrl = socketProtocol + window.location.host + '/ws/group/' + GROUP_ID + '/';
    const socket = new WebSocket(socketUrl);
    
    // Scroll to bottom initially
    scrollToBottom();
    
    // WebSocket event handlers
    socket.onopen = function(e) {
        console.log('WebSocket connection established');
        checkForNewMessages();
    };
    
    socket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        
        if (data.type === 'message') {
            addMessage(data.message);
        } 
        else if (data.type === 'typing') {
            handleTypingIndicator(data);
        }
        else if (data.type === 'presence') {
            updateOnlineMembers(data.online_members);
        }
        else if (data.type === 'call') {
            handleCallEvent(data);
        }
    };
    
    socket.onclose = function(e) {
        console.log('WebSocket disconnected, attempting to reconnect...');
        setTimeout(function() {
            // Try to reconnect every 5 seconds
            const newSocket = new WebSocket(socketUrl);
            newSocket.onopen = socket.onopen;
            newSocket.onmessage = socket.onmessage;
            newSocket.onclose = socket.onclose;
            socket = newSocket;
        }, 5000);
    };
    
    // Send message when send button is clicked
    sendButton.addEventListener('click', sendMessage);
    
    // Send message when Enter is pressed
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Typing indicators
    messageInput.addEventListener('input', function() {
        if (!isTyping) {
            isTyping = true;
            socket.send(JSON.stringify({
                'type': 'typing',
                'user_id': USER_ID,
                'is_typing': true
            }));
        }
        
        clearTimeout(typingTimer);
        typingTimer = setTimeout(function() {
            isTyping = false;
            socket.send(JSON.stringify({
                'type': 'typing',
                'user_id': USER_ID,
                'is_typing': false
            }));
        }, 2000);
    });
    
    // Call functionality
    startCallButton.addEventListener('click', function() {
        callModal.style.display = 'flex';
    });
    
    closeModal.addEventListener('click', function() {
        callModal.style.display = 'none';
    });
    
    callOptions.forEach(option => {
        option.addEventListener('click', function() {
            const callType = this.dataset.type;
            startCall(callType);
            callModal.style.display = 'none';
        });
    });
    
    // Periodically check for new messages (fallback if WebSocket fails)
    setInterval(checkForNewMessages, 10000);
    
    function sendMessage() {
        const message = messageInput.value.trim();
        if (message) {
            socket.send(JSON.stringify({
                'type': 'message',
                'message': message,
                'user_id': USER_ID
            }));
            
            // Optimistically add the message to the UI
            const tempMessage = {
                id: 'temp-' + Date.now(),
                content: message,
                sender: USER_ID,
                timestamp: new Date().toISOString(),
                is_self: true
            };
            addMessage(tempMessage);
            
            messageInput.value = '';
        }
    }
    
    function addMessage(messageData) {
        // Check if message already exists
        if (document.querySelector(`[data-message-id="${messageData.id}"]`)) {
            return;
        }
        
        const messageElement = document.createElement('div');
        messageElement.className = `message ${messageData.is_self ? 'sent' : 'received'}`;
        messageElement.dataset.messageId = messageData.id;
        
        let avatarHtml = '';
        if (!messageData.is_self) {
            avatarHtml = `
                <img src="${messageData.sender_avatar || '/static/images/default-avatar.jpg'}" 
                     alt="${messageData.sender}" class="avatar">
            `;
        }
        
        const time = new Date(messageData.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageElement.innerHTML = `
            ${avatarHtml}
            <div class="message-content">
                ${!messageData.is_self ? `<div class="sender-name">${messageData.sender}</div>` : ''}
                <div class="message-bubble">${messageData.content}</div>
                <div class="message-time">
                    ${time}
                    ${messageData.is_self ? '<i class="status-icon fas fa-check"></i>' : ''}
                </div>
            </div>
        `;
        
        // If it's our own message, replace the temporary one
        if (messageData.is_self && messageData.id.startsWith('temp-')) {
            const tempMessage = document.querySelector(`[data-message-id="${messageData.id}"]`);
            if (tempMessage) {
                tempMessage.replaceWith(messageElement);
            } else {
                chatMessages.prepend(messageElement);
            }
        } else {
            chatMessages.prepend(messageElement);
        }
        
        scrollToBottom();
        
        // Update last message ID
        if (!messageData.id.startsWith('temp-') && messageData.id > lastMessageId) {
            lastMessageId = messageData.id;
        }
    }
    
    function checkForNewMessages() {
        fetch(`/group/${GROUP_ID}/chat/api/?last_id=${lastMessageId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    data.messages.reverse().forEach(msg => {
                        // Only add messages we don't already have
                        if (!document.querySelector(`[data-message-id="${msg.id}"]`)) {
                            addMessage(msg);
                        }
                    });
                    
                    updateOnlineMembers(data.online_members);
                }
            });
    }
    
    function updateOnlineMembers(onlineMembers) {
        const onlineCount = document.getElementById('online-members');
        if (onlineCount) {
            onlineCount.textContent = onlineMembers.length;
        }
    }
    
    function handleTypingIndicator(data) {
        // Implement typing indicators if needed
    }
    
    function handleCallEvent(data) {
        if (data.action === 'started') {
            // Show notification about new call
            const callButton = document.createElement('a');
            callButton.href = `/group/call/${data.call_id}/join/`;
            callButton.className = 'call-button';
            callButton.innerHTML = `
                <i class="fas fa-${data.call_type === 'video' ? 'video' : 'phone'}"></i> 
                Join ${data.call_type} Call
            `;
            
            const callActions = document.querySelector('.call-actions');
            callActions.appendChild(callButton);
        }
    }
    
    function startCall(callType) {
        fetch(`/group/${GROUP_ID}/call/start/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({
                'call_type': callType
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.location.href = `/group/call/${data.call_id}/`;
            }
        });
    }
    
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});