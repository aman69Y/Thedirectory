
(function(){
  // Post preview logic
  const postFormForPreview = document.getElementById('post-form');
  if (postFormForPreview) {
      const contentInput = postFormForPreview.querySelector('textarea[name="content"]');
      const mediaInput = postFormForPreview.querySelector('input[name="media"]');
      const previewContainer = document.getElementById('post-preview-container');
      const previewImage = document.getElementById('preview-media-image');
      const previewVideo = document.getElementById('preview-media-video');

      function updatePreview() {
          if (!previewContainer) return; // if preview elements are not on the page
          const file = mediaInput.files[0];

          // Reset media previews
          previewImage.style.display = 'none';
          previewImage.src = '';
          previewVideo.style.display = 'none';
          previewVideo.src = '';

          if (file) {
              previewContainer.style.display = 'block';
              const reader = new FileReader();
              reader.onload = (e) => {
                  if (file.type.startsWith('image/')) {
                      previewImage.src = e.target.result;
                      previewImage.style.display = 'block';
                  } else if (file.type.startsWith('video/')) {
                      previewVideo.src = e.target.result;
                      previewVideo.style.display = 'block';
                  }
              };
              reader.readAsDataURL(file);
          } else {
              previewContainer.style.display = 'none';
          }
      }

      mediaInput.addEventListener('change', updatePreview);
  }

  const imageModal = document.getElementById('imageModal');
  const imageModalImg = document.getElementById('imageModalImg');
  if(imageModal && imageModalImg){
    document.addEventListener('click', (e)=>{
      const img = e.target.closest('.post-media');
      if(!img) return;
      imageModalImg.src = img.dataset.src || img.src;
      const modal = new bootstrap.Modal(imageModal); modal.show();
    });
  }

  const postForm = document.getElementById('post-form');
  if(postForm){
    postForm.addEventListener('submit', async (e)=>{
      e.preventDefault();
      const fd = new FormData(postForm);
      const r = await fetch('/post_ajax', {method:'POST', body:fd});
      const j = await r.json();
      if(j.ok){
        const feed = document.getElementById('feed-list');
        const temp = document.createElement('div'); temp.innerHTML = j.html;
        feed.prepend(temp.firstElementChild);
        postForm.reset();
        // Clear preview after posting
        const previewContainer = document.getElementById('post-preview-container');
        if (previewContainer) {
          previewContainer.style.display = 'none';
          const previewImage = document.getElementById('preview-media-image');
          const previewVideo = document.getElementById('preview-media-video');
          if (previewImage) previewImage.src = '';
          if (previewVideo) previewVideo.src = '';
        }
      }
    });
  }

  document.addEventListener('click', async (e)=>{
    const btn = e.target.closest('.like-btn'); if(!btn) return;
    const id = e.target.closest('.like-btn').dataset.id;
    
    // Add visual feedback immediately
    const likeBtn = e.target.closest('.like-btn');
    const likeCount = likeBtn.querySelector('.like-count');
    const isLiked = likeBtn.classList.contains('btn-danger');
    
    // Toggle UI immediately for better responsiveness
    if (isLiked) {
      likeBtn.classList.remove('btn-danger');
      likeBtn.classList.add('btn-outline-secondary');
    } else {
      likeBtn.classList.add('btn-danger');
      likeBtn.classList.remove('btn-outline-secondary');
    }
    
    try {
      const r = await fetch(`/like_ajax/${id}`, {method:'POST'});
      const j = await r.json();
      likeCount.textContent = j.count;
    } catch (error) {
      // Revert UI changes if request fails
      if (isLiked) {
        likeBtn.classList.add('btn-danger');
        likeBtn.classList.remove('btn-outline-secondary');
      } else {
        likeBtn.classList.remove('btn-danger');
        likeBtn.classList.add('btn-outline-secondary');
      }
    }
  });

  document.addEventListener('submit', async function(e) {
    if (!e.target.classList.contains('comment-form')) return;
    e.preventDefault();
    const postId = e.target.dataset.postId;
    const input = e.target.querySelector('.comment-input');
    const content = input.value.trim();
    if (!content) return;
    const r = await fetch(`/comment_ajax/${postId}`, {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:`comment=${encodeURIComponent(content)}`});
    const j = await r.json();
    if(j.ok){
      const commentsList = document.querySelector(`.comments[data-post-id="${postId}"] .comments-list`);
      const temp = document.createElement('div'); temp.innerHTML = j.html;
      commentsList.appendChild(temp.firstElementChild);
      input.value = '';
    }
  });

  // Handle show more comments
  document.addEventListener('click', function(e) {
    if (!e.target.classList.contains('show-more-comments')) return;
    const postId = e.target.dataset.postId;
    const hiddenComments = document.querySelector(`#post-${postId} .hidden-comments`);
    
    if (hiddenComments) {
      hiddenComments.classList.remove('d-none');
      e.target.remove();
    }
  });

  // Handle hide comments
  document.addEventListener('click', function(e) {
    if (!e.target.classList.contains('hide-comments')) return;
    const postId = e.target.dataset.postId;
    const hiddenComments = document.querySelector(`#post-${postId} .hidden-comments`);
    const commentsList = document.querySelector(`#post-${postId} .comments-list`);
    
    if (hiddenComments && commentsList) {
      // Hide the hidden comments section
      hiddenComments.classList.add('d-none');
      
      // Remove all comments from the comments list except the first 3
      const allComments = commentsList.querySelectorAll('.comment');
      for (let i = 3; i < allComments.length; i++) {
        allComments[i].remove();
      }
      
      // Remove the hide comments button if it exists
      const hideBtn = commentsList.querySelector('.hide-comments');
      if (hideBtn) hideBtn.remove();
      
      // Add the show more button
      const showMoreBtn = document.createElement('button');
      showMoreBtn.className = 'btn btn-sm btn-outline-secondary show-more-comments';
      showMoreBtn.dataset.postId = postId;
      showMoreBtn.textContent = 'Show more comments';
      commentsList.appendChild(showMoreBtn);
    }
  });

  document.addEventListener('click', async function(e) {
    if (!e.target.classList.contains('delete-post-btn')) return;
    const id = e.target.dataset.id;
    
    // Add confirmation dialog
    if (!confirm('Are you sure you want to delete this post?')) return;
    
    try {
      const r = await fetch(`/delete_post_ajax/${id}`, {method:'POST'});
      const j = await r.json();
      if(j.ok){ 
        const postElement = document.getElementById(`post-${id}`);
        if (postElement) {
          postElement.remove();
        }
      }
    } catch (error) {
      // Silent fail for better UX
    }
  });

  const shareModalEl = document.getElementById('shareModal');
  let shareModal = null; if(shareModalEl){ shareModal = new bootstrap.Modal(shareModalEl); }
  const shareFriendSelect = document.getElementById('share-friend-select');
  document.addEventListener('click', (e)=>{
    const btn = e.target.closest('.share-post-btn'); if(!btn) return;
    document.getElementById('share-post-id').value = btn.dataset.id;
    fetch('/friends_list_json').then(r=>r.json()).then(j=>{
      shareFriendSelect.innerHTML = '';
      (j.friends||[]).forEach(f=>{
        const opt = document.createElement('option'); opt.value=f.id; opt.textContent='@'+f.username;
        shareFriendSelect.appendChild(opt);
      });
      shareModal.show();
    });
  });
  const shareConfirmBtn = document.getElementById('share-confirm-btn');
  if(shareConfirmBtn){
    shareConfirmBtn.addEventListener('click', ()=>{
      const postId = document.getElementById('share-post-id').value;
      const friendId = shareFriendSelect.value;
      const fd = new FormData(); fd.append('post_id', postId); fd.append('friend_id', friendId);
      fetch('/share_post', {method:'POST', body:fd}).then(r=>r.json()).then(j=>{
        if(j.ok){ shareModal.hide(); }
      });
    });
  }

  document.addEventListener('click', (e)=>{
    const btn = e.target.closest('.mark-read-btn'); if(!btn) return;
    fetch(`/notifications/mark_read/${btn.dataset.id}`, {method:'POST'}).then(r=>r.json()).then(j=>{
      if(j.ok){ btn.closest('li').classList.remove('fw-bold'); }
    });
  });

  // Real-time notification updates
  function updateNotifications() {
    fetch('/notifications/api/notifications').then(r=>r.json()).then(j=>{
      const notifCount = j.notifications.filter(n => !n.is_read).length;
      const notifBadge = document.getElementById('notification-badge');
      if (notifBadge) {
        notifBadge.textContent = notifCount;
        notifBadge.classList.toggle('d-none', notifCount === 0);
      }
    });
  }

  // Update notifications every 30 seconds
  setInterval(updateNotifications, 30000);
  // Initial update
  updateNotifications();
})();
