const filterInput = document.getElementById('filter-input');
const projectCount = document.getElementById('project-count');
const addTitleInput = document.getElementById('new-title');
const addProjectBtn = document.getElementById('add-project-btn');
const smartNotes = document.getElementById('smart-notes');
const smartCreateBtn = document.getElementById('smart-create-btn');
const smartCreateStatus = document.getElementById('smart-create-status');
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
    try {
      const response = await fetch(`/api/projects/${card.dataset.projectId}/upvote`, {
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

  if (project.likes > 10) {
    const badge = document.createElement('span');
    badge.className = 'badge';
    badge.textContent = 'Trending';
    card.appendChild(badge);
  }

  const title = document.createElement('h3');
  title.textContent = project.title;
  card.appendChild(title);

  const summary = document.createElement('p');
  summary.textContent = project.summary || project.description || '';
  card.appendChild(summary);

  if (project.technologies) {
    const technologies = document.createElement('p');
    technologies.className = 'project-technologies';
    technologies.textContent = `Technologies: ${project.technologies}`;
    card.appendChild(technologies);
  }

  const author = document.createElement('p');
  author.className = 'project-author';
  author.textContent = `Author: ${project.author || project.author_name || ''}`;
  card.appendChild(author);

  const likes = document.createElement('p');
  likes.append('Likes: ');
  const likeCount = document.createElement('span');
  likeCount.className = 'like-count';
  likeCount.textContent = project.likes;
  likes.appendChild(likeCount);
  card.appendChild(likes);

  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'upvote-btn';
  button.textContent = 'Upvote';
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
      cardGrid.appendChild(createProjectCard(project));
      addTitleInput.value = '';
      updateProjectList();
    } catch (error) {
      console.error('Unable to create project:', error);
    }
  });
}

if (smartCreateBtn && smartNotes && smartCreateStatus && cardGrid) {
  smartCreateBtn.addEventListener('click', async () => {
    smartCreateStatus.textContent = '';

    try {
      const response = await fetch('/api/projects/smart', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ notes: smartNotes.value }),
      });

      if (!response.ok) {
        throw new Error(`Smart create failed with status ${response.status}`);
      }

      const project = await response.json();
      cardGrid.appendChild(createProjectCard(project));
      smartNotes.value = '';
      updateProjectList();
      smartCreateStatus.textContent = 'Project created.';
    } catch (error) {
      console.error('Unable to smart-create project:', error);
      smartCreateStatus.textContent = 'Unable to create project. Please check the notes and try again.';
    }
  });
}

document.querySelectorAll('.card').forEach((card) => {
  bindCardEvents(card);
});

if (filterInput && projectCount) {
  updateProjectList();
}
