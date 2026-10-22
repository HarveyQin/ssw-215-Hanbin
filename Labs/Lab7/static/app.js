const filterInput = document.getElementById('filter-input');
const projectCount = document.getElementById('project-count');
const cards = Array.from(document.querySelectorAll('.card'));

function updateProjectList() {
  const query = filterInput.value.trim().toLowerCase();
  let visibleCount = 0;

  cards.forEach((card) => {
    const text = card.textContent.toLowerCase();
    const matches = text.includes(query);

    card.classList.toggle('hidden', !matches);

    if (matches) {
      visibleCount += 1;
    }
  });

  projectCount.textContent = `Showing ${visibleCount} of ${cards.length} projects`;
}

if (filterInput && projectCount && cards.length > 0) {
  filterInput.addEventListener('input', updateProjectList);
  updateProjectList();
}

cards.forEach((card) => {
  const upvoteButton = card.querySelector('.upvote-btn');
  const likeCount = card.querySelector('.like-count');

  if (!upvoteButton || !likeCount) {
    return;
  }

  upvoteButton.addEventListener('click', async () => {
    const projectId = card.dataset.projectId;

    try {
      const response = await fetch(`/api/projects/${projectId}/upvote`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Upvote failed with status ${response.status}`);
      }

      const result = await response.json();
      likeCount.textContent = result.likes;
    } catch (error) {
      console.error('Unable to upvote project:', error);
    }
  });
});
