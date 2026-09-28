(function () {
  const ingRows = document.getElementById('ing-rows');
  const addIngBtn = document.getElementById('add-ing');
  const ingHidden = document.getElementById('ingredients_json');

  const stepRows = document.getElementById('step-rows');
  const addStepBtn = document.getElementById('add-step');
  const stepHidden = document.getElementById('steps_json');

  const form = document.getElementById('recipe-form');

  function createIngRow(name = '', quantity = '') {
    const row = document.createElement('div');
    row.className = 'ing-row';
    row.innerHTML = `
      <input type="text" class="ing-name" placeholder="Ingrédient" maxlength="100" autocomplete="off" required>
      <input type="text" class="ing-qty" placeholder="Quantité (optionnel)" maxlength="50">
      <button type="button" class="remove">×</button>
    `;
    const nameInput = row.querySelector('.ing-name');
    nameInput.value = name;
    row.querySelector('.ing-qty').value = quantity;
    row.querySelector('.remove').addEventListener('click', () => row.remove());
    attachSuggest(nameInput, row);
    ingRows.appendChild(row);
    nameInput.focus();
  }

  function attachSuggest(input, row) {
    let list = null;
    let timer = null;

    const close = () => { if (list) { list.remove(); list = null; } };

    input.addEventListener('input', () => {
      clearTimeout(timer);
      timer = setTimeout(async () => {
        const q = input.value.trim();
        if (q.length < 1) { close(); return; }
        const res = await fetch('/ingredients/suggest?q=' + encodeURIComponent(q));
        const html = await res.text();
        close();
        list = document.createElement('ul');
        list.className = 'suggest';
        list.innerHTML = html;
        row.appendChild(list);
        list.querySelectorAll('li').forEach(li => {
          li.addEventListener('mousedown', (e) => {
            e.preventDefault();
            input.value = li.dataset.name;
            close();
          });
        });
      }, 150);
    });
    input.addEventListener('blur', () => setTimeout(close, 200));
  }

  function createStepRow(text = '') {
    const row = document.createElement('div');
    row.className = 'step-row';
    row.innerHTML = `
      <span class="step-num"></span>
      <textarea class="step-text" rows="2" maxlength="2000" placeholder="Décris l'étape…" required></textarea>
      <button type="button" class="remove">×</button>
    `;
    row.querySelector('.step-text').value = text;
    row.querySelector('.remove').addEventListener('click', () => { row.remove(); renumberSteps(); });
    stepRows.appendChild(row);
    renumberSteps();
  }

  function renumberSteps() {
    Array.from(stepRows.querySelectorAll('.step-row')).forEach((r, i) => {
      r.querySelector('.step-num').textContent = (i + 1) + '.';
    });
  }

  addIngBtn.addEventListener('click', () => createIngRow());
  addStepBtn.addEventListener('click', () => createStepRow());

  form.addEventListener('submit', (e) => {
    const ings = Array.from(ingRows.querySelectorAll('.ing-row')).map(r => ({
      name: r.querySelector('.ing-name').value.trim(),
      quantity: r.querySelector('.ing-qty').value.trim() || null,
    })).filter(r => r.name);
    if (ings.length === 0) {
      e.preventDefault();
      alert('Ajoute au moins un ingrédient.');
      return;
    }
    const steps = Array.from(stepRows.querySelectorAll('.step-text'))
      .map(t => t.value.trim()).filter(s => s);
    if (steps.length === 0) {
      e.preventDefault();
      alert('Ajoute au moins une étape.');
      return;
    }
    ingHidden.value = JSON.stringify(ings);
    stepHidden.value = JSON.stringify(steps);
  });

  // Initial population (edit mode) or blank defaults.
  let initialIngs = [];
  let initialSteps = [];
  try { initialIngs = JSON.parse(ingRows.dataset.initial || '[]'); } catch (_) {}
  try { initialSteps = JSON.parse(stepRows.dataset.initial || '[]'); } catch (_) {}

  if (initialIngs.length) {
    initialIngs.forEach(i => createIngRow(i.name || '', i.quantity || ''));
  } else {
    createIngRow();
  }
  if (initialSteps.length) {
    initialSteps.forEach(s => createStepRow(s));
  } else {
    createStepRow();
  }
})();
