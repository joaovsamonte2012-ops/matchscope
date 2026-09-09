import os
from pathlib import Path

android_dir = Path(os.environ["ANDROID_DIR"])
app_js = android_dir / "app/src/main/assets/www/app.js"

if not app_js.exists():
    raise SystemExit(f"ERRO: app.js nao encontrado: {app_js}")

js = app_js.read_text(encoding="utf-8")
marker = "__MATCHSCOPE_FLOATING_PROFILE_NAV__"

if marker in js:
    print("Menu flutuante ja aplicado.")
    raise SystemExit(0)

injection = r'''

/* __MATCHSCOPE_FLOATING_PROFILE_NAV__ */
(function () {
  if (window.__matchscopeFloatingProfileNavInstalled) return;
  window.__matchscopeFloatingProfileNavInstalled = true;

  const NAV_LABELS = ['Jogos', 'Ao vivo', 'Análises', 'Competições', 'Favoritos'];
  let menu = null;
  let profileButton = null;
  let boundProfileButton = null;

  function norm(value) {
    return (value || '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/\s+/g, ' ')
      .trim()
      .toLowerCase();
  }

  const wanted = NAV_LABELS.map(norm);

  function elementText(el) {
    return norm(el && (el.innerText || el.textContent || ''));
  }

  function navMatches(el) {
    if (!el || el === document.body || el === document.documentElement) return false;
    const text = elementText(el);
    const count = wanted.filter(label => text.includes(label)).length;
    if (count < 4) return false;

    const r = el.getBoundingClientRect();
    if (r.width < window.innerWidth * 0.65) return false;
    if (r.height < 45 || r.height > 170) return false;
    if (r.bottom < window.innerHeight * 0.72) return false;

    return true;
  }

  function findBottomNav() {
    const preferred = [
      ...document.querySelectorAll('nav, footer, [class*="bottom" i], [class*="nav" i], [role="navigation"]')
    ].filter(navMatches);

    if (preferred.length) {
      preferred.sort((a, b) => a.getBoundingClientRect().height - b.getBoundingClientRect().height);
      return preferred[0];
    }

    const fallback = [...document.querySelectorAll('div')].filter(navMatches);
    fallback.sort((a, b) => a.getBoundingClientRect().height - b.getBoundingClientRect().height);
    return fallback[0] || null;
  }

  function findTargetForLabel(label) {
    const nav = findBottomNav();
    const root = nav || document;
    const target = norm(label);
    const nodes = [...root.querySelectorAll('button, a, [role="button"], [data-tab], [data-route], div, span')];

    let best = null;
    let bestScore = -1;
    for (const node of nodes) {
      const text = elementText(node);
      if (!text) continue;
      let score = -1;
      if (text === target) score = 100;
      else if (text.includes(target) && text.length <= target.length + 12) score = 60;
      if (score < 0) continue;

      const clickable = node.closest('button, a, [role="button"], [data-tab], [data-route]') || node;
      if (clickable !== node) score += 10;
      if (score > bestScore) {
        best = clickable;
        bestScore = score;
      }
    }
    return best;
  }

  function hideBottomNav() {
    const nav = findBottomNav();
    if (!nav) return;
    nav.setAttribute('data-matchscope-hidden-bottom-nav', '1');
    nav.style.setProperty('display', 'none', 'important');
    nav.style.setProperty('visibility', 'hidden', 'important');
    nav.style.setProperty('pointer-events', 'none', 'important');

    document.documentElement.style.setProperty('--matchscope-bottom-nav-height', '0px');
    document.body.style.setProperty('padding-bottom', 'max(12px, env(safe-area-inset-bottom))', 'important');
  }

  function findProfileButton() {
    const explicit = document.querySelector(
      '[aria-label*="perfil" i], [title*="perfil" i], [aria-label*="profile" i], [title*="profile" i]'
    );
    if (explicit) return explicit.closest('button, a, [role="button"]') || explicit;

    const candidates = [...document.querySelectorAll('button, a, [role="button"]')]
      .map(el => ({ el, r: el.getBoundingClientRect() }))
      .filter(x =>
        x.r.width >= 34 && x.r.width <= 110 &&
        x.r.height >= 34 && x.r.height <= 110 &&
        x.r.top >= 20 && x.r.top <= 190 &&
        x.r.right >= window.innerWidth * 0.72
      );

    candidates.sort((a, b) => b.r.right - a.r.right || a.r.top - b.r.top);
    return candidates[0]?.el || null;
  }

  function closeMenu() {
    if (menu) menu.hidden = true;
  }

  function createMenu() {
    if (menu && document.body.contains(menu)) return menu;

    menu = document.createElement('div');
    menu.id = 'matchscope-floating-profile-menu';
    menu.hidden = true;
    menu.setAttribute('role', 'menu');
    menu.style.cssText = [
      'position:fixed',
      'top:88px',
      'right:18px',
      'width:min(270px,calc(100vw - 36px))',
      'padding:10px',
      'border-radius:20px',
      'background:rgba(9,19,36,.98)',
      'border:1px solid rgba(126,151,190,.28)',
      'box-shadow:0 18px 50px rgba(0,0,0,.42)',
      'z-index:2147483646',
      'backdrop-filter:blur(18px)',
      '-webkit-backdrop-filter:blur(18px)'
    ].join(';');

    const title = document.createElement('div');
    title.textContent = 'Navegação';
    title.style.cssText = 'padding:8px 10px 10px;color:#7ce7c4;font:700 12px/1.2 system-ui;letter-spacing:.08em;text-transform:uppercase';
    menu.appendChild(title);

    NAV_LABELS.forEach(label => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = label;
      btn.setAttribute('role', 'menuitem');
      btn.style.cssText = [
        'display:flex',
        'align-items:center',
        'width:100%',
        'min-height:48px',
        'padding:0 14px',
        'margin:2px 0',
        'border:0',
        'border-radius:14px',
        'background:transparent',
        'color:#eef3ff',
        'font:700 15px/1 system-ui',
        'text-align:left'
      ].join(';');

      btn.addEventListener('click', () => {
        const target = findTargetForLabel(label);
        closeMenu();
        if (target) {
          target.click();
          setTimeout(apply, 50);
          setTimeout(apply, 250);
        }
      });
      menu.appendChild(btn);
    });

    document.body.appendChild(menu);
    return menu;
  }

  function bindProfileButton() {
    profileButton = findProfileButton();
    if (!profileButton || profileButton === boundProfileButton) return;

    boundProfileButton = profileButton;
    profileButton.setAttribute('aria-label', 'Abrir menu de navegação');

    profileButton.addEventListener('click', function (event) {
      event.preventDefault();
      event.stopPropagation();
      if (event.stopImmediatePropagation) event.stopImmediatePropagation();
      const panel = createMenu();
      panel.hidden = !panel.hidden;
    }, true);
  }

  function apply() {
    hideBottomNav();
    createMenu();
    bindProfileButton();
  }

  document.addEventListener('click', function (event) {
    if (!menu || menu.hidden) return;
    if (menu.contains(event.target)) return;
    if (profileButton && profileButton.contains(event.target)) return;
    closeMenu();
  }, true);

  const observer = new MutationObserver(() => {
    clearTimeout(window.__matchscopeFloatingNavTimer);
    window.__matchscopeFloatingNavTimer = setTimeout(apply, 40);
  });

  function start() {
    apply();
    observer.observe(document.documentElement, { childList: true, subtree: true });
    setTimeout(apply, 300);
    setTimeout(apply, 1000);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, { once: true });
  } else {
    start();
  }
})();
'''

app_js.write_text(js + injection, encoding="utf-8")
print("Patch de menu flutuante aplicado com sucesso.")
