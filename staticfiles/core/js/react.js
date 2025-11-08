document.addEventListener("DOMContentLoaded", () => {
    const buttons = document.querySelectorAll('.react-btn');

    buttons.forEach(button => {
        button.addEventListener('click', () => {
            const storyId = button.dataset.storyId;
            const reactionType = button.dataset.reaction;

            fetch(`/stories/${storyId}/react/${reactionType}/`)
                .then(response => response.json())
                .then(data => {
                    const parent = button.parentElement;

                    // Update counts
                    parent.querySelector('[data-reaction="heart"] .reaction-count').textContent = data.reactions_count.heart;
                    parent.querySelector('[data-reaction="hug"] .reaction-count').textContent = data.reactions_count.hug;
                    parent.querySelector('[data-reaction="hands"] .reaction-count').textContent = data.reactions_count.hands;

                    // Remove active from all buttons
                    parent.querySelectorAll('.react-btn').forEach(btn => btn.classList.remove('active', 'btn-danger', 'btn-warning', 'btn-primary'));

                    // Highlight the button the user clicked
                    if (data.reacted === reactionType) {
                        if (reactionType === 'heart') button.classList.add('active', 'btn-danger');
                        if (reactionType === 'hug') button.classList.add('active', 'btn-warning');
                        if (reactionType === 'hands') button.classList.add('active', 'btn-primary');
                    }
                })
                .catch(error => console.error('Error:', error));
        });
    });
});
