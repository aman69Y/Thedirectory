
(function(){
  const chatWindow = document.getElementById('chat-window');
  if(!chatWindow) return;
  const chatId = chatWindow.dataset.chatId;
  const sendInput = document.getElementById('send-input');
  const sendBtn = document.getElementById('send-btn');
  const gifBtn = document.getElementById('gif-btn');
  const gifModal = document.getElementById('gif-search-modal');
  const gifQuery = document.getElementById('gif-query');
  const gifSearch = document.getElementById('gif-search');
  const gifResults = document.getElementById('gif-results');
  const mediaInput = document.getElementById('chat-media');
  let lastId = 0;

  function escapeHtml(s){ return (s||'').replace(/[&<>"']/g, m=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[m])); }

  function appendMessage(m){
    lastId = Math.max(lastId, m.id);
    const wrap = document.createElement('div');
    wrap.className = 'msg ' + (m.sender_id === window.__CURRENT_USER_ID__ ? 'me' : 'them');
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

    wrap.innerHTML = `<div class="bubble">
      <div class="meta small text-muted">
        <span class="sender">${escapeHtml(m.sender_name)}</span> • <span class="time">${new Date(m.timestamp).toLocaleString()}</span>
        ${m.sender_id===window.__CURRENT_USER_ID__?'<button class="btn btn-link btn-sm p-0 ms-2 text-danger msg-delete" data-id="'+m.id+'">delete</button>':''}
      </div>
      <div class="content">${inner}</div>
    </div>`;
    chatWindow.appendChild(wrap);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  async function fetchMessages(){
    try{
      const r = await fetch(`/messages/api/messages?chat_id=${chatId}&after_id=${lastId}`);
      const j = await r.json();
      if(j.messages) j.messages.forEach(appendMessage);
    }catch(e){
      // Silent fail for better UX
    }
  }

  chatWindow.addEventListener('click', (e)=>{
    const btn = e.target.closest('.msg-delete');
    if(!btn) return;
    const id = btn.dataset.id;
    fetch(`/messages/api/delete/${id}`, {method:'POST'})
      .then(r=>r.json()).then(res=>{ if(res.ok){ const el = document.querySelector('.msg[data-id="'+id+'"]'); if(el) el.remove(); } });
  });

  sendBtn.addEventListener('click', async ()=>{
    const content = sendInput.value.trim();
    if (!content && (!mediaInput || !mediaInput.files || mediaInput.files.length === 0)) return;
    
    const fd = new FormData();
    fd.append('chat_id', chatId);
    if(content) fd.append('content', content);
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
        fetchMessages(); 
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
            .then(r=>r.json()).then(res=>{ if(res.ok){ fetchMessages(); gifModal.classList.add('d-none'); } });
        });
        gifResults.appendChild(img);
      });
    }catch(e){ gifResults.innerHTML='Failed'; }
  });

  const items = chatWindow.querySelectorAll('.msg');
  items.forEach(el=> lastId = Math.max(lastId, parseInt(el.dataset.id||'0')));
  fetchMessages(); 
  
  // Use requestAnimationFrame for smoother scrolling
  function smoothScrollToBottom() {
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }
  
  // Throttle message fetching to prevent excessive requests
  let fetching = false;
  async function throttledFetchMessages() {
    if (fetching) return;
    fetching = true;
    await fetchMessages();
    fetching = false;
  }
  
  // Fetch messages every 3 seconds instead of 2 for better performance
  setInterval(throttledFetchMessages, 3000);
  
  // Scroll to bottom on load
  requestAnimationFrame(smoothScrollToBottom);
})();
