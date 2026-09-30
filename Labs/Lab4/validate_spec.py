from pathlib import Path
import re

root = Path('c:/Users/61075/Desktop/ssw-215-Hanbin/Labs/Lab4')
html = (root / 'index.html').read_text(encoding='utf-8')
css = (root / 'style.css').read_text(encoding='utf-8')

checks = {
    'css_reset': css.lstrip().startswith('*, *::before, *::after { box-sizing: border-box; }'),
    'no_inline_style': 'style=' not in html.lower(),
    'no_id_selectors': not re.search(r'#[A-Za-z0-9_-]+\s*\{', css),
    'avatar_relative': 'assets/avatar.png' in html,
    'github_target_blank': 'target="_blank"' in html and 'rel="noopener"' in html,
    'one_h1': html.count('<h1') == 1,
    'one_header': html.count('<header') == 1,
    'one_nav': html.count('<nav') == 1,
    'one_main': html.count('<main') == 1,
    'one_footer': html.count('<footer') == 1,
    'projects_anchor': 'href="#projects"' in html,
    'no_hash_links': 'href="#"' not in html,
    'project_card': 'article class="card"' in html,
    'projects_flex': '.projects-grid' in css and 'display: flex' in css and 'flex-wrap: wrap' in css and 'gap:' in css,
    'no_js': '<script' not in html.lower(),
}

for name, ok in checks.items():
    print(f'{name}: {ok}')
print('CSS prefix:', repr(css[:40]))
print('GitHub count:', html.count('https://github.com/HarveyQin'))
