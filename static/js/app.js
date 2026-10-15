// Hamburger menyu
var burger = document.getElementById('burger');
var menu = document.getElementById('menu');
if (burger && menu) {
  burger.addEventListener('click', function () {
    menu.classList.toggle('open');
  });
}

// Dark / light tema
var themeBtn = document.getElementById('theme');
if (themeBtn) {
  themeBtn.addEventListener('click', function () {
    var root = document.documentElement;
    var next = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem('kinora-theme', next); } catch (e) {}
  });
}
