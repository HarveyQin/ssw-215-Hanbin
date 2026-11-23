const filterInput = document.getElementById('filter-input');
const projectCount = document.getElementById('project-count');
const addTitleInput = document.getElementById('new-title');
const addProjectBtn = document.getElementById('add-project-btn');
const smartNotes = document.getElementById('smart-notes');
const smartCreateBtn = document.getElementById('smart-create-btn');
const smartCreateStatus = document.getElementById('smart-create-status');
const githubImportForm = document.getElementById('github-import-form');
const githubImportStatus = document.getElementById('github-import-status');
const githubDraftPanel = document.getElementById('github-draft-panel');
const githubFeedback = document.getElementById('github-feedback');
const githubDraftStatus = document.getElementById('github-draft-status');
const githubSendFeedback = document.getElementById('github-send-feedback');
const githubRefineBlind = document.getElementById('github-refine-blind');
const githubApproveDraft = document.getElementById('github-approve-draft');
const cardGrid = document.querySelector('.card-grid');
let githubSessionId = null;

async function readApiResponse(response) {
  if (!response.ok) {
    let payload;
    try {
      payload = await response.json();
    } catch (error) {
      throw new Error(`Request failed with status ${response.status}`);
    }
    throw new Error(payload.error || `Request failed with status ${response.status}`);
  }

  return response.json();
}

function renderGithubDraft(draft) {
  document.getElementById('github-draft-title').textContent = draft.title;
  document.getElementById('github-draft-summary').textContent = draft.summary;
  document.getElementById('github-draft-technologies').textContent =
    Array.isArray(draft.technologies) ? draft.technologies.join(', ') : '';
  document.getElementById('github-draft-difficulty').textContent = draft.difficulty;
  githubDraftPanel.classList.remove('hidden');
}

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

  if (project.difficulty) {
    const difficulty = document.createElement('p');
    difficulty.className = 'project-difficulty';
    difficulty.textContent = `Difficulty: ${project.difficulty}`;
    card.appendChild(difficulty);
  }

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

if (
  githubImportForm &&
  githubImportStatus &&
  githubDraftPanel &&
  githubFeedback &&
  githubDraftStatus &&
  githubSendFeedback &&
  githubRefineBlind &&
  githubApproveDraft &&
  cardGrid
) {
  githubImportForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    githubImportStatus.textContent = '';
    githubDraftStatus.textContent = '';

    const owner = document.getElementById('repo-owner').value.trim();
    const repo = document.getElementById('repo-name').value.trim();

    try {
      const response = await fetch('/api/projects/git-start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ owner, repo }),
      });
      const result = await readApiResponse(response);
      githubSessionId = result.session_id;
      renderGithubDraft(result.draft);
      githubImportStatus.textContent = 'Draft fetched.';
    } catch (error) {
      githubImportStatus.textContent = error.message;
    }
  });

  githubSendFeedback.addEventListener('click', async () => {
    githubDraftStatus.textContent = '';

    try {
      const response = await fetch('/api/projects/git-refine', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: githubSessionId,
          feedback: githubFeedback.value,
        }),
      });
      const draft = await readApiResponse(response);
      renderGithubDraft(draft);
      githubFeedback.value = '';
      githubDraftStatus.textContent = 'Draft updated.';
    } catch (error) {
      githubDraftStatus.textContent = error.message;
    }
  });

  githubRefineBlind.addEventListener('click', async () => {
    githubDraftStatus.textContent = '';

    try {
      const response = await fetch('/api/projects/git-refine-blind', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: githubSessionId,
          feedback: githubFeedback.value,
        }),
      });
      const draft = await readApiResponse(response);
      renderGithubDraft(draft);
      githubDraftStatus.textContent =
        'Preview only; the saved draft session remains unchanged.';
    } catch (error) {
      githubDraftStatus.textContent = error.message;
    }
  });

  githubApproveDraft.addEventListener('click', async () => {
    githubDraftStatus.textContent = '';

    try {
      const response = await fetch('/api/projects/git-commit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session_id: githubSessionId }),
      });
      const project = await readApiResponse(response);
      cardGrid.appendChild(createProjectCard(project));
      githubSessionId = null;
      githubFeedback.value = '';
      githubDraftPanel.classList.add('hidden');
      githubImportStatus.textContent = 'Project saved.';
      updateProjectList();
    } catch (error) {
      githubDraftStatus.textContent = error.message;
    }
  });
}

document.querySelectorAll('.card').forEach((card) => {
  bindCardEvents(card);
});

if (filterInput && projectCount) {
  updateProjectList();
}
