document.addEventListener('DOMContentLoaded', ()=>{
  // posting AJAX
  const postForm = document.getElementById('post-form');
  if(postForm){
    postForm.addEventListener('submit', async (e)=>{
      e.preventDefault();
      const fd = new FormData(postForm);
      const res = await fetch('/post_ajax', {method:'POST', body:fd});
      const data = await res.json();
      if(data.ok){
        const postsList = document.getElementById('posts-list');
        postsList.insertAdjacentHTML('afterbegin', data.html);
        document.getElementById('post-content').value = '';
        const newPost = document.getElementById('post-'+data.post_id);
        if(newPost) newPost.scrollIntoView({behavior:'smooth'});
      } else {
        alert(data.error || 'Failed to post');
      }
    });
  }

  // delegated clicks
  document.addEventListener('click', async (e)=>{
    const likeBtn = e.target.closest('.like-btn');
    if(likeBtn){
      const id = likeBtn.dataset.id;
      const res = await fetch(`/like_ajax/${id}`, {method:'POST'});
      const data = await res.json();
      if(data.ok) likeBtn.querySelector('.like-count').textContent = data.count;
      return;
    }

    const delPost = e.target.closest('.delete-post-btn');
    if(delPost){
      const id = delPost.dataset.id;
      if(!confirm('Delete post?')) return;
      const res = await fetch(`/delete_post_ajax/${id}`, {method:'POST'});
      const data = await res.json();
      if(data.ok){
        const el = document.getElementById('post-'+id); if(el) el.remove();
      }
      return;
    }

    const delC = e.target.closest('.delete-comment-btn');
    if(delC){
      const id = delC.dataset.id;
      if(!confirm('Delete comment?')) return;
      const res = await fetch(`/delete_comment_ajax/${id}`, {method:'POST'});
      const data = await res.json();
      if(data.ok){ const el = document.getElementById('comment-'+id); if(el) el.remove(); }
      return;
    }

    const commentSend = e.target.closest('.comment-send');
    if(commentSend){
      e.preventDefault();
      const form = commentSend.closest('.comment-form');
      const postId = form.dataset.postId;
      const input = form.querySelector('.comment-input');
      const fd = new FormData(); fd.append('comment', input.value);
      const res = await fetch(`/comment_ajax/${postId}`, {method:'POST', body:fd});
      const data = await res.json();
      if(data.ok){
        const list = form.closest('.comments').querySelector('.comments-list');
        list.insertAdjacentHTML('beforeend', data.html); input.value='';
      } else { alert(data.error || 'Failed'); }
      return;
    }

    const shareBtn = e.target.closest('.share-post-btn');
    if(shareBtn){
      const pid = shareBtn.dataset.id;
      const modal = new bootstrap.Modal(document.getElementById('shareModal'));
      document.getElementById('share-post-id').value = pid;
      modal.show();
      return;
    }

    const markBtn = e.target.closest('.mark-read-btn');
    if(markBtn){
      const id = markBtn.dataset.id;
      fetch(`/notifications/read/${id}`, {method:'POST'}).then(()=>{ markBtn.remove(); });
      return;
    }
  });

  // share confirm
  const shareConfirm = document.getElementById('share-confirm');
  if(shareConfirm){
    shareConfirm.addEventListener('click', async ()=>{
      const pid = document.getElementById('share-post-id').value;
      const fid = document.getElementById('share-friend').value;
      if(!fid) return alert('Choose a friend');
      const fd = new FormData();
      fd.append('post_id', pid); fd.append('friend_id', fid);
      const res = await fetch('/share_post', {method:'POST', body:fd});
      const j = await res.json();
      if(j.ok){ bootstrap.Modal.getInstance(document.getElementById('shareModal')).hide(); alert('Shared'); }
      else alert(j.error || 'Failed to share');
    });
  }

  async function pollNotifs(){ try{ const r = await fetch('/notifications/count'); const j = await r.json(); const badge = document.getElementById('notif-badge'); if(badge) badge.textContent = j.count || 0; }catch(e){} }
  setInterval(pollNotifs, 4000); pollNotifs();
});
