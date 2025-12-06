const STORAGE_KEY = 'editable-roulette-pages';

const state = {
  pages: [],
  currentId: null,
  rotation: 0,
};

const colors = ['#5ad8ff', '#ffb86c', '#9effa0', '#c792ea', '#ff6b6b', '#59dfa3', '#ffd93d'];

const pageListEl = document.getElementById('pageList');
const addPageBtn = document.getElementById('addPageBtn');
const editorBody = document.getElementById('editorBody');
const emptyState = document.getElementById('emptyState');
const titleInput = document.getElementById('titleInput');
const subtitleInput = document.getElementById('subtitleInput');
const mediaFileInput = document.getElementById('mediaFile');
const mediaUrlInput = document.getElementById('mediaUrl');
const mediaPreview = document.getElementById('mediaPreview');
const wheelItemInput = document.getElementById('wheelItemInput');
const addItemBtn = document.getElementById('addItemBtn');
const itemList = document.getElementById('itemList');
const spinBtn = document.getElementById('spinBtn');
const spinResult = document.getElementById('spinResult');
const wheelCanvas = document.getElementById('wheelCanvas');
const randomBtn = document.getElementById('randomBtn');
const randomResult = document.getElementById('randomResult');
const minInput = document.getElementById('minInput');
const maxInput = document.getElementById('maxInput');

const ctx = wheelCanvas.getContext('2d');

function uuid() {
  return crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2);
}

function loadState() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (raw) {
    try {
      const parsed = JSON.parse(raw);
      state.pages = parsed.pages || [];
      state.currentId = parsed.currentId || (state.pages[0]?.id ?? null);
    } catch (e) {
      console.warn('无法解析本地数据，已重置。', e);
      state.pages = [];
      state.currentId = null;
    }
  } else {
    state.pages = [createDefaultPage()];
    state.currentId = state.pages[0].id;
    persist();
  }
}

function persist() {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({ pages: state.pages, currentId: state.currentId })
  );
}

function createDefaultPage() {
  return {
    id: uuid(),
    title: '示例页面',
    subtitle: '点击左侧可新增页面',
    mediaType: null,
    mediaSrc: null,
    items: ['红色', '蓝色', '绿色', '橙色'],
  };
}

function renderPageList() {
  pageListEl.innerHTML = '';
  state.pages.forEach((page) => {
    const li = document.createElement('li');
    const btn = document.createElement('button');
    btn.className = `page-btn ${page.id === state.currentId ? 'active' : ''}`;
    btn.textContent = page.title || '未命名页面';
    btn.onclick = () => selectPage(page.id);
    li.appendChild(btn);
    pageListEl.appendChild(li);
  });
}

function selectPage(id) {
  state.currentId = id;
  persist();
  refreshEditor();
}

function currentPage() {
  return state.pages.find((p) => p.id === state.currentId);
}

function refreshEditor() {
  const page = currentPage();
  if (!page) {
    editorBody.classList.add('hidden');
    emptyState.classList.remove('hidden');
    return;
  }

  editorBody.classList.remove('hidden');
  emptyState.classList.add('hidden');
  renderPageList();

  titleInput.value = page.title || '';
  subtitleInput.value = page.subtitle || '';
  wheelItemInput.value = '';
  renderMedia(page);
  renderItems(page);
  drawWheel(page.items);
  spinResult.textContent = '等待抽取...';
}

function renderMedia(page) {
  mediaPreview.innerHTML = '';
  mediaUrlInput.value = page.mediaSrc || '';

  if (!page.mediaSrc) {
    mediaPreview.textContent = '未选择媒体';
    return;
  }

  if (page.mediaType === 'video') {
    const video = document.createElement('video');
    video.src = page.mediaSrc;
    video.controls = true;
    video.loop = true;
    mediaPreview.appendChild(video);
  } else {
    const img = document.createElement('img');
    img.src = page.mediaSrc;
    mediaPreview.appendChild(img);
  }
}

function renderItems(page) {
  itemList.innerHTML = '';
  if (!page.items.length) {
    const empty = document.createElement('div');
    empty.textContent = '暂未添加内容';
    empty.className = 'result';
    itemList.appendChild(empty);
    return;
  }

  page.items.forEach((text, index) => {
    const li = document.createElement('li');
    li.className = 'item-row';
    const span = document.createElement('span');
    span.textContent = text;
    const remove = document.createElement('button');
    remove.className = 'remove-btn';
    remove.textContent = '删除';
    remove.onclick = () => {
      page.items.splice(index, 1);
      persist();
      refreshEditor();
    };

    li.appendChild(span);
    li.appendChild(remove);
    itemList.appendChild(li);
  });
}

function drawWheel(items) {
  const radius = wheelCanvas.width / 2;
  const center = radius;
  ctx.clearRect(0, 0, wheelCanvas.width, wheelCanvas.height);

  if (!items.length) {
    ctx.fillStyle = '#1f2d3b';
    ctx.beginPath();
    ctx.arc(center, center, radius - 8, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#8da5b8';
    ctx.textAlign = 'center';
    ctx.font = '16px sans-serif';
    ctx.fillText('添加条目后可抽取', center, center);
    return;
  }

  const slice = (Math.PI * 2) / items.length;
  let start = -Math.PI / 2;

  items.forEach((item, idx) => {
    const end = start + slice;
    ctx.beginPath();
    ctx.moveTo(center, center);
    ctx.arc(center, center, radius - 6, start, end);
    ctx.closePath();
    ctx.fillStyle = colors[idx % colors.length];
    ctx.fill();

    ctx.save();
    ctx.translate(center, center);
    ctx.rotate(start + slice / 2);
    ctx.textAlign = 'right';
    ctx.fillStyle = '#0b1720';
    ctx.font = 'bold 15px sans-serif';
    ctx.fillText(item, radius - 24, 6);
    ctx.restore();

    start = end;
  });
}

function addPage() {
  const newPage = createDefaultPage();
  newPage.title = `页面 ${state.pages.length + 1}`;
  state.pages.push(newPage);
  state.currentId = newPage.id;
  persist();
  refreshEditor();
}

function handleMediaFile(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    const page = currentPage();
    if (!page) return;
    page.mediaSrc = e.target?.result;
    page.mediaType = file.type.startsWith('video') ? 'video' : 'image';
    persist();
    renderMedia(page);
  };
  reader.readAsDataURL(file);
}

function handleMediaUrl() {
  const page = currentPage();
  if (!page) return;
  const value = mediaUrlInput.value.trim();
  page.mediaSrc = value || null;
  if (!value) {
    page.mediaType = null;
  } else if (value.match(/\.mp4$|\.webm$|\.mov$/i)) {
    page.mediaType = 'video';
  } else {
    page.mediaType = 'image';
  }
  persist();
  renderMedia(page);
}

function addItem() {
  const text = wheelItemInput.value.trim();
  if (!text) return;
  const page = currentPage();
  if (!page) return;
  page.items.push(text);
  wheelItemInput.value = '';
  persist();
  refreshEditor();
}

function spinWheel() {
  const page = currentPage();
  if (!page || !page.items.length) return;
  const targetIndex = Math.floor(Math.random() * page.items.length);
  const slice = 360 / page.items.length;
  const randomTurns = Math.floor(Math.random() * 3) + 4; // 4-6 turns
  const targetAngle = randomTurns * 360 + targetIndex * slice + slice / 2;
  state.rotation += targetAngle;
  wheelCanvas.style.transform = `rotate(${state.rotation}deg)`;

  spinResult.textContent = '旋转中...';
  setTimeout(() => {
    spinResult.textContent = `结果：${page.items[targetIndex]}`;
  }, 2000);
}

function randomize() {
  const min = Number(minInput.value);
  const max = Number(maxInput.value);
  if (Number.isNaN(min) || Number.isNaN(max) || min > max) {
    randomResult.textContent = '请检查最小值和最大值';
    return;
  }
  const value = Math.floor(Math.random() * (max - min + 1)) + min;
  randomResult.textContent = `随机数：${value}`;
}

function bindEvents() {
  addPageBtn.addEventListener('click', addPage);
  titleInput.addEventListener('input', () => {
    const page = currentPage();
    if (!page) return;
    page.title = titleInput.value;
    persist();
    renderPageList();
  });
  subtitleInput.addEventListener('input', () => {
    const page = currentPage();
    if (!page) return;
    page.subtitle = subtitleInput.value;
    persist();
  });

  mediaFileInput.addEventListener('change', handleMediaFile);
  mediaUrlInput.addEventListener('change', handleMediaUrl);
  addItemBtn.addEventListener('click', addItem);
  wheelItemInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addItem();
    }
  });
  spinBtn.addEventListener('click', spinWheel);
  randomBtn.addEventListener('click', randomize);
}

function init() {
  loadState();
  bindEvents();
  refreshEditor();
}

init();
