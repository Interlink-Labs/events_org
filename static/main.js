/* ============================================================
   Interlink Labs · Eventique — Frontend Application
   ============================================================ */

const defaultUsers = [
  { id: 1, fullName: 'Иван Иванов Иванович', email: 'client@example.com', password: '123456', role: 'client', createdAt: '2026-01-10' },
  { id: 2, fullName: 'Алексей Менеджеров', email: 'admin@example.com', password: '123456', role: 'admin', createdAt: '2025-05-20' },
  { id: 3, fullName: 'Arseniy (Developer)', email: 'arseniy28@gmail.com', password: '123ars', role: 'developer', createdAt: '2026-10-27' }
];

let MOCK_USERS = JSON.parse(localStorage.getItem('il_users_db'));
if (!MOCK_USERS || !Array.isArray(MOCK_USERS)) {
  MOCK_USERS = defaultUsers;
  localStorage.setItem('il_users_db', JSON.stringify(MOCK_USERS));
}

function saveUsersDB() {
  localStorage.setItem('il_users_db', JSON.stringify(MOCK_USERS));
}

const HOSTS = [
  { id: 1, name: 'Сергей Зверев', phone: '+7 (999) 111-22-33' },
  { id: 2, name: 'Анна Смирнова', phone: '+7 (999) 444-55-66' },
  { id: 3, name: 'Дмитрий Кузнецов', phone: '+7 (999) 777-88-99' },
];
const DJS = [
  { id: 1, name: 'DJ Alex', phone: '+7 (911) 222-33-44' },
  { id: 2, name: 'DJ Groove', phone: '+7 (911) 555-66-77' },
  { id: 3, name: 'DJ Night', phone: '+7 (911) 888-99-00' },
];

const MOCK_LOCATIONS = [
  { id: 1,  name: 'Зал «Гранд»', type: 'hall', capacity: 200, pricePerHour: 8000, address: 'ул. Центральная, 10', features: 'Кондиционер, сцена, звук', workHours: '10:00 - 02:00', isActive: true, hosts: HOSTS.slice(0,2), djs: DJS.slice(0,2) },
  { id: 2,  name: 'Лофт «Кирпич»', type: 'loft', capacity: 80,  pricePerHour: 5000, address: 'пр-т Индустриальный, 25', features: 'Высокие потолки, свет', workHours: '12:00 - 02:00', isActive: true, hosts: HOSTS.slice(1,3), djs: DJS.slice(0,2) },
  { id: 3,  name: 'Шатёр «Белый»', type: 'tent', capacity: 120, pricePerHour: 6000, address: 'пл. Парковая, 1', features: 'На открытом воздухе, декор', workHours: '14:00 - 02:00', isActive: true, hosts: HOSTS, djs: DJS },
  { id: 4,  name: 'Загородная площадка', type: 'open', capacity: 300, pricePerHour: 4000, address: 'шоссе Солнечное, кв. 7', features: 'Парковка, беседка, мангал', workHours: 'круглосуточно', isActive: true, hosts: HOSTS.slice(0,1), djs: DJS.slice(0,1) },
  { id: 5,  name: 'Камерный зал «Уют»', type: 'hall', capacity: 40, pricePerHour: 3000, address: 'ул. Тихая, 5', features: 'Камин, мягкая мебель', workHours: '10:00 - 02:00', isActive: true, hosts: HOSTS.slice(1,2), djs: DJS.slice(1,2) },
  { id: 6,  name: 'Ресторан «Астория»', type: 'hall', capacity: 150, pricePerHour: 9000, address: 'ул. Невский пр., 44', features: 'Авторская кухня, сцена', workHours: '12:00 - 02:00', isActive: true, hosts: HOSTS, djs: DJS },
  { id: 7,  name: 'Лофт «Фабрика»', type: 'loft', capacity: 100, pricePerHour: 5500, address: 'ул. Заводская, 12', features: 'Панорамные окна, бар', workHours: '12:00 - 02:00', isActive: true, hosts: HOSTS.slice(0,2), djs: DJS.slice(0,2) },
  { id: 8,  name: 'Терраса «Sunset»', type: 'open', capacity: 60, pricePerHour: 4500, address: 'набережная Реки, 3', features: 'Вид на воду, зонты', workHours: '15:00 - 02:00', isActive: true, hosts: HOSTS.slice(2,3), djs: DJS.slice(1,3) },
  { id: 9,  name: 'Банкетный комплекс «Лес»', type: 'hall', capacity: 250, pricePerHour: 7000, address: 'Лесной пр-д, 18', features: 'Сосновый бор, парковка', workHours: '10:00 - 02:00', isActive: true, hosts: HOSTS, djs: DJS },
  { id: 10, name: 'Шатёр «Оливковый»', type: 'tent', capacity: 90, pricePerHour: 5000, address: 'ул. Садовая, 21', features: 'Прованский стиль, свет', workHours: '14:00 - 02:00', isActive: true, hosts: HOSTS.slice(0,1), djs: DJS.slice(0,1) },
  { id: 11, name: 'Villa «Sapphire»', type: 'open', capacity: 180, pricePerHour: 12000, address: 'курорт «Ясный», сектор 2', features: 'Бассейн, VIP-зона, охрана', workHours: 'круглосуточно', isActive: true, hosts: HOSTS, djs: DJS },
  { id: 12, name: 'Арт-пространство «Лофт 8»', type: 'loft', capacity: 70, pricePerHour: 4200, address: 'ул. Пушкина, 8', features: 'Картины, инсталляции, свет', workHours: '12:00 - 02:00', isActive: true, hosts: HOSTS.slice(1,3), djs: DJS.slice(1,3) },
];

const MOCK_SERVICES = [
  { id: 1, name: 'Базовое оформление зала', category: 'base', price: 15000 },
  { id: 2, name: 'Фотозона', category: 'add', price: 8000 },
  { id: 3, name: 'Кейтеринг (фуршет)', category: 'add', price: 25000 },
  { id: 4, name: 'Оформление шарами', category: 'add', price: 5000 },
  { id: 5, name: 'Аниматоры', category: 'add', price: 6000, hasConfig: true, configType: 'animator' },
  { id: 6, name: 'Тамада', category: 'add', price: 15000, hasConfig: true, configType: 'host' },
  { id: 7, name: 'Диджей', category: 'add', price: 12000, hasConfig: true, configType: 'dj' },
];

const EVENT_TYPES = [
  { id: 'sw', label: 'Свадьба', emoji: '💍' },
  { id: 'corp', label: 'Корпоратив', emoji: '🏢' },
  { id: 'bd', label: 'День рождения', emoji: '🎂' },
  { id: 'other', label: 'Другое', emoji: '🎈' },
];

const MOCK_BOOKINGS = [
  { id: 101, clientId: 1, locationId: 1, eventType: 'sw', date: '2026-11-15', timeStart: '14:00', timeEnd: '22:00', participants: 120, status: 'approved', totalAmount: 103000, createdAt: '2026-10-01', comment: 'Белый декор' },
];

const MOCK_PAYMENTS = [
  { id: 1, bookingId: 101, amount: 31500, type: 'prepayment', date: '2026-10-05', status: 'completed' },
];

const app = {
  currentUser: null,
  selectedEventType: null,
  selectedLocationId: null,
  selectedServices: new Set(),
  serviceConfigs: {},
  filterBookingsStatus: 'all',
  currentTotalAmount: 0,

  api: {
    delay(ms = 400) { return new Promise((r) => setTimeout(r, ms)); },
    async authLogin(email, password) {
      await this.delay();
      const user = MOCK_USERS.find((u) => u.email === email && u.password === password);
      if (!user) throw new Error('Неверный e-mail или пароль');
      return { ...user };
    },
    async authRegister(fullName, email, password) {
      await this.delay();
      if (MOCK_USERS.some((u) => u.email === email)) throw new Error('Пользователь с таким e-mail уже существует');
      const newUser = { id: Date.now(), fullName, email, password, role: 'client', createdAt: new Date().toISOString().slice(0, 10) };
      MOCK_USERS.push(newUser);
      saveUsersDB(); // Сохраняем в JSON (localStorage)
      return { ...newUser };
    },
    async locationsList() { await this.delay(); return MOCK_LOCATIONS.filter((l) => l.isActive); },
    async servicesList() { await this.delay(); return [...MOCK_SERVICES]; },
    async bookingsList() { await this.delay(); return [...MOCK_BOOKINGS]; },
    async bookingsCreate(data) {
      await this.delay();
      const booking = { id: Date.now(), ...data, status: 'pending', createdAt: new Date().toISOString().slice(0, 10) };
      MOCK_BOOKINGS.push(booking);
      return { ...booking };
    },
    async accountUpdate(id, data) {
      await this.delay();
      const u = MOCK_USERS.find((x) => x.id === id);
      if (!u) throw new Error('Пользователь не найден');
      Object.assign(u, data);
      saveUsersDB(); // Сохраняем изменения
      return { ...u };
    },
    async accountDelete(id) {
      await this.delay();
      const idx = MOCK_USERS.findIndex((x) => x.id === id);
      if (idx === -1) throw new Error('Пользователь не найден');
      MOCK_USERS.splice(idx, 1);
      saveUsersDB();
      return { ok: true };
    },
  },

  init() {
    this.bindAuthForms();
    this.bindDevAuthForm();
    this.bindProfileForm();
    this.restoreSession();
    this.updateNav();
    this.showScreen('home');
  },

  restoreSession() {
    const raw = sessionStorage.getItem('il_user');
    if (raw) { try { this.currentUser = JSON.parse(raw); } catch (e) {} }
  },
  saveSession() { sessionStorage.setItem('il_user', JSON.stringify(this.currentUser)); },
  clearSession() { this.currentUser = null; sessionStorage.removeItem('il_user'); },

  showScreen(id) {
    document.querySelectorAll('.screen').forEach((el) => { el.classList.remove('active'); el.classList.add('hidden'); });
    const target = document.getElementById(`screen-${id}`);
    if (target) { target.classList.remove('hidden'); target.classList.add('active'); window.scrollTo({ top: 0, behavior: 'smooth' }); }

    if (id === 'locations') this.renderLocations();
    if (id === 'create-booking') { this.resetBookingWizard(); this.renderEventTypes(); }
    if (id === 'bookings') { this.filterBookingsStatus = 'all'; this.renderBookings(); }
    if (id === 'client-dashboard') this.renderClientDashboard();
    if (id === 'estimate') this.renderEstimate();
    if (id === 'profile') this.renderProfile();
    this.updateNav();
    
    setTimeout(() => this.initScrollAnimations(), 50);
  },

  updateNav() {
    const btnLogin = document.getElementById('btn-login');
    const btnRegister = document.getElementById('btn-register');
    const btnDev = document.getElementById('btn-dev');
    const userMenu = document.getElementById('user-menu');
    const adminLink = document.getElementById('admin-link');

    if (!this.currentUser) {
      // Если не авторизован — показываем кнопки входа и кнопку разработчика
      btnLogin.classList.remove('hidden'); 
      btnRegister.classList.remove('hidden'); 
      if (btnDev) btnDev.classList.remove('hidden');
      userMenu.classList.add('hidden');
    } else {
      // Если авторизован — скрываем кнопки входа и кнопку разработчика (он уже в системе)
      btnLogin.classList.add('hidden'); 
      btnRegister.classList.add('hidden'); 
      if (btnDev) btnDev.classList.add('hidden');
      userMenu.classList.remove('hidden');
      
      document.getElementById('user-avatar').textContent = this.currentUser.fullName.split(' ').map(s => s[0]).slice(0, 2).join('').toUpperCase();
      document.getElementById('user-name-short').textContent = this.currentUser.fullName.split(' ')[0];
      
      if (adminLink) {
        if (this.currentUser.role === 'developer' || this.currentUser.role === 'admin') {
          adminLink.classList.remove('hidden');
        } else {
          adminLink.classList.add('hidden');
        }
      }
    }
  },

  devAccess() {
    // Если пользователь уже разработчик, просто ведем в админку
    if (this.currentUser && this.currentUser.role === 'developer') {
      this.showScreen('admin');
    } else {
      // Иначе показываем форму входа разработчика
      this.showScreen('dev-login');
    }
  },

  initScrollAnimations() {
    document.querySelectorAll('.animate-on-scroll').forEach(el => el.classList.add('animate-prepare'));
    const observerOptions = { root: null, rootMargin: '0px', threshold: 0.1 };
    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          obs.unobserve(entry.target);
        }
      });
    }, observerOptions);

    document.querySelectorAll('.animate-on-scroll').forEach(el => {
      observer.observe(el);
      const rect = el.getBoundingClientRect();
      if (rect.top < window.innerHeight && rect.bottom >= 0) el.classList.add('visible');
    });
  },

  bindAuthForms() {
    document.getElementById('form-login').addEventListener('submit', (e) => { e.preventDefault(); this.login(); });
    document.getElementById('form-register').addEventListener('submit', (e) => { e.preventDefault(); this.register(); });
  },

  bindDevAuthForm() {
    const form = document.getElementById('form-dev-login');
    if (form) form.addEventListener('submit', (e) => { e.preventDefault(); this.loginDev(); });
  },

  async login() {
    const fd = new FormData(document.getElementById('form-login'));
    try {
      const user = await this.api.authLogin(fd.get('email'), fd.get('password'));
      this.currentUser = user; this.saveSession(); this.updateNav(); this.showScreen('client-dashboard');
      app.toast('Добро пожаловать, ' + user.fullName);
    } catch (e) { app.alert(e.message); }
  },

  async loginDev() {
    const fd = new FormData(document.getElementById('form-dev-login'));
    const email = fd.get('email');
    const password = fd.get('password');
    
    const user = MOCK_USERS.find(u => u.email === email && u.password === password);
    
    if (!user || user.role !== 'developer') {
      return app.alert('Доступ запрещен. Вы не являетесь разработчиком.');
    }
    
    this.currentUser = user;
    this.saveSession();
    this.updateNav();
    app.toast('Добро пожаловать в систему, ' + user.fullName);
    this.showScreen('admin');
  },

  async register() {
    const fd = new FormData(document.getElementById('form-register'));
    if (fd.get('password') !== fd.get('passwordConfirm')) return app.alert('Пароли не совпадают');
    try {
      const user = await this.api.authRegister(fd.get('fullName'), fd.get('email'), fd.get('password'));
      this.currentUser = user; this.saveSession(); this.updateNav(); this.showScreen('client-dashboard');
      app.toast('Аккаунт создан. Добро пожаловать, ' + user.fullName);
    } catch (e) { app.alert(e.message); }
  },
  logout() { this.clearSession(); this.updateNav(); this.showScreen('home'); app.toast('Вы вышли из аккаунта'); },

  togglePassword(btn) {
    const input = btn.previousElementSibling;
    if (input.type === 'password') { input.type = 'text'; btn.textContent = '🙈'; }
    else { input.type = 'password'; btn.textContent = '👁️'; }
  },

  alert(message) {
    document.getElementById('modal-title').textContent = 'Внимание';
    document.getElementById('modal-body').innerHTML = `<p style="margin:0">${message}</p>`;
    document.getElementById('modal-actions').innerHTML = `<button class="btn btn-gold" onclick="app.closeModal()">ОК</button>`;
    document.getElementById('modal-overlay').classList.remove('hidden');
  },
  toast(message) {
    let t = document.getElementById('il-toast');
    if (!t) { t = document.createElement('div'); t.id = 'il-toast'; document.body.appendChild(t); }
    t.textContent = message; t.style.opacity = 1;
    setTimeout(() => { t.style.opacity = 0; }, 2800);
  },
  closeModal() { document.getElementById('modal-overlay').classList.add('hidden'); },

  async openLocationDetail(id) {
    const loc = MOCK_LOCATIONS.find(l => l.id === id);
    if (!loc) return;
    const typeLabel = { hall: 'Банкетный зал', loft: 'Лофт', tent: 'Шатёр', open: 'Открытая площадка' }[loc.type];
    const hostsHtml = loc.hosts ? loc.hosts.map(h => `<li><span>${h.name}</span> · ${h.phone}</li>`).join('') : '<li>Нет данных</li>';
    const djsHtml = loc.djs ? loc.djs.map(d => `<li><span>${d.name}</span> · ${d.phone}</li>`).join('') : '<li>Нет данных</li>';

    document.getElementById('modal-title').textContent = loc.name;
    document.getElementById('modal-body').innerHTML = `
      <div class="location-detail-header">${typeLabel}</div>
      <div class="location-info-grid">
        <div class="location-info-item"><strong>Вместимость</strong>до ${loc.capacity} гостей</div>
        <div class="location-info-item"><strong>Цена</strong>${loc.pricePerHour.toLocaleString()} ₽ / час</div>
        <div class="location-info-item"><strong>Режим работы</strong>${loc.workHours}</div>
        <div class="location-info-item"><strong>Адрес</strong>${loc.address}</div>
      </div>
      <p style="font-size:0.9rem;margin-bottom:1.5rem"><strong>Особенности:</strong> ${loc.features}</p>
      <h4 style="margin-bottom:0.5rem;font-size:0.95rem;color:var(--navy)">Доступные тамады:</h4>
      <ul class="location-staff-list">${hostsHtml}</ul>
      <h4 style="margin-top:1rem;margin-bottom:0.5rem;font-size:0.95rem;color:var(--navy)">Доступные диджеи:</h4>
      <ul class="location-staff-list">${djsHtml}</ul>
    `;
    document.getElementById('modal-actions').innerHTML = `<button class="btn btn-gold" onclick="app.closeModal()">Закрыть</button>`;
    document.getElementById('modal-overlay').classList.remove('hidden');
  },

  async renderClientDashboard() {
    if (!this.currentUser) return this.showScreen('login');
    document.getElementById('dashboard-user-name').textContent = this.currentUser.fullName;
    const bookings = (await this.api.bookingsList()).filter((b) => b.clientId === this.currentUser.id);
    const total = bookings.length;
    const active = bookings.filter((b) => b.status === 'pending' || b.status === 'approved').length;
    const debt = bookings.reduce((acc, b) => acc + (b.status !== 'rejected' ? b.totalAmount : 0), 0);
    document.getElementById('stat-bookings-total').textContent = total;
    document.getElementById('stat-bookings-active').textContent = active;
    document.getElementById('stat-debt').textContent = debt.toLocaleString() + ' ₽';
    const recent = bookings.slice().sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)).slice(0, 4);
    document.getElementById('dashboard-bookings-list').innerHTML = this.bookingsTableHtml(recent);
  },

  async renderBookings() {
    if (!this.currentUser) return this.showScreen('login');
    const all = await this.api.bookingsList();
    let list = all.filter((b) => b.clientId === this.currentUser.id);
    if (this.filterBookingsStatus !== 'all') list = list.filter((b) => b.status === this.filterBookingsStatus);
    list.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
    document.getElementById('bookings-list').innerHTML = this.bookingsTableHtml(list);
  },

  filterBookings(status) {
    this.filterBookingsStatus = status;
    document.querySelectorAll('.status-filter .chip').forEach((c) => c.classList.toggle('active', c.dataset.filter === status));
    this.renderBookings();
  },

  bookingsTableHtml(list) {
    if (!list.length) return '<p style="padding:2rem;text-align:center;color:var(--muted)">Заявок не найдено</p>';
    const statusLabel = { pending: 'На рассмотрении', approved: 'Одобрена', rejected: 'Отклонена', completed: 'Завершена' };
    return `<table>
      <thead><tr><th>ID</th><th>Мероприятие</th><th>Дата и время</th><th>Гостей</th><th>Статус</th><th>Сумма</th></tr></thead>
      <tbody>
        ${list.map((b) => {
          const loc = MOCK_LOCATIONS.find((l) => l.id === b.locationId);
          const ev = EVENT_TYPES.find((e) => e.id === b.eventType);
          const evLabel = ev ? ev.emoji + ' ' + ev.label : (b.eventType || 'Мероприятие');
          const locLabel = loc ? '· ' + loc.name : '';
          return `<tr>
            <td>#${b.id.toString().slice(-6)}</td>
            <td>${evLabel} ${locLabel}</td>
            <td>${b.date} <br><small style="color:var(--muted)">${b.timeStart || b.time} - ${b.timeEnd || ''}</small></td>
            <td>${b.participants}</td>
            <td><span class="status-badge status-${b.status}">${statusLabel[b.status] || b.status}</span></td>
            <td>${b.totalAmount.toLocaleString()} ₽</td>
          </tr>`;
        }).join('')}
      </tbody></table>`;
  },

  async renderLocations() {
    const locations = await this.api.locationsList();
    document.getElementById('locations-list').innerHTML = locations.map((l) => {
      const typeLabel = { hall: 'Банкетный зал', loft: 'Лофт', tent: 'Шатёр', open: 'Открытая площадка' }[l.type] || l.type;
      return `
        <div class="location-card" onclick="app.openLocationDetail(${l.id})">
          <div class="card-media"><span>${typeLabel}</span></div>
          <div class="card-body">
            <h3>${l.name}</h3>
            <div class="meta">👥 До ${l.capacity} гостей</div>
            <div class="meta">📍 ${l.address}</div>
            <div class="price">от ${l.pricePerHour.toLocaleString()} ₽<small>/час</small></div>
          </div>
        </div>`;
    }).join('');
  },

  resetBookingWizard() {
    this.selectedEventType = null; this.selectedLocationId = null; this.selectedServices = new Set(); this.serviceConfigs = {}; this.currentTotalAmount = 0;
    document.getElementById('booking-date').value = '';
    document.getElementById('booking-time-start').value = '';
    document.getElementById('booking-time-end').value = '';
    document.getElementById('booking-participants').value = '';
    document.getElementById('booking-comment').value = '';
    this.setBookingStep(1);
  },

  setBookingStep(step) {
    document.querySelectorAll('#booking-stepper .step').forEach((el, i) => {
      el.classList.toggle('active', i + 1 === step);
      el.classList.toggle('done', i + 1 < step);
    });
    document.querySelectorAll('.booking-step').forEach((el, i) => el.classList.toggle('hidden', i + 1 !== step));
  },

  bookingPrev(step) { this.setBookingStep(step); },

  async bookingNext(step) {
    if (step === 1) {
      if (!this.selectedEventType) return app.alert('Выберите тип мероприятия');
      await this.renderLocationChoices();
    }
    if (step === 2) {
      if (!this.selectedLocationId) return app.alert('Выберите локацию');
    }
    if (step === 3) {
      const date = document.getElementById('booking-date').value;
      const timeStart = document.getElementById('booking-time-start').value;
      const timeEnd = document.getElementById('booking-time-end').value;
      const participants = Number(document.getElementById('booking-participants').value);
      const loc = MOCK_LOCATIONS.find((l) => l.id === this.selectedLocationId);

      if (!date || !timeStart || !timeEnd || !participants) return app.alert('Заполните все поля');
      
      const endHour = parseInt(timeEnd.split(':')[0], 10);
      if (endHour > 2 && endHour !== 0) {
        return app.alert('Локации работают до 02:00 ночи. Пожалуйста, выберите время окончания не позже 02:00.');
      }

      if (loc && participants > loc.capacity) return app.alert('Выбрана локация недостаточной вместимости');
      await this.renderBookingServices();
    }
    if (step === 4) {
      await this.renderEstimateSummary();
    }
    this.setBookingStep(step + 1);
  },

  async renderEventTypes() {
    document.getElementById('event-type-grid').innerHTML = EVENT_TYPES.map((ev) => `
      <button type="button" class="choice-btn ${this.selectedEventType === ev.id ? 'selected' : ''}" onclick="app.selectEventType('${ev.id}')">
        <span class="emoji">${ev.emoji}</span><span>${ev.label}</span>
      </button>`).join('');
  },
  selectEventType(id) { this.selectedEventType = id; this.renderEventTypes(); },

  async renderLocationChoices() {
    const wrap = document.getElementById('location-choice-list');
    const locations = await this.api.locationsList();
    const ev = EVENT_TYPES.find((e) => e.id === this.selectedEventType);
    const minCap = ev ? { sw: 60, corp: 40, bd: 20, other: 10 }[ev.id] : 10;
    const list = locations.filter((l) => l.capacity >= minCap);
    wrap.innerHTML = list.map((l) => `
      <div class="choice-btn ${this.selectedLocationId === l.id ? 'selected' : ''}" onclick="app.selectLocation(${l.id})">
        <div class="name">${l.name}</div>
        <div class="info">до ${l.capacity} чел. · ${l.address}</div>
        <div class="price-tag">${l.pricePerHour.toLocaleString()} ₽/час</div>
      </div>`).join('');
  },
  selectLocation(id) { this.selectedLocationId = id; this.renderLocationChoices(); },

  async renderBookingServices() {
    const services = await this.api.servicesList();
    const wrap = document.getElementById('booking-services-list');
    
    wrap.innerHTML = services.map((s) => {
      let configHtml = '';
      if (s.hasConfig) {
        let options = [];
        if (s.configType === 'animator') {
          options = ['Пираты', 'Клоун', 'Чебурашка и Гена', 'Фиксики', 'Смешарики'].map(o => ({val: o, label: o}));
        } else if (s.configType === 'host') {
          const loc = MOCK_LOCATIONS.find(l => l.id === this.selectedLocationId);
          const hosts = loc && loc.hosts ? loc.hosts : [];
          options = hosts.map(h => ({val: h.name, label: h.name}));
        } else if (s.configType === 'dj') {
          const loc = MOCK_LOCATIONS.find(l => l.id === this.selectedLocationId);
          const djs = loc && loc.djs ? loc.djs : [];
          options = djs.map(d => ({val: d.name, label: d.name}));
        }

        const selVal = this.serviceConfigs[s.id] || '';
        configHtml = `<div class="service-config">
          <select onchange="app.setServiceConfig(${s.id}, this.value)">
            <option value="">— Выберите опцию —</option>
            ${options.map(opt => `<option value="${opt.val}" ${selVal === opt.val ? 'selected' : ''}>${opt.label}</option>`).join('')}
          </select>
        </div>`;
      }

      return `
      <div class="service-item">
        <label>
          <input type="checkbox" value="${s.id}" onchange="app.toggleService(${s.id}, this.checked)" ${this.selectedServices.has(s.id) ? 'checked' : ''}>
          ${s.name}
        </label>
        <span class="price">${s.price.toLocaleString()} ₽</span>
        ${configHtml}
      </div>`;
    }).join('');
  },

  toggleService(id, checked) {
    if (checked) this.selectedServices.add(id); else this.selectedServices.delete(id);
  },
  
  setServiceConfig(id, val) {
    this.serviceConfigs[id] = val;
  },

  async renderEstimateSummary() {
    const services = await this.api.servicesList();
    const loc = MOCK_LOCATIONS.find((l) => l.id === this.selectedLocationId);
    const date = document.getElementById('booking-date').value;
    const start = document.getElementById('booking-time-start').value;
    const end = document.getElementById('booking-time-end').value;
    
    let locPrice = 0;
    let hours = 0;
    if (loc && start && end) {
      const startH = parseInt(start.split(':')[0], 10);
      let endH = parseInt(end.split(':')[0], 10);
      if (endH < startH) endH += 24;
      hours = endH - startH;
      locPrice = loc.pricePerHour * hours;
    }

    let servicesPrice = 0;
    let configsHtml = '';
    for (const [srvId, val] of Object.entries(this.serviceConfigs)) {
       const srv = services.find(s => s.id === Number(srvId));
       if (srv && val) configsHtml += `<div class="row"><span>${srv.name} (опция)</span><span>${val}</span></div>`;
    }

    this.selectedServices.forEach(id => {
      const s = services.find((x) => x.id === Number(id));
      if (s) servicesPrice += s.price;
    });

    const total = locPrice + servicesPrice;
    this.currentTotalAmount = total;

    let locDetails = loc ? `${loc.name} (${hours} ч.)` : '—';

    document.getElementById('estimate-summary').innerHTML = `
      <div class="row"><span>Локация</span><span>${locDetails}</span></div>
      <div class="row"><span>Аренда локации</span><span>${locPrice.toLocaleString()} ₽</span></div>
      <div class="row"><span>Тип мероприятия</span><span>${EVENT_TYPES.find((e) => e.id === this.selectedEventType)?.label || '—'}</span></div>
      <div class="row"><span>Дата и время</span><span>${date} · ${start} - ${end}</span></div>
      <div class="row"><span>Гостей</span><span>${document.getElementById('booking-participants').value}</span></div>
      ${this.selectedServices.size > 0 ? `<div class="row"><span>Доп. услуги</span><span>${servicesPrice.toLocaleString()} ₽</span></div>` : ''}
      ${configsHtml}
      <div class="row total"><span>Итоговая сумма</span><span>${total.toLocaleString()} ₽</span></div>
    `;
  },

  async submitBooking() {
    if (!this.currentUser) return this.showScreen('login');
    try {
      await this.api.bookingsCreate({
        clientId: this.currentUser.id,
        locationId: this.selectedLocationId,
        eventType: this.selectedEventType,
        date: document.getElementById('booking-date').value,
        timeStart: document.getElementById('booking-time-start').value,
        timeEnd: document.getElementById('booking-time-end').value,
        participants: Number(document.getElementById('booking-participants').value),
        totalAmount: this.currentTotalAmount || 0,
        comment: document.getElementById('booking-comment').value,
        services: Array.from(this.selectedServices),
        serviceConfigs: this.serviceConfigs
      });
      app.toast('Заявка отправлена на рассмотрение');
      this.resetBookingWizard();
      this.showScreen('bookings');
    } catch (e) { app.alert(e.message); }
  },

  async renderEstimate() {
    if (!this.currentUser) return this.showScreen('login');
    const services = await this.api.servicesList();
    
    const wrap = document.getElementById('estimate-services-list');
    wrap.innerHTML = services.map((s) => {
      let configHtml = '';
      if (s.hasConfig) {
        let options = [];
        if (s.configType === 'animator') {
          options = ['Пираты', 'Клоун', 'Чебурашка и Гена', 'Фиксики', 'Смешарики'].map(o => ({val: o, label: o}));
        } else if (s.configType === 'host') {
          const loc = MOCK_LOCATIONS.find(l => l.id === this.selectedLocationId);
          const hosts = loc && loc.hosts ? loc.hosts : [];
          options = hosts.map(h => ({val: h.name, label: h.name}));
        } else if (s.configType === 'dj') {
          const loc = MOCK_LOCATIONS.find(l => l.id === this.selectedLocationId);
          const djs = loc && loc.djs ? loc.djs : [];
          options = djs.map(d => ({val: d.name, label: d.name}));
        }

        const selVal = this.serviceConfigs[s.id] || '';
        configHtml = `<div class="service-config">
          <select onchange="app.setServiceConfig(${s.id}, this.value)">
            <option value="">— Выберите опцию —</option>
            ${options.map(opt => `<option value="${opt.val}" ${selVal === opt.val ? 'selected' : ''}>${opt.label}</option>`).join('')}
          </select>
        </div>`;
      }

      return `
      <div class="service-item">
        <label>
          <input type="checkbox" value="${s.id}" onchange="app.toggleService(${s.id}, this.checked)" ${this.selectedServices.has(s.id) ? 'checked' : ''}>
          ${s.name}
        </label>
        <span class="price">${s.price.toLocaleString()} ₽</span>
        ${configHtml}
      </div>`;
    }).join('');

    const total = Array.from(this.selectedServices).reduce((sum, id) => {
      const s = services.find((x) => x.id === Number(id));
      return sum + (s ? s.price : 0);
    }, 0);
    document.getElementById('estimate-total-value').textContent = total.toLocaleString() + ' ₽';

    const userBookings = (await this.api.bookingsList()).filter((b) => b.clientId === this.currentUser.id);
    const debt = userBookings.reduce((acc, b) => b.status !== 'rejected' ? acc + b.totalAmount : acc, 0);
    const paid = MOCK_PAYMENTS.filter(p => p.status === 'completed').reduce((acc, p) => acc + p.amount, 0);
    document.getElementById('payment-debt').textContent = debt.toLocaleString() + ' ₽';
    document.getElementById('payment-paid').textContent = paid.toLocaleString() + ' ₽';

    const histWrap = document.getElementById('payment-history');
    if (!MOCK_PAYMENTS.length) {
      histWrap.innerHTML = '<p style="padding:1.5rem;text-align:center;color:var(--muted)">Платежей нет</p>';
    } else {
      histWrap.innerHTML = `<table>
        <thead><tr><th>Дата</th><th>Тип</th><th>Сумма</th><th>Статус</th></tr></thead>
        <tbody>
          ${MOCK_PAYMENTS.map((p) => `<tr><td>${p.date}</td><td>${p.type === 'prepayment' ? 'Предоплата' : 'Финальный'}</td><td>${p.amount.toLocaleString()} ₽</td><td><span class="status-badge status-${p.status === 'completed' ? 'completed' : 'pending'}">${p.status === 'completed' ? 'Оплачено' : 'Ожидается'}</span></td></tr>`).join('')}
        </tbody></table>`;
    }
  },

  async mockPay() {
    const totalText = document.getElementById('estimate-total-value').textContent;
    if (!totalText || totalText === '0 ₽') return app.alert('Нет суммы к оплате');
    if (!confirm('Оплатить на сумму ' + totalText + '?')) return;
    await this.api.delay(800);
    app.toast('Оплата прошла успешно');
    this.renderEstimate();
  },

  async renderProfile() {
    if (!this.currentUser) return this.showScreen('login');
    const u = this.currentUser;
    document.getElementById('profile-fullName').value = u.fullName;
    document.getElementById('profile-email').value = u.email;
    document.getElementById('profile-password').value = '';
    document.getElementById('profile-role').value = u.role === 'admin' ? 'Администратор' : (u.role === 'developer' ? 'Разработчик' : 'Клиент');
  },
  bindProfileForm() {
    document.getElementById('form-profile').addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!this.currentUser) return;
      const fd = new FormData(document.getElementById('form-profile'));
      const updates = { fullName: fd.get('fullName'), email: fd.get('email') };
      if (fd.get('password')) updates.password = fd.get('password');
      try {
        const updated = await this.api.accountUpdate(this.currentUser.id, updates);
        Object.assign(this.currentUser, updated); this.saveSession(); this.updateNav();
        app.toast('Профиль обновлён');
      } catch (err) { app.alert(err.message); }
    });
  },
  async deleteAccount() {
    if (!confirm('Удалить аккаунт? Все заявки будут удалены.')) return;
    if (!this.currentUser) return;
    try {
      await this.api.accountDelete(this.currentUser.id);
      this.logout(); app.toast('Аккаунт удалён');
    } catch (err) { app.alert(err.message); }
  },
};

document.addEventListener('DOMContentLoaded', () => app.init());