// Run with node --test test_table_sort.cjs. Exercise the real table script.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { test } = require('node:test');
const source = fs.readFileSync('web/static/lib/table/table.js', 'utf8');

function page(storage, path = '/tasks', endpoint = '/table/tasks') {
  const requests = [];
  const header = { addEventListener: (_, fn) => { header.click = fn; } };
  const select = { addEventListener: (_, fn) => { select.change = fn; } };
  const body = {
    rows: [],
    querySelector: () => null,
    querySelectorAll: () => body.rows,
    append: (row) => { body.rows = body.rows.filter((r) => r !== row).concat(row); },
  };
  const el = {
    hasAttribute: (name) => name === 'data-src',
    getAttribute: () => endpoint,
    classList: { contains: () => true },
    style: { removeProperty() {} },
    querySelector: (selector) => ({ tbody: body, '.em-tableSort select': select,
      'input.switch': { parentElement: { removeAttribute() {}, querySelector: () => ({ addEventListener() {} }) } } })[selector] || null,
    querySelectorAll: (selector) => selector.includes(' th') ? [header] : [],
  };
  vm.runInNewContext(source, {
    document: { getElementsByClassName: () => [el] },
    window: { location: { pathname: path, href: `https://hub.test${path}` }, clearTimeout() {} },
    sessionStorage: storage, URL,
    XMLHttpRequest: function () {
      this.open = (_, url) => { this.url = url; };
      this.send = () => { requests.push(this); };
    },
  });
  function load() {
    body.rows = ['2', '1'].map((value) => ({ getElementsByTagName: () => [{ textContent: value }] }));
    header.asc = undefined;
    const req = requests.at(-1);
    req.responseText = JSON.stringify([{ Name: '2' }, { Name: '1' }]);
    req.onload();
  }
  return { requests, header, select, body, load };
}

test('header sorting survives navigation, toggles, and stays scoped to each table', () => {
  const values = new Map();
  const storage = { getItem: (key) => values.get(key), setItem: (key, value) => values.set(key, value) };
  let p = page(storage);
  p.load();
  p.header.click();
  p = page(storage);
  p.load();
  assert.equal(p.body.rows[0].getElementsByTagName()[0].textContent, '1');
  p.header.click();
  p = page(storage);
  p.load();
  assert.equal(p.body.rows[0].getElementsByTagName()[0].textContent, '2');
  assert.equal(p.header.asc, false);
  const other = page(storage, '/other', '/table/other');
  other.load();
  assert.equal(other.header.asc, undefined);
});

test('dropdown sorting is restored in requests and clears header sorting', () => {
  const values = new Map();
  const storage = { getItem: (key) => values.get(key), setItem: (key, value) => values.set(key, value) };
  const p = page(storage);
  p.load();
  p.header.click();
  const option = { hasAttribute: () => true, getAttribute: () => '/table/tasks?p=2&s=Name.desc' };
  p.select.change({ target: { options: [option], selectedIndex: 0 } });
  assert.equal(new URL(p.requests.at(-1).url).searchParams.get('p'), '2');
  const restored = page(storage);
  assert.equal(new URL(restored.requests[0].url).searchParams.get('s'), 'Name.desc');
  restored.load();
  assert.equal(restored.header.asc, undefined);
});

test('unavailable or corrupt storage does not break table loading or sorting', () => {
  for (const storage of [
    { getItem() { throw Error('blocked'); }, setItem() { throw Error('blocked'); } },
    { getItem: () => '{broken', setItem() {} },
  ]) {
    const p = page(storage);
    p.load();
    p.header.click();
    assert.equal(p.body.rows[0].getElementsByTagName()[0].textContent, '1');
  }
});
