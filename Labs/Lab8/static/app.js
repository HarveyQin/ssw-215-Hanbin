const filterInput = document.getElementById('filter-input');
const projectCount = document.getElementById('project-count');
const addTitleInput = document.getElementById('new-title');
const addProjectBtn = document.getElementById('add-project-btn');
const cardGrid = document.querySelector('.card-grid');

function updateProjectList() {
  const cards = Array.from(document.querySelectorAll('.card'));
  const query = filterInput ? filterInput.value.trim().toLowerCase() : '';
  let visibleCount = 0;

  cards.forEach((card) => {
    const text = card.textContent.toLowerCase();
    const matches = text.includes(query);

    card.classList.toggle('hidden', !matches);

    if (matches) {
      visibleCount += 1;
    }
  });

  if (projectCount) {
    projectCount.textContent = `Showing ${visibleCount} of ${cards.length} projects`;
  }
}

function bindCardEvents(card) {
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

      if (Number(result.likes) > 10 && !card.querySelector('.badge')) {
        const badge = document.createElement('span');
        badge.className = 'badge';
        badge.textContent = 'Trending';
        card.insertBefore(badge, card.firstChild);
      }
    } catch (error) {
      console.error('Unable to upvote project:', error);
    }
  });
}

function createProjectCard(project) {
  const card = document.createElement('article');
  card.className = 'card';
  card.dataset.projectId = project.id;

  const trending = project.likes > 10;

  if (trending) {
    const badge = document.createElement('span');
    badge.className = 'badge';
    badge.textContent = 'Trending';
    card.appendChild(badge);
  }

  const header = document.createElement('h3');
  header.textContent = project.title;

  const description = document.createElement('p');
  description.textContent = project.description;

  const likesText = document.createElement('p');
  likesText.innerHTML = 'Likes: <span class="like-count">' + project.likes + '</span>';

  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'upvote-btn';
  button.textContent = 'Upvote';

  card.appendChild(header);
  card.appendChild(description);
  card.appendChild(likesText);
  card.appendChild(button);

  bindCardEvents(card);
  return card;
}

if (filterInput && projectCount) {
  filterInput.addEventListener('input', updateProjectList);
}

if (addProjectBtn && addTitleInput && cardGrid) {
  addProjectBtn.addEventListener('click', async () => {
    const title = addTitleInput.value.trim();

    if (!title) {
      addTitleInput.focus();
      return;
    }

    try {
      const response = await fetch('/api/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title }),
      });

      if (!response.ok) {
        throw new Error(`Create failed with status ${response.status}`);
      }

      const project = await response.json();
      const newCard = createProjectCard(project);
      cardGrid.appendChild(newCard);
      addTitleInput.value = '';
      updateProjectList();
    } catch (error) {
      console.error('Unable to create project:', error);
    }
  });
}

document.querySelectorAll('.card').forEach((card) => {
  bindCardEvents(card);
});

if (filterInput && projectCount) {
  updateProjectList();
}
