// static/core/js/react.js
document.addEventListener('DOMContentLoaded', () => {
  // select all reaction buttons rendered in stories.html
  const reactionButtons = document.querySelectorAll('.reaction-btn');

  reactionButtons.forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();

      const storyId = btn.dataset.storyId;
      const reactionType = btn.dataset.reactionType;
      if (!storyId || !reactionType) return;

      // URL pattern expected by your Django view:
      // react_to_story(request, story_id, reaction_type)
      const url = `/react_to_story/${storyId}/${reactionType}/`;

      try {
        const resp = await fetch(url, {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Accept': 'application/json'
          },
          credentials: 'same-origin'
        });

        // If user not logged in, view may redirect — handle common cases:
        if (resp.status === 403 || resp.status === 401) {
          // not authorized -> redirect to login
          window.location.href = '/login/';
          return;
        }

        if (!resp.ok) {
          console.error('Reaction request failed', resp.status);
          return;
        }

        const data = await resp.json();

        // Your view returns { "reactions_count": {...}, "reacted": <reactionType|null> }
        const counts = data.reactions_count || data.reactions_count || data.counts || {};
        const reacted = data.reacted ?? data.user_reacted ?? null;

        // Update counts for each reaction button belonging to this story
        const storyBtns = document.querySelectorAll(`.reaction-btn[data-story-id="${storyId}"]`);
        storyBtns.forEach(b => {
          const type = b.dataset.reactionType;
          // Update the numeric span inside the button
          const span = b.querySelector('span');
          if (span) {
            // counts could be keys like 'heart','hug','hands'
            span.textContent = counts[type] ?? span.textContent;
          }
          // Manage active state: if server says reacted === type, mark active; otherwise remove
          if (reacted && reacted === type) {
            b.classList.add('active');
          } else {
            b.classList.remove('active');
          }
        });

      } catch (err) {
        console.error('Error reacting to story:', err);
      }
    });
  });
});

/**
 * Minimal getCookie helper to fetch CSRF token from cookies
 */
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}
