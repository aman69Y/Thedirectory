
(function(){
  const chatWindow = document.getElementById('chat-window');
  if(!chatWindow) return;
  const currentUserId = parseInt(document.body.dataset.uid, 10);
  const chatId = chatWindow.dataset.chatId;
  const sendInput = document.getElementById('send-input');
  const sendBtn = document.getElementById('send-btn');
  const gifBtn = document.getElementById('gif-btn');
  const gifModal = document.getElementById('gif-search-modal');
  const gifQuery = document.getElementById('gif-query');
  const gifSearch = document.getElementById('gif-search');
  const gifResults = document.getElementById('gif-results');
  const mediaInput = document.getElementById('chat-media');
  const replyBanner = document.getElementById('reply-banner');
  const replyToName = document.getElementById('reply-to-name');
  const replyToContent = document.getElementById('reply-to-content');
  const cancelReplyBtn = document.getElementById('cancel-reply');
  let lastId = 0;
  let replyToId = null;
  let forwardMsgId = null;
  const forwardModal = new bootstrap.Modal(document.getElementById('forward-modal'));
  const forwardChatList = document.getElementById('forward-chat-list');
  const forwardSendBtn = document.getElementById('forward-send-btn');
  const socket = io();

  function escapeHtml(s){ return (s||'').replace(/[&<>"']/g, m=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[m])); }

  function appendMessage(m){
    lastId = Math.max(lastId, m.id);
    const wrap = document.createElement('div');
    wrap.className = 'msg ' + (m.sender_id == currentUserId ? 'me' : 'them');
    wrap.dataset.id = m.id;

    let inner = '';
    if(m.shared_post_id){
      inner = `
        <div class="border rounded p-2 bg-light">
          <div class="small text-muted">Shared a post</div>
          <div><a href="#post-${m.shared_post_id}">Open post</a></div>
        </div>`;
    } else if(m.media){
      const url = `/static/uploads/chat_media/${m.media}`;
      const ext = (m.media.split('.').pop()||'').toLowerCase();
      if(['png','jpg','jpeg','gif'].includes(ext)){
        inner = `<img src="${url}" style="max-width:240px; border-radius:8px;">`;
      } else if(['mp4','webm'].includes(ext)){
        inner = `<video src="${url}" controls style="max-width:240px;"></video>`;
      } else {
        inner = `<a href="${url}" target="_blank">Download ${escapeHtml(m.media)}</a>`;
      }
    } else if(m.gif_url){
      inner = `<img src="${m.gif_url}" style="max-width:240px; border-radius:8px;">`;
    } else {
      inner = escapeHtml(m.content);
    }

    if (m.is_forwarded && m.forwarded_from) {
      inner = `<div class="forwarded-from small text-muted mb-1"><i>Forwarded from <b>${escapeHtml(m.forwarded_from.username)}</b></i></div>` + inner;
    }

    if (m.replied_to) {
      let replyContent = '';
      if (m.replied_to.gif_url) {
        replyContent = '<img src="' + m.replied_to.gif_url + '" style="max-height: 30px; border-radius: 4px;">';
      } else if (m.replied_to.media) {
        replyContent = '<i>Media</i>';
      } else {
        replyContent = escapeHtml(m.replied_to.content);
      }
      inner = `<div class="replied-to small text-muted p-2 border rounded mb-2">
        Replying to <b>${escapeHtml(m.replied_to.sender_name)}</b>: ${replyContent}
      </div>` + inner;
    }

    wrap.innerHTML = `<div class="bubble">
      <div class="meta small text-muted">
        <span class="sender">${escapeHtml(m.sender_name)}</span> • <span class="time">${new Date(m.timestamp).toLocaleString()}</span>
        ${m.sender_id===currentUserId?'<button class="btn btn-link btn-sm p-0 ms-2 text-danger msg-delete" data-id="'+m.id+'">delete</button>':''}
        <button class="btn btn-link btn-sm p-0 ms-2 msg-reply" data-id="${m.id}" data-sender="${escapeHtml(m.sender_name)}" data-content="${escapeHtml(m.content)}">reply</button>
        <button class="btn btn-link btn-sm p-0 ms-2 msg-forward" data-id="${m.id}">forward</button>
      </div>
      <div class="content">${inner}</div>
      <div class="status">${m.sender_id === currentUserId ? getStatusIcon(m.status) : ''}</div>
    </div>`;
    chatWindow.appendChild(wrap);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  function getStatusIcon(status) {
    if (status === 'seen') {
      return '<i class="bi bi-check2-all seen"></i>'; // Blue double check
    } else if (status === 'delivered') {
      return '<i class="bi bi-check2-all"></i>'; // Grey double check
    } else if (status === 'sent') {
      return '<i class="bi bi-check"></i>'; // Single check
    }
    return '';
  }

  chatWindow.addEventListener('click', (e)=>{
    const deleteBtn = e.target.closest('.msg-delete');
    if(deleteBtn) {
      const id = deleteBtn.dataset.id;
      fetch(`/messages/api/delete/${id}`, {method:'POST'})
        .then(r=>r.json()).then(res=>{ if(res.ok){ const el = document.querySelector('.msg[data-id="'+id+'"]'); if(el) el.remove(); } });
      return;
    }

    const replyBtn = e.target.closest('.msg-reply');
    if(replyBtn) {
      replyToId = replyBtn.dataset.id;
      replyToName.textContent = replyBtn.dataset.sender;
      replyToContent.textContent = replyBtn.dataset.content;
      replyBanner.classList.remove('d-none');
      sendInput.focus();
      return;
    }

    const forwardBtn = e.target.closest('.msg-forward');
    if (forwardBtn) {
      forwardMsgId = forwardBtn.dataset.id;
      fetch('/messages/api/get_chats')
        .then(r => r.json())
        .then(data => {
          forwardChatList.innerHTML = '';
          data.chats.forEach(chat => {
            const div = document.createElement('div');
            div.className = 'form-check';
            div.innerHTML = `<input class="form-check-input" type="checkbox" value="${chat.id}" id="chat-${chat.id}">
                             <label class="form-check-label" for="chat-${chat.id}">${escapeHtml(chat.name)}</label>`;
            forwardChatList.appendChild(div);
          });
          forwardModal.show();
        });
      return;
    }
  });

  cancelReplyBtn.addEventListener('click', () => {
    replyToId = null;
    replyBanner.classList.add('d-none');
  });

  forwardSendBtn.addEventListener('click', () => {
    const selectedChats = Array.from(forwardChatList.querySelectorAll('input:checked')).map(input => input.value);
    if (selectedChats.length > 0 && forwardMsgId) {
      const fd = new FormData();
      fd.append('message_id', forwardMsgId);
      fd.append('chat_ids', selectedChats.join(','));
      fetch('/messages/api/forward', { method: 'POST', body: fd })
        .then(r => r.json())
        .then(res => {
          if (res.ok) {
            forwardModal.hide();
          }
        });
    }
  });

  sendBtn.addEventListener('click', async ()=>{
    const content = sendInput.value.trim();
    if (!content && (!mediaInput || !mediaInput.files || mediaInput.files.length === 0)) return;
    
    const fd = new FormData();
    fd.append('chat_id', chatId);
    if(content) fd.append('content', content);
    if(replyToId) fd.append('reply_to_id', replyToId);
    if(mediaInput && mediaInput.files && mediaInput.files.length>0){
      fd.append('media', mediaInput.files[0]);
    }
    
    // Disable button during send to prevent double sends
    sendBtn.disabled = true;
    sendBtn.textContent = 'Sending...';
    
    try {
      const r = await fetch('/messages/api/send', {method:'POST', body: fd});
      const j = await r.json();
      if(j.ok){ 
        sendInput.value=''; 
        if(mediaInput) mediaInput.value='';
      }
    } catch(e) {
      // Silent fail for better UX
    } finally {
      // Re-enable button
      sendBtn.disabled = false;
      sendBtn.textContent = 'Send';
    }
  });

  sendInput.addEventListener('keydown', (e)=>{ if(e.key==='Enter'){ e.preventDefault(); sendBtn.click(); } });

  gifBtn.addEventListener('click', ()=>{ gifModal.classList.toggle('d-none'); });
  gifSearch.addEventListener('click', async ()=>{
    const q = gifQuery.value.trim(); if(!q) return; gifResults.innerHTML='Searching...';
    try{
      const r = await fetch(`/giphy_search?q=${encodeURIComponent(q)}`);
      const j = await r.json();
      gifResults.innerHTML='';
      (j.data||[]).forEach(g => {
        const url = g.images.fixed_width.url;
        const img = document.createElement('img'); img.src = url;
        img.addEventListener('click', ()=>{
          const fd = new FormData(); fd.append('chat_id', chatId); fd.append('gif', url);
          fetch('/messages/api/send', {method:'POST', body:fd})
            .then(r=>r.json()).then(res=>{ if(res.ok){ gifModal.classList.add('d-none'); } });
        });
        gifResults.appendChild(img);
      });
    }catch(e){ gifResults.innerHTML='Failed'; }
  });

  // Use requestAnimationFrame for smoother scrolling
  function smoothScrollToBottom() {
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  socket.on('connect', () => {
    socket.emit('join', {room: `chat_${chatId}`});
  });

  socket.on('new_message', (data) => {
    if (data.message) {
        appendMessage(data.message);
        if (data.message.sender_id !== currentUserId) {
            socket.emit('message_delivered', { message_id: data.message.id });
        }
    }
  });

  socket.on('status_update', (data) => {
    if (data.message_id) {
        const msgElement = document.querySelector(`.msg[data-id="${data.message_id}"] .status`);
        if (msgElement) {
            msgElement.innerHTML = getStatusIcon(data.status);
        }
    } else if (data.message_ids) {
        data.message_ids.forEach(id => {
            const msgElement = document.querySelector(`.msg[data-id="${id}"] .status`);
            if (msgElement) {
                msgElement.innerHTML = getStatusIcon(data.status);
            }
        });
    }
  });

  // When chat is opened, mark messages as seen
  socket.emit('messages_seen', { chat_id: chatId });
  
  // Scroll to bottom on load
  requestAnimationFrame(smoothScrollToBottom);
})();
