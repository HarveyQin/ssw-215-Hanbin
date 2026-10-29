const filterInput = document.getElementById('filter-input');
const projectCount = document.getElementById('project-count');
const cardGrid = document.querySelector('.card-grid');
const projectForm = document.getElementById('project-form');
const newTitleInput = document.getElementById('new-title');
const createStatus = document.getElementById('create-status');

function updateProjectList() {
  const cards = Array.from(document.querySelectorAll('.card'));
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

if (filterInput && projectCount) {
  filterInput.addEventListener('input', updateProjectList);
  updateProjectList();
}

function createProjectCard(project) {
  const card = document.createElement('article');
  card.className = 'card';
  card.dataset.projectId = project.id;

  if (project.likes > 10) {
    const badge = document.createElement('span');
    badge.className = 'badge';
    badge.textContent = 'Trending';
    card.append(badge);
  }

  const title = document.createElement('h3');
  title.textContent = project.title;
  card.append(title);

  const description = document.createElement('p');
  description.textContent = project.description;
  card.append(description);

  const likes = document.createElement('p');
  likes.append('Likes: ');
  const likeCount = document.createElement('span');
  likeCount.className = 'like-count';
  likeCount.textContent = project.likes;
  likes.append(likeCount);
  card.append(likes);

  const upvoteButton = document.createElement('button');
  upvoteButton.className = 'upvote-btn';
  upvoteButton.type = 'button';
  upvoteButton.textContent = 'Upvote';
  card.append(upvoteButton);

  return card;
}

if (cardGrid) {
  cardGrid.addEventListener('click', async (event) => {
    if (!(event.target instanceof Element)) {
      return;
    }

    const upvoteButton = event.target.closest('.upvote-btn');
    if (!upvoteButton || !cardGrid.contains(upvoteButton)) {
      return;
    }

    const card = upvoteButton.closest('.card');
    const likeCount = card && card.querySelector('.like-count');
    if (!card || !likeCount) {
      return;
    }

    try {
      const response = await fetch(`/api/projects/${card.dataset.projectId}/upvote`, {
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
}

if (projectForm && newTitleInput && createStatus && cardGrid) {
  projectForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    createStatus.textContent = '';

    try {
      const response = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitleInput.value }),
      });

      if (!response.ok) {
        throw new Error(`Project creation failed with status ${response.status}`);
      }

      const project = await response.json();
      cardGrid.append(createProjectCard(project));
      newTitleInput.value = '';
      updateProjectList();
      createStatus.textContent = 'Project added.';
    } catch (error) {
      console.error('Unable to create project:', error);
      createStatus.textContent = 'Unable to add project. Please try again.';
    }
  });
}
