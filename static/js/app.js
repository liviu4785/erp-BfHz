const API = '';
let token = localStorage.getItem('token');
let currentUser = JSON.parse(localStorage.getItem('user') || 'null');
let currentPage = 'dashboard';

async function api(method, path, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (token) opts.headers['Authorization'] = `Bearer ${token}`;
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${API}${path}`, opts);
    if (res.status === 204) return null;
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Eroare server');
    return data;
}

function toast(msg, type='success') {
    const d = document.createElement('div');
    d.className = `toast toast-${type}`;
    d.textContent = msg;
    document.body.appendChild(d);
    setTimeout(() => d.remove(), 3000);
}

// --- Auth ---
function showLogin() {
    document.getElementById('app').innerHTML = `
    <div class="login-page">
        <div class="login-card">
            <h1>ERP WLB</h1>
            <p class="subtitle">Sistem de gestiune</p>
            <div id="login-alert"></div>
            <div class="login-tabs">
                <button class="active" onclick="switchTab('login')">Autentificare</button>
                <button onclick="switchTab('register')">Inregistrare</button>
            </div>
            <form id="login-form" onsubmit="handleLogin(event)">
                <div class="form-group"><label>Email</label><input type="email" id="login-email" required placeholder="email@exemplu.ro"></div>
                <div class="form-group"><label>Parola</label><input type="password" id="login-password" required placeholder="Minim 6 caractere"></div>
                <button type="submit" class="btn btn-primary btn-full">Autentificare</button>
            </form>
            <form id="register-form" style="display:none" onsubmit="handleRegister(event)">
                <div class="form-group"><label>Nume complet</label><input type="text" id="reg-name" required placeholder="Ion Popescu"></div>
                <div class="form-group"><label>Email</label><input type="email" id="reg-email" required placeholder="email@exemplu.ro"></div>
                <div class="form-group"><label>Parola</label><input type="password" id="reg-password" required minlength="6" placeholder="Minim 6 caractere"></div>
                <button type="submit" class="btn btn-primary btn-full">Creeaza cont</button>
            </form>
        </div>
    </div>`;
}

function switchTab(tab) {
    document.querySelectorAll('.login-tabs button').forEach(b => b.classList.remove('active'));
    if (tab === 'login') {
        document.querySelector('.login-tabs button:first-child').classList.add('active');
        document.getElementById('login-form').style.display = '';
        document.getElementById('register-form').style.display = 'none';
    } else {
        document.querySelector('.login-tabs button:last-child').classList.add('active');
        document.getElementById('login-form').style.display = 'none';
        document.getElementById('register-form').style.display = '';
    }
}

async function handleLogin(e) {
    e.preventDefault();
    try {
        const data = await api('POST', '/auth/login', {
            email: document.getElementById('login-email').value,
            password: document.getElementById('login-password').value,
        });
        setAuth(data);
    } catch (err) {
        document.getElementById('login-alert').innerHTML = `<div class="alert alert-error">${err.message}</div>`;
    }
}

async function handleRegister(e) {
    e.preventDefault();
    try {
        const data = await api('POST', '/auth/register', {
            name: document.getElementById('reg-name').value,
            email: document.getElementById('reg-email').value,
            password: document.getElementById('reg-password').value,
        });
        setAuth(data);
    } catch (err) {
        document.getElementById('login-alert').innerHTML = `<div class="alert alert-error">${err.message}</div>`;
    }
}

function setAuth(data) {
    token = data.access_token;
    currentUser = data.user;
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(currentUser));
    showApp();
}

function logout() {
    token = null; currentUser = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    showLogin();
}

// --- App Layout ---
function showApp() {
    document.getElementById('app').innerHTML = `
    <div class="app-layout">
        <nav class="sidebar">
            <div class="sidebar-brand">ERP WLB <span>Sistem de gestiune v2.0</span></div>
            <div class="sidebar-nav" id="sidebar-nav">
                <a onclick="navigate('dashboard')" data-page="dashboard"><span class="nav-icon">&#9632;</span> Dashboard</a>
                <div class="sidebar-section">Gestiune</div>
                <a onclick="navigate('companies')" data-page="companies"><span class="nav-icon">&#127970;</span> Companii</a>
                <a onclick="navigate('people')" data-page="people"><span class="nav-icon">&#128101;</span> Persoane</a>
                <a onclick="navigate('products')" data-page="products"><span class="nav-icon">&#128230;</span> Produse</a>
                <a onclick="navigate('inventory')" data-page="inventory"><span class="nav-icon">&#128451;</span> Stoc</a>
                <a onclick="navigate('orders')" data-page="orders"><span class="nav-icon">&#128196;</span> Comenzi</a>
                <div class="sidebar-section">Administrare</div>
                <a onclick="navigate('admin')" data-page="admin"><span class="nav-icon">&#9881;</span> Panou Admin</a>
                <a onclick="navigate('users')" data-page="users"><span class="nav-icon">&#128100;</span> Utilizatori</a>
                <a onclick="navigate('roles')" data-page="roles"><span class="nav-icon">&#128274;</span> Roluri</a>
                <a onclick="navigate('addresses')" data-page="addresses"><span class="nav-icon">&#128205;</span> Adrese</a>
                <a onclick="navigate('documents')" data-page="documents"><span class="nav-icon">&#128195;</span> Documente</a>
                <a onclick="navigate('profile')" data-page="profile"><span class="nav-icon">&#128113;</span> Profilul meu</a>
            </div>
            <div class="sidebar-footer">
                <div class="user-info"><strong>${currentUser.name}</strong>${currentUser.email}</div>
                <button class="btn btn-secondary btn-sm btn-full" onclick="logout()">Deconectare</button>
            </div>
        </nav>
        <div class="main-content">
            <div class="topbar">
                <h2 id="page-title">Dashboard</h2>
                <div class="topbar-actions" id="topbar-actions"></div>
            </div>
            <div class="content" id="page-content"></div>
        </div>
    </div>
    <div class="modal-overlay" id="modal-overlay">
        <div class="modal">
            <div class="modal-header"><h3 id="modal-title"></h3><button class="modal-close" onclick="closeModal()">&times;</button></div>
            <div class="modal-body" id="modal-body"></div>
            <div class="modal-footer" id="modal-footer"></div>
        </div>
    </div>`;
    navigate('dashboard');
}

function navigate(page) {
    currentPage = page;
    document.querySelectorAll('.sidebar-nav a').forEach(a => a.classList.toggle('active', a.dataset.page === page));
    const titles = {
        dashboard:'Dashboard', companies:'Companii', people:'Persoane', products:'Produse',
        inventory:'Stoc', orders:'Comenzi', admin:'Panou Administrare', users:'Utilizatori',
        roles:'Roluri', addresses:'Adrese', documents:'Documente', profile:'Profilul meu',
    };
    document.getElementById('page-title').textContent = titles[page] || page;
    document.getElementById('topbar-actions').innerHTML = '';
    if (window['load_' + page]) window['load_' + page]();
}

function openModal(title, bodyHtml, footerHtml) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = bodyHtml;
    document.getElementById('modal-footer').innerHTML = footerHtml;
    document.getElementById('modal-overlay').classList.add('active');
}

function closeModal() { document.getElementById('modal-overlay').classList.remove('active'); }

// --- Dashboard ---
window.load_dashboard = async function() {
    try {
        const [companies, products, orders, people, inventory, users] = await Promise.all([
            api('GET','/companies/'), api('GET','/products/'), api('GET','/orders/'),
            api('GET','/people/'), api('GET','/inventory/'), api('GET','/users/'),
        ]);
        const sales = orders.filter(o => o.order_type === 'sale');
        const purchases = orders.filter(o => o.order_type === 'purchase');
        const totalStock = inventory.reduce((s,i) => s + i.quantity, 0);
        document.getElementById('page-content').innerHTML = `
        <div class="stats-grid">
            <div class="stat-card stat-primary"><div class="stat-label">Companii</div><div class="stat-value">${companies.length}</div></div>
            <div class="stat-card stat-primary"><div class="stat-label">Persoane</div><div class="stat-value">${people.length}</div></div>
            <div class="stat-card stat-success"><div class="stat-label">Produse</div><div class="stat-value">${products.length}</div></div>
            <div class="stat-card stat-warning"><div class="stat-label">Stoc total</div><div class="stat-value">${totalStock}</div></div>
            <div class="stat-card stat-success"><div class="stat-label">Vanzari</div><div class="stat-value">${sales.length}</div></div>
            <div class="stat-card stat-danger"><div class="stat-label">Achizitii</div><div class="stat-value">${purchases.length}</div></div>
            <div class="stat-card"><div class="stat-label">Total Comenzi</div><div class="stat-value">${orders.length}</div></div>
            <div class="stat-card"><div class="stat-label">Utilizatori</div><div class="stat-value">${users.length}</div></div>
        </div>
        <div class="table-card">
            <div class="table-header"><h3>Ultimele comenzi</h3></div>
            <table><thead><tr><th>ID</th><th>Tip</th><th>Data</th><th>Status</th><th>Linii</th></tr></thead>
            <tbody>${orders.slice(0,10).map(o => `<tr>
                <td>#${o.id}</td>
                <td><span class="badge ${o.order_type==='sale'?'badge-green':'badge-blue'}">${o.order_type==='sale'?'Vanzare':o.order_type==='purchase'?'Achizitie':o.order_type}</span></td>
                <td>${o.date}</td>
                <td><span class="badge badge-${o.status==='completed'?'green':o.status==='draft'?'gray':'yellow'}">${o.status}</span></td>
                <td>${o.items.length}</td>
            </tr>`).join('')}
            ${orders.length===0?'<tr><td colspan="5" style="text-align:center;color:var(--gray-500)">Nicio comanda</td></tr>':''}
            </tbody></table>
        </div>`;
    } catch(err) {
        document.getElementById('page-content').innerHTML = `<div class="alert alert-error">${err.message}</div>`;
    }
};

// --- Admin Panel ---
window.load_admin = async function() {
    try {
        const [users, roles, companies, products, orders] = await Promise.all([
            api('GET','/users/'), api('GET','/roles/'), api('GET','/companies/'),
            api('GET','/products/'), api('GET','/orders/'),
        ]);
        document.getElementById('page-content').innerHTML = `
        <div class="admin-grid">
            <div class="admin-card" onclick="navigate('users')">
                <h3>&#128100; Utilizatori</h3>
                <p>Gestioneaza conturile utilizatorilor, activeaza/dezactiveaza conturi, atribuie roluri</p>
                <div class="admin-count">${users.length} utilizatori</div>
            </div>
            <div class="admin-card" onclick="navigate('roles')">
                <h3>&#128274; Roluri & Permisiuni</h3>
                <p>Creeaza si gestioneaza rolurile din sistem (Admin, Operator, Vizualizator)</p>
                <div class="admin-count">${roles.length} roluri</div>
            </div>
            <div class="admin-card" onclick="navigate('companies')">
                <h3>&#127970; Companii</h3>
                <p>Gestioneaza companiile partenere, clienti si furnizori</p>
                <div class="admin-count">${companies.length} companii</div>
            </div>
            <div class="admin-card" onclick="navigate('products')">
                <h3>&#128230; Produse</h3>
                <p>Catalog de produse cu preturi, categorii, coduri si descrieri</p>
                <div class="admin-count">${products.length} produse</div>
            </div>
            <div class="admin-card" onclick="navigate('orders')">
                <h3>&#128196; Comenzi</h3>
                <p>Vanzari, achizitii si retururi - gestionare completa comenzi</p>
                <div class="admin-count">${orders.length} comenzi</div>
            </div>
            <div class="admin-card" onclick="navigate('profile')">
                <h3>&#128113; Profil & Setari</h3>
                <p>Modifica datele contului tau, schimba parola si setari personale</p>
                <div class="admin-count">&rarr;</div>
            </div>
        </div>
        <div class="settings-section">
            <h3>Informatii Sistem</h3>
            <div class="profile-info">
                <dt>Versiune</dt><dd>ERP WLB v2.0</dd>
                <dt>Baza de date</dt><dd>SQLite (portabil)</dd>
                <dt>API Docs</dt><dd><a href="/docs" target="_blank">Deschide documentatia API &rarr;</a></dd>
                <dt>Utilizator curent</dt><dd>${currentUser.name} (${currentUser.email})</dd>
                <dt>Rol</dt><dd>${currentUser.role_name || 'Fara rol atribuit'}</dd>
            </div>
        </div>`;
    } catch(err) {
        document.getElementById('page-content').innerHTML = `<div class="alert alert-error">${err.message}</div>`;
    }
};

// --- Profile ---
window.load_profile = async function() {
    try {
        const me = await api('GET', '/auth/me');
        document.getElementById('page-content').innerHTML = `
        <div class="profile-card">
            <h3>Informatii cont</h3>
            <div class="profile-info">
                <dt>Nume</dt><dd>${me.name}</dd>
                <dt>Email</dt><dd>${me.email}</dd>
                <dt>Rol</dt><dd>${me.role_name || 'Neatribuit'}</dd>
                <dt>Cont activ</dt><dd><span class="badge ${me.is_active?'badge-green':'badge-red'}">${me.is_active?'Da':'Nu'}</span></dd>
                <dt>ID utilizator</dt><dd>#${me.id}</dd>
            </div>
        </div>
        <div class="settings-section">
            <h3>Modifica datele contului</h3>
            <div class="form-grid">
                <div class="form-group"><label>Nume</label><input id="prof-name" value="${me.name}"></div>
                <div class="form-group"><label>Email</label><input id="prof-email" value="${me.email}"></div>
            </div>
            <button class="btn btn-primary" style="margin-top:12px" onclick="updateProfile()">Salveaza modificarile</button>
        </div>`;
    } catch(err) {
        document.getElementById('page-content').innerHTML = `<div class="alert alert-error">${err.message}</div>`;
    }
};

window.updateProfile = async function() {
    try {
        await api('PUT', `/users/${currentUser.id}`, {
            name: document.getElementById('prof-name').value,
            email: document.getElementById('prof-email').value,
        });
        const me = await api('GET', '/auth/me');
        currentUser = me;
        localStorage.setItem('user', JSON.stringify(me));
        toast('Profil actualizat cu succes!');
        navigate('profile');
    } catch(err) { toast(err.message, 'error'); }
};

// --- Generic CRUD ---
function crudPage(config) {
    return async function() {
        document.getElementById('topbar-actions').innerHTML =
            `<input class="search-input" placeholder="Cauta..." oninput="window._crud_search(this.value)">
             <button class="btn btn-primary btn-sm" onclick="window._crud_add()">+ Adauga</button>`;
        try {
            const items = await api('GET', config.endpoint);
            window._crud_items = items;
            window._crud_config = config;
            renderCrudTable(items);
        } catch(err) {
            document.getElementById('page-content').innerHTML = `<div class="alert alert-error">${err.message}</div>`;
        }
    };
}

function renderCrudTable(items) {
    const c = window._crud_config;
    if (!items.length) {
        document.getElementById('page-content').innerHTML = `<div class="empty-state"><div class="icon">&#128196;</div><p>Nu exista inregistrari</p><button class="btn btn-primary" onclick="window._crud_add()">+ Adauga</button></div>`;
        return;
    }
    document.getElementById('page-content').innerHTML = `<div class="table-card"><table>
        <thead><tr>${c.columns.map(col => `<th>${col.label}</th>`).join('')}<th>Actiuni</th></tr></thead>
        <tbody>${items.map(item => `<tr>
            ${c.columns.map(col => `<td>${col.render ? col.render(item) : (item[col.key] ?? '-')}</td>`).join('')}
            <td class="actions-cell">
                <button class="btn btn-sm btn-secondary" onclick='window._crud_edit(${JSON.stringify(item).replace(/'/g,"&#39;")})'>Editeaza</button>
                <button class="btn btn-sm btn-danger" onclick="window._crud_delete(${item.id})">Sterge</button>
            </td></tr>`).join('')}
        </tbody></table></div>`;
}

window._crud_search = function(q) {
    const filtered = window._crud_items.filter(item =>
        window._crud_config.searchFields.some(f => (item[f]||'').toString().toLowerCase().includes(q.toLowerCase()))
    );
    renderCrudTable(filtered);
};

window._crud_add = function() {
    openModal(`Adauga ${window._crud_config.singular}`, window._crud_config.formHtml({}),
        `<button class="btn btn-secondary" onclick="closeModal()">Anuleaza</button>
         <button class="btn btn-primary" onclick="window._crud_save()">Salveaza</button>`);
};

window._crud_edit = function(item) {
    openModal(`Editeaza ${window._crud_config.singular}`, window._crud_config.formHtml(item),
        `<button class="btn btn-secondary" onclick="closeModal()">Anuleaza</button>
         <button class="btn btn-primary" onclick="window._crud_save(${item.id})">Salveaza</button>`);
};

window._crud_save = async function(id) {
    try {
        const body = window._crud_config.getFormData();
        if (id) await api('PUT', `${window._crud_config.endpoint}${id}`, body);
        else await api('POST', window._crud_config.endpoint, body);
        closeModal();
        toast(id ? 'Actualizat cu succes!' : 'Adaugat cu succes!');
        navigate(currentPage);
    } catch(err) { toast(err.message, 'error'); }
};

window._crud_delete = async function(id) {
    if (!confirm('Esti sigur ca vrei sa stergi?')) return;
    try {
        await api('DELETE', `${window._crud_config.endpoint}${id}`);
        toast('Sters cu succes!');
        navigate(currentPage);
    } catch(err) { toast(err.message, 'error'); }
};

// --- Companies ---
window.load_companies = crudPage({
    endpoint: '/companies/', singular: 'companie',
    searchFields: ['name','fiscal_code','email'],
    columns: [
        {key:'id',label:'ID'}, {key:'name',label:'Nume'}, {key:'fiscal_code',label:'CUI'},
        {key:'phone',label:'Telefon'}, {key:'email',label:'Email'},
        {key:'status',label:'Status',render:i=>`<span class="badge badge-${i.status==='active'?'green':'gray'}">${i.status||'active'}</span>`},
    ],
    formHtml: i => `<div class="form-grid">
        <div class="form-group"><label>Nume *</label><input id="f-name" value="${i.name||''}"></div>
        <div class="form-group"><label>CUI</label><input id="f-fiscal_code" value="${i.fiscal_code||''}"></div>
        <div class="form-group"><label>Nr. Reg. Com.</label><input id="f-reg" value="${i.trade_registry_number||''}"></div>
        <div class="form-group"><label>Email</label><input id="f-email" value="${i.email||''}"></div>
        <div class="form-group"><label>Telefon</label><input id="f-phone" value="${i.phone||''}"></div>
        <div class="form-group"><label>Status</label><select id="f-status"><option value="active" ${i.status==='active'?'selected':''}>Activ</option><option value="inactive" ${i.status==='inactive'?'selected':''}>Inactiv</option></select></div>
    </div>`,
    getFormData: () => ({
        name:document.getElementById('f-name').value, fiscal_code:document.getElementById('f-fiscal_code').value||null,
        trade_registry_number:document.getElementById('f-reg').value||null, email:document.getElementById('f-email').value||null,
        phone:document.getElementById('f-phone').value||null, status:document.getElementById('f-status').value,
    }),
});

// --- People ---
window.load_people = crudPage({
    endpoint: '/people/', singular: 'persoana',
    searchFields: ['first_name','last_name','email'],
    columns: [
        {key:'id',label:'ID'}, {key:'first_name',label:'Prenume'}, {key:'last_name',label:'Nume'},
        {key:'email',label:'Email'}, {key:'phone',label:'Telefon'},
    ],
    formHtml: i => `<div class="form-grid">
        <div class="form-group"><label>Prenume *</label><input id="f-first_name" value="${i.first_name||''}"></div>
        <div class="form-group"><label>Nume *</label><input id="f-last_name" value="${i.last_name||''}"></div>
        <div class="form-group"><label>Email</label><input id="f-email" value="${i.email||''}"></div>
        <div class="form-group"><label>Telefon</label><input id="f-phone" value="${i.phone||''}"></div>
        <div class="form-group"><label>Data nasterii</label><input type="date" id="f-dob" value="${i.date_of_birth||''}"></div>
        <div class="form-group"><label>CNP</label><input id="f-cnp" value="${i.unique_identifier||''}"></div>
        <div class="form-group full"><label>Note</label><textarea id="f-notes" rows="2">${i.notes||''}</textarea></div>
    </div>`,
    getFormData: () => ({
        first_name:document.getElementById('f-first_name').value, last_name:document.getElementById('f-last_name').value,
        email:document.getElementById('f-email').value||null, phone:document.getElementById('f-phone').value||null,
        date_of_birth:document.getElementById('f-dob').value||null, unique_identifier:document.getElementById('f-cnp').value||null,
        notes:document.getElementById('f-notes').value||null,
    }),
});

// --- Products ---
window.load_products = crudPage({
    endpoint: '/products/', singular: 'produs',
    searchFields: ['name','code','category'],
    columns: [
        {key:'id',label:'ID'}, {key:'code',label:'Cod'}, {key:'name',label:'Nume'},
        {key:'category',label:'Categorie'},
        {key:'list_price',label:'Pret',render:i=>i.list_price!=null?`${Number(i.list_price).toFixed(2)} RON`:'-'},
        {key:'status',label:'Status',render:i=>`<span class="badge badge-${i.status==='active'?'green':'gray'}">${i.status||'active'}</span>`},
    ],
    formHtml: i => `<div class="form-grid">
        <div class="form-group full"><label>Nume *</label><input id="f-name" value="${i.name||''}"></div>
        <div class="form-group"><label>Cod</label><input id="f-code" value="${i.code||''}"></div>
        <div class="form-group"><label>Producator</label><input id="f-producer" value="${i.producer||''}"></div>
        <div class="form-group"><label>Categorie</label><input id="f-category" value="${i.category||''}"></div>
        <div class="form-group"><label>UM</label><input id="f-unit" value="${i.unit_of_measure||'buc'}"></div>
        <div class="form-group"><label>Pret lista</label><input type="number" step="0.01" id="f-price" value="${i.list_price||0}"></div>
        <div class="form-group"><label>TVA %</label><input type="number" id="f-vat" value="${i.vat_percent||19}"></div>
        <div class="form-group"><label>Status</label><select id="f-status"><option value="active" ${i.status==='active'?'selected':''}>Activ</option><option value="inactive" ${i.status==='inactive'?'selected':''}>Inactiv</option></select></div>
        <div class="form-group full"><label>Descriere</label><textarea id="f-desc" rows="2">${i.description||''}</textarea></div>
    </div>`,
    getFormData: () => ({
        name:document.getElementById('f-name').value, code:document.getElementById('f-code').value||null,
        producer:document.getElementById('f-producer').value||null, category:document.getElementById('f-category').value||null,
        unit_of_measure:document.getElementById('f-unit').value||'buc',
        list_price:parseFloat(document.getElementById('f-price').value)||0,
        vat_percent:parseFloat(document.getElementById('f-vat').value)||19,
        status:document.getElementById('f-status').value, description:document.getElementById('f-desc').value||null,
    }),
});

// --- Inventory ---
window.load_inventory = crudPage({
    endpoint: '/inventory/', singular: 'stoc',
    searchFields: ['product_name'],
    columns: [
        {key:'id',label:'ID'}, {key:'product_name',label:'Produs'}, {key:'quantity',label:'Cantitate'},
        {key:'reserved',label:'Rezervat'}, {key:'available',label:'Disponibil',render:i=>i.quantity-i.reserved},
    ],
    formHtml: i => `<div class="form-grid">
        <div class="form-group"><label>ID Produs *</label><input type="number" id="f-product_id" value="${i.product_id||''}"></div>
        <div class="form-group"><label>Cantitate *</label><input type="number" id="f-quantity" value="${i.quantity||0}"></div>
        <div class="form-group"><label>Rezervat</label><input type="number" id="f-reserved" value="${i.reserved||0}"></div>
    </div>`,
    getFormData: () => ({
        product_id:parseInt(document.getElementById('f-product_id').value),
        quantity:parseInt(document.getElementById('f-quantity').value)||0,
        reserved:parseInt(document.getElementById('f-reserved').value)||0,
    }),
});

// --- Orders ---
window.load_orders = async function() {
    document.getElementById('topbar-actions').innerHTML =
        `<button class="btn btn-primary btn-sm" onclick="window._order_add()">+ Comanda noua</button>`;
    try {
        const orders = await api('GET', '/orders/');
        if (!orders.length) {
            document.getElementById('page-content').innerHTML = `<div class="empty-state"><div class="icon">&#128230;</div><p>Nicio comanda</p><button class="btn btn-primary" onclick="window._order_add()">+ Prima comanda</button></div>`;
            return;
        }
        document.getElementById('page-content').innerHTML = `<div class="table-card"><table>
            <thead><tr><th>ID</th><th>Tip</th><th>Partener</th><th>Data</th><th>Status</th><th>Linii</th><th>Actiuni</th></tr></thead>
            <tbody>${orders.map(o => `<tr>
                <td>#${o.id}</td>
                <td><span class="badge ${o.order_type==='sale'?'badge-green':'badge-blue'}">${o.order_type==='sale'?'Vanzare':o.order_type==='purchase'?'Achizitie':o.order_type}</span></td>
                <td>${o.partner_type} #${o.partner_id}</td>
                <td>${o.date}</td>
                <td><span class="badge badge-${o.status==='completed'?'green':o.status==='draft'?'gray':o.status==='cancelled'?'red':'yellow'}">${o.status}</span></td>
                <td>${o.items.length}</td>
                <td class="actions-cell">
                    <button class="btn btn-sm btn-secondary" onclick="window._order_edit(${o.id})">Editeaza</button>
                    <button class="btn btn-sm btn-danger" onclick="window._order_delete(${o.id})">Sterge</button>
                </td></tr>`).join('')}
            </tbody></table></div>`;
    } catch(err) { document.getElementById('page-content').innerHTML = `<div class="alert alert-error">${err.message}</div>`; }
};

window._order_add = function() {
    openModal('Comanda noua', `
        <div class="form-grid">
            <div class="form-group"><label>Tip *</label><select id="f-order_type">
                <option value="sale">Vanzare</option><option value="purchase">Achizitie</option>
                <option value="return_sale">Retur vanzare</option><option value="return_purchase">Retur achizitie</option></select></div>
            <div class="form-group"><label>Tip partener</label><select id="f-partner_type">
                <option value="company">Companie</option><option value="person">Persoana</option></select></div>
            <div class="form-group"><label>ID Partener *</label><input type="number" id="f-partner_id"></div>
            <div class="form-group"><label>Data *</label><input type="date" id="f-date" value="${new Date().toISOString().split('T')[0]}"></div>
            <div class="form-group"><label>Status</label><select id="f-status">
                <option value="draft">Draft</option><option value="confirmed">Confirmat</option><option value="completed">Finalizat</option></select></div>
            <div class="form-group"><label>Note</label><input id="f-notes"></div>
        </div>
        <h4 style="margin:16px 0 8px">Linii comanda</h4>
        <div id="order-lines"></div>
        <button class="btn btn-sm btn-secondary" style="margin-top:8px" onclick="window._order_add_line()">+ Adauga linie</button>
    `, `<button class="btn btn-secondary" onclick="closeModal()">Anuleaza</button>
        <button class="btn btn-primary" onclick="window._order_save()">Salveaza</button>`);
    window._orderLineCount = 0;
    window._order_add_line();
};

window._order_add_line = function() {
    const idx = window._orderLineCount++;
    const div = document.createElement('div');
    div.className = 'form-grid'; div.style.marginBottom = '8px';
    div.innerHTML = `
        <div class="form-group"><label>Produs ID</label><input type="number" id="ol-product-${idx}"></div>
        <div class="form-group"><label>Cantitate</label><input type="number" id="ol-qty-${idx}" value="1"></div>
        <div class="form-group"><label>Pret unitar</label><input type="number" step="0.01" id="ol-price-${idx}" value="0"></div>
        <div class="form-group"><label>TVA %</label><input type="number" id="ol-vat-${idx}" value="19"></div>`;
    document.getElementById('order-lines').appendChild(div);
};

window._order_save = async function(id) {
    const items = [];
    for (let i = 0; i < window._orderLineCount; i++) {
        const pid = document.getElementById(`ol-product-${i}`);
        if (!pid || !pid.value) continue;
        items.push({ product_id:parseInt(pid.value), quantity:parseInt(document.getElementById(`ol-qty-${i}`).value)||1,
            unit_price:parseFloat(document.getElementById(`ol-price-${i}`).value)||0,
            vat_percent:parseFloat(document.getElementById(`ol-vat-${i}`).value)||19, discount_percent:0 });
    }
    const body = { order_type:document.getElementById('f-order_type').value, partner_id:parseInt(document.getElementById('f-partner_id').value),
        partner_type:document.getElementById('f-partner_type').value, date:document.getElementById('f-date').value,
        status:document.getElementById('f-status').value, notes:document.getElementById('f-notes').value||null, items };
    try {
        if (id) await api('PUT', `/orders/${id}`, body); else await api('POST', '/orders/', body);
        closeModal(); toast(id?'Comanda actualizata!':'Comanda creata!'); navigate('orders');
    } catch(err) { toast(err.message, 'error'); }
};

window._order_edit = async function(id) {
    const o = await api('GET', `/orders/${id}`);
    openModal('Editeaza comanda', `
        <div class="form-grid">
            <div class="form-group"><label>Tip</label><select id="f-order_type">
                ${['sale','purchase','return_sale','return_purchase'].map(t=>`<option value="${t}" ${o.order_type===t?'selected':''}>${t}</option>`).join('')}</select></div>
            <div class="form-group"><label>Tip partener</label><select id="f-partner_type">
                <option value="company" ${o.partner_type==='company'?'selected':''}>Companie</option>
                <option value="person" ${o.partner_type==='person'?'selected':''}>Persoana</option></select></div>
            <div class="form-group"><label>ID Partener</label><input type="number" id="f-partner_id" value="${o.partner_id}"></div>
            <div class="form-group"><label>Data</label><input type="date" id="f-date" value="${o.date}"></div>
            <div class="form-group"><label>Status</label><select id="f-status">
                ${['draft','confirmed','completed','cancelled'].map(s=>`<option value="${s}" ${o.status===s?'selected':''}>${s}</option>`).join('')}</select></div>
            <div class="form-group"><label>Note</label><input id="f-notes" value="${o.notes||''}"></div>
        </div>
        <h4 style="margin:16px 0 8px">Linii comanda</h4>
        <div id="order-lines"></div>
        <button class="btn btn-sm btn-secondary" style="margin-top:8px" onclick="window._order_add_line()">+ Adauga linie</button>
    `, `<button class="btn btn-secondary" onclick="closeModal()">Anuleaza</button>
        <button class="btn btn-primary" onclick="window._order_save(${o.id})">Salveaza</button>`);
    window._orderLineCount = 0;
    o.items.forEach(line => {
        const idx = window._orderLineCount++;
        const div = document.createElement('div');
        div.className = 'form-grid'; div.style.marginBottom = '8px';
        div.innerHTML = `
            <div class="form-group"><label>Produs ID</label><input type="number" id="ol-product-${idx}" value="${line.product_id}"></div>
            <div class="form-group"><label>Cantitate</label><input type="number" id="ol-qty-${idx}" value="${line.quantity}"></div>
            <div class="form-group"><label>Pret unitar</label><input type="number" step="0.01" id="ol-price-${idx}" value="${line.unit_price}"></div>
            <div class="form-group"><label>TVA %</label><input type="number" id="ol-vat-${idx}" value="${line.vat_percent}"></div>`;
        document.getElementById('order-lines').appendChild(div);
    });
};

window._order_delete = async function(id) {
    if (!confirm('Stergi comanda?')) return;
    try { await api('DELETE', `/orders/${id}`); toast('Comanda stearsa!'); navigate('orders'); }
    catch(err) { toast(err.message, 'error'); }
};

// --- Users (Admin) ---
window.load_users = crudPage({
    endpoint: '/users/', singular: 'utilizator',
    searchFields: ['name','email'],
    columns: [
        {key:'id',label:'ID'}, {key:'name',label:'Nume'}, {key:'email',label:'Email'},
        {key:'role_name',label:'Rol',render:i=>`<span class="badge badge-purple">${i.role_name||'Neatribuit'}</span>`},
        {key:'is_active',label:'Activ',render:i=>`<span class="badge ${i.is_active?'badge-green':'badge-red'}">${i.is_active?'Da':'Nu'}</span>`},
    ],
    formHtml: i => `<div class="form-grid">
        <div class="form-group"><label>Nume</label><input id="f-name" value="${i.name||''}"></div>
        <div class="form-group"><label>Email</label><input id="f-email" value="${i.email||''}"></div>
        <div class="form-group"><label>Rol ID</label><input type="number" id="f-role_id" value="${i.role_id||''}"></div>
        <div class="form-group"><label>Activ</label><select id="f-is_active"><option value="true" ${i.is_active!==false?'selected':''}>Da</option><option value="false" ${i.is_active===false?'selected':''}>Nu</option></select></div>
    </div>`,
    getFormData: () => ({
        name:document.getElementById('f-name').value, email:document.getElementById('f-email').value,
        role_id:parseInt(document.getElementById('f-role_id').value)||null,
        is_active:document.getElementById('f-is_active').value==='true',
    }),
});

// --- Roles ---
window.load_roles = crudPage({
    endpoint: '/roles/', singular: 'rol',
    searchFields: ['name'],
    columns: [{key:'id',label:'ID'}, {key:'name',label:'Nume'}, {key:'description',label:'Descriere'}],
    formHtml: i => `<div class="form-grid">
        <div class="form-group"><label>Nume *</label><input id="f-name" value="${i.name||''}"></div>
        <div class="form-group full"><label>Descriere</label><textarea id="f-description" rows="2">${i.description||''}</textarea></div>
    </div>`,
    getFormData: () => ({ name:document.getElementById('f-name').value, description:document.getElementById('f-description').value||null }),
});

// --- Addresses ---
window.load_addresses = crudPage({
    endpoint: '/addresses/', singular: 'adresa',
    searchFields: ['city','county','street'],
    columns: [{key:'id',label:'ID'},{key:'city',label:'Oras'},{key:'county',label:'Judet'},{key:'street',label:'Strada'},{key:'country',label:'Tara'}],
    formHtml: i => `<div class="form-grid">
        <div class="form-group"><label>Tara</label><input id="f-country" value="${i.country||'Romania'}"></div>
        <div class="form-group"><label>Judet</label><input id="f-county" value="${i.county||''}"></div>
        <div class="form-group"><label>Oras</label><input id="f-city" value="${i.city||''}"></div>
        <div class="form-group"><label>Cod postal</label><input id="f-postal" value="${i.postal_code||''}"></div>
        <div class="form-group full"><label>Strada</label><input id="f-street" value="${i.street||''}"></div>
        <div class="form-group full"><label>Info suplimentare</label><input id="f-additional" value="${i.additional_info||''}"></div>
    </div>`,
    getFormData: () => ({
        country:document.getElementById('f-country').value, county:document.getElementById('f-county').value||null,
        city:document.getElementById('f-city').value||null, postal_code:document.getElementById('f-postal').value||null,
        street:document.getElementById('f-street').value||null, additional_info:document.getElementById('f-additional').value||null,
    }),
});

// --- Documents ---
window.load_documents = crudPage({
    endpoint: '/documents/', singular: 'document',
    searchFields: ['name','type'],
    columns: [
        {key:'id',label:'ID'}, {key:'name',label:'Nume'},
        {key:'type',label:'Tip',render:i=>`<span class="badge badge-blue">${i.type}</span>`},
        {key:'record_type',label:'Entitate'}, {key:'record_id',label:'ID Entitate'},
    ],
    formHtml: i => `<div class="form-grid">
        <div class="form-group"><label>Nume *</label><input id="f-name" value="${i.name||''}"></div>
        <div class="form-group"><label>Tip *</label><input id="f-type" value="${i.type||''}" placeholder="invoice, contract, AWB..."></div>
        <div class="form-group full"><label>URL</label><input id="f-url" value="${i.url||''}"></div>
        <div class="form-group"><label>Tip entitate *</label><input id="f-record_type" value="${i.record_type||''}" placeholder="company, order..."></div>
        <div class="form-group"><label>ID Entitate *</label><input type="number" id="f-record_id" value="${i.record_id||''}"></div>
    </div>`,
    getFormData: () => ({
        name:document.getElementById('f-name').value, type:document.getElementById('f-type').value,
        url:document.getElementById('f-url').value||null, record_type:document.getElementById('f-record_type').value,
        record_id:parseInt(document.getElementById('f-record_id').value),
    }),
});

// --- Init ---
if (token && currentUser) showApp(); else showLogin();
