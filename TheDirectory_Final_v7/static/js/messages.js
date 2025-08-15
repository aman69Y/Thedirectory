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
  let lastId = 0;
  function appendMessage(m){
    lastId = Math.max(lastId, m.id);
    const wrap = document.createElement('div');
    wrap.className = 'msg ' + (m.sender_id === window.__CURRENT_USER_ID__ ? 'me' : 'them');
    wrap.dataset.id = m.id;
    const content = m.gif_url ? (`<img src="${m.gif_url}" style="max-width:240px; border-radius:8px;">`) : (m.content || '');
    wrap.innerHTML = `<div class="bubble"><div class="meta small text-muted"><span class="sender">${m.sender_name}</span> • <span class="time">${new Date(m.timestamp).toLocaleString()}</span>${m.sender_id===window.__CURRENT_USER_ID__?'<button class="btn btn-link btn-sm p-0 ms-2 text-danger msg-delete" data-id="'+m.id+'">delete</button>':''}</div><div class="content">${content}</div></div>`;
    chatWindow.appendChild(wrap); chatWindow.scrollTop = chatWindow.scrollHeight;
  }
  async function fetchMessages(){
    try{
      const r = await fetch(`/messages/api/messages?chat_id=${chatId}&after_id=${lastId}`);
      const j = await r.json();
      if(j.messages) j.messages.forEach(appendMessage);
    }catch(e){}
  }
  chatWindow.addEventListener('click', (e)=>{
    const btn = e.target.closest('.msg-delete');
    if(!btn) return;
    const id = btn.dataset.id;
    fetch(`/messages/api/delete/${id}`, {method:'POST'}).then(r=>r.json()).then(res=>{ if(res.ok){ const el = document.querySelector('.msg[data-id="'+id+'"]').remove(); } });
  });
  sendBtn.addEventListener('click', async ()=>{
    const content = sendInput.value.trim(); if(!content) return;
    const fd = new FormData(); fd.append('chat_id', chatId); fd.append('content', content);
    const r = await fetch('/messages/api/send', {method:'POST', body: fd}); const j = await r.json();
    if(j.ok){ sendInput.value=''; fetchMessages(); }
  });
  sendInput.addEventListener('keydown', (e)=>{ if(e.key==='Enter'){ e.preventDefault(); sendBtn.click(); } });
  gifBtn.addEventListener('click', ()=>{ gifModal.classList.toggle('d-none'); });
  gifSearch.addEventListener('click', async ()=>{
    const q = gifQuery.value.trim(); if(!q) return; gifResults.innerHTML='Searching...';
    try{
      const r = await fetch(`/giphy_search?q=${encodeURIComponent(q)}`); const j = await r.json();
      gifResults.innerHTML='';
      (j.data||[]).forEach(g => {
        const url = g.images.fixed_width.url; const img = document.createElement('img'); img.src = url; img.addEventListener('click', ()=>{ const fd = new FormData(); fd.append('chat_id', chatId); fd.append('gif', url); fetch('/messages/api/send', {method:'POST', body:fd}).then(r=>r.json()).then(res=>{ if(res.ok){ fetchMessages(); gifModal.classList.add('d-none'); } }); }); gifResults.appendChild(img);
      });
    }catch(e){ gifResults.innerHTML='Failed'; }
  });
  const items = chatWindow.querySelectorAll('.msg'); items.forEach(el=> lastId = Math.max(lastId, parseInt(el.dataset.id||'0')));
  fetchMessages(); setInterval(fetchMessages, 2000);
})();