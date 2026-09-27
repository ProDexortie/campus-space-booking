(function () {
  const API_BASE = "/api/v1";

  let currentUser = null;
  let authToken = localStorage.getItem("campus_token");

  // DOM elements
  const authNav = document.getElementById("auth-nav");
  const alertBox = document.getElementById("alert-box");
  const tabButtons = document.querySelectorAll(".tab-button");
  const tabPanels = document.querySelectorAll(".tab-panel");

  const myBookingsTabBtn = document.getElementById("my-bookings-tab-btn");
  const adminTabBtn = document.getElementById("admin-tab-btn");

  const spacesGrid = document.getElementById("spaces-grid");
  const spacesLoading = document.getElementById("spaces-loading");
  const bookingsList = document.getElementById("bookings-list");
  const bookingsLoading = document.getElementById("bookings-loading");

  // Modals
  const modalLogin = document.getElementById("modal-login");
  const modalRegister = document.getElementById("modal-register");
  const modalBooking = document.getElementById("modal-booking");

  function showAlert(message, type = "success") {
    alertBox.textContent = message;
    alertBox.className = `alert-box ${type}`;
    alertBox.style.display = "block";
    setTimeout(() => {
      alertBox.style.display = "none";
    }, 5000);
  }

  function getHeaders(includeAuth = true) {
    const headers = {
      "Content-Type": "application/json",
    };
    if (includeAuth && authToken) {
      headers["Authorization"] = `Bearer ${authToken}`;
    }
    return headers;
  }

  function openModal(modal) {
    modal.classList.add("open");
  }

  function closeModal(modal) {
    modal.classList.remove("open");
  }

  document.querySelectorAll(".modal-close, [data-close]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const modalId = btn.getAttribute("data-close");
      if (modalId) {
        closeModal(document.getElementById(modalId));
      }
    });
  });

  // Switch tabs
  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      tabButtons.forEach((b) => b.classList.remove("active"));
      tabPanels.forEach((p) => p.classList.remove("active"));

      btn.classList.add("active");
      const activePanel = document.getElementById(targetTab);
      if (activePanel) {
        activePanel.classList.add("active");
      }

      if (targetTab === "tab-my-bookings") {
        loadMyBookings();
      }
    });
  });

  // Render navigation state
  function updateAuthUI() {
    if (currentUser) {
      const isAdmin = currentUser.role === "admin";
      authNav.innerHTML = `
        <span class="user-badge">${escapeHtml(currentUser.full_name)} <span class="role-tag ${isAdmin ? "admin" : ""}">${currentUser.role}</span></span>
        <button id="logout-btn" class="btn btn-secondary btn-sm">Выйти</button>
      `;
      document.getElementById("logout-btn").addEventListener("click", logout);

      myBookingsTabBtn.style.display = "inline-block";
      if (isAdmin) {
        adminTabBtn.style.display = "inline-block";
      } else {
        adminTabBtn.style.display = "none";
      }
    } else {
      authNav.innerHTML = `
        <button id="open-login-btn" class="btn btn-secondary btn-sm">Войти</button>
        <button id="open-reg-btn" class="btn btn-primary btn-sm">Регистрация</button>
      `;
      document.getElementById("open-login-btn").addEventListener("click", () => openModal(modalLogin));
      document.getElementById("open-reg-btn").addEventListener("click", () => openModal(modalRegister));

      myBookingsTabBtn.style.display = "none";
      adminTabBtn.style.display = "none";
    }
  }

  async function checkCurrentUser() {
    if (!authToken) {
      currentUser = null;
      updateAuthUI();
      return;
    }
    try {
      const resp = await fetch(`${API_BASE}/auth/me`, {
        headers: getHeaders(true),
      });
      if (resp.ok) {
        currentUser = await resp.json();
      } else {
        authToken = null;
        localStorage.removeItem("campus_token");
        currentUser = null;
      }
    } catch {
      currentUser = null;
    }
    updateAuthUI();
  }

  function logout() {
    authToken = null;
    localStorage.removeItem("campus_token");
    currentUser = null;
    updateAuthUI();
    showAlert("Вы успешно вышли из профиля");
    // Switch to spaces tab
    document.querySelector('[data-tab="tab-spaces"]').click();
  }

  // Load and render spaces
  async function loadSpaces() {
    spacesLoading.style.display = "block";
    spacesGrid.innerHTML = "";

    const type = document.getElementById("filter-type").value;
    const minCap = document.getElementById("filter-min-capacity").value;
    const proj = document.getElementById("filter-projector").checked;
    const board = document.getElementById("filter-whiteboard").checked;

    const query = new URLSearchParams();
    if (type) query.append("space_type", type);
    if (minCap) query.append("min_capacity", minCap);
    if (proj) query.append("has_projector", "true");
    if (board) query.append("has_whiteboard", "true");

    try {
      const resp = await fetch(`${API_BASE}/spaces?${query.toString()}`);
      spacesLoading.style.display = "none";

      if (!resp.ok) {
        showAlert("Не удалось загрузить каталог мест", "error");
        return;
      }

      const spaces = await resp.json();
      if (spaces.length === 0) {
        spacesGrid.innerHTML = '<div class="empty-state">По выбранным фильтрам ничего не найдено</div>';
        return;
      }

      spaces.forEach((space) => {
        const card = document.createElement("div");
        card.className = "space-card";
        card.innerHTML = `
          <div>
            <div class="space-card-header">
              <h3 class="space-card-title">${escapeHtml(space.title)}</h3>
              <span class="space-type-badge">${formatType(space.space_type)}</span>
            </div>
            <p class="space-card-desc">${escapeHtml(space.description || "Без описания")}</p>
            <div class="space-meta">
              <span class="space-meta-item">Вместимость: ${space.capacity} чел.</span>
              ${space.has_projector ? '<span class="space-meta-item">✓ Проектор</span>' : ""}
              ${space.has_whiteboard ? '<span class="space-meta-item">✓ Маркерная доска</span>' : ""}
            </div>
          </div>
          <button class="btn btn-primary btn-sm book-space-btn" data-id="${space.id}" data-title="${escapeHtml(space.title)}">Забронировать</button>
        `;
        spacesGrid.appendChild(card);
      });

      document.querySelectorAll(".book-space-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          if (!currentUser) {
            showAlert("Для бронирования необходимо войти в аккаунт", "error");
            openModal(modalLogin);
            return;
          }
          initBookingDialog(btn.getAttribute("data-id"), btn.getAttribute("data-title"));
        });
      });
    } catch {
      spacesLoading.style.display = "none";
      showAlert("Ошибка соединения с сервером", "error");
    }
  }

  function initBookingDialog(spaceId, spaceTitle) {
    document.getElementById("booking-space-id").value = spaceId;
    document.getElementById("booking-modal-title").textContent = `Бронирование: ${spaceTitle}`;
    document.getElementById("booking-space-info").textContent = `Вы бронируете место #${spaceId}`;

    const now = new Date();
    now.setMinutes(0, 0, 0);
    now.setHours(now.getHours() + 1);

    const later = new Date(now.getTime() + 2 * 60 * 60 * 1000);

    document.getElementById("booking-start").value = toLocalISO(now);
    document.getElementById("booking-end").value = toLocalISO(later);

    openModal(modalBooking);
  }

  // Load My Bookings
  async function loadMyBookings() {
    if (!currentUser) return;
    bookingsLoading.style.display = "block";
    bookingsList.innerHTML = "";

    try {
      const resp = await fetch(`${API_BASE}/bookings/my`, {
        headers: getHeaders(true),
      });
      bookingsLoading.style.display = "none";

      if (!resp.ok) {
        showAlert("Не удалось загрузить бронирования", "error");
        return;
      }

      const bookings = await resp.json();
      if (bookings.length === 0) {
        bookingsList.innerHTML = '<div class="empty-state">У вас пока нет активных бронирований</div>';
        return;
      }

      bookings.forEach((b) => {
        const item = document.createElement("div");
        item.className = "booking-item";
        const canCancel = b.status === "confirmed";

        item.innerHTML = `
          <div>
            <div class="booking-info-title">Бронь #${b.id} (Место #${b.space_id})</div>
            <div class="booking-info-times">
              ${formatDateTime(b.start_time)} — ${formatDateTime(b.end_time)}
            </div>
          </div>
          <div style="display: flex; align-items: center; gap: 12px;">
            <span class="status-badge ${b.status}">${formatStatus(b.status)}</span>
            ${canCancel ? `<button class="btn btn-secondary btn-sm cancel-booking-btn" data-id="${b.id}">Отменить</button>` : ""}
          </div>
        `;
        bookingsList.appendChild(item);
      });

      document.querySelectorAll(".cancel-booking-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const bookingId = btn.getAttribute("data-id");
          if (confirm(`Отменить бронирование #${bookingId}?`)) {
            await cancelBooking(bookingId);
          }
        });
      });
    } catch {
      bookingsLoading.style.display = "none";
      showAlert("Ошибка при получении списка бронирований", "error");
    }
  }

  async function cancelBooking(bookingId) {
    try {
      const resp = await fetch(`${API_BASE}/bookings/${bookingId}/cancel`, {
        method: "POST",
        headers: getHeaders(true),
      });
      const data = await resp.json();
      if (resp.ok) {
        showAlert(`Бронирование #${bookingId} успешно отменено`);
        loadMyBookings();
      } else {
        showAlert(data.detail || "Не удалось отменить бронь", "error");
      }
    } catch {
      showAlert("Ошибка сети при отмене брони", "error");
    }
  }

  // Handle Login
  document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;

    try {
      const resp = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: getHeaders(false),
        body: JSON.stringify({ email, password }),
      });
      const data = await resp.json();
      if (resp.ok) {
        authToken = data.access_token;
        localStorage.setItem("campus_token", authToken);
        closeModal(modalLogin);
        document.getElementById("login-form").reset();
        await checkCurrentUser();
        showAlert("Добро пожаловать в систему!");
      } else {
        showAlert(data.detail || "Неверный логин или пароль", "error");
      }
    } catch {
      showAlert("Ошибка сервера при авторизации", "error");
    }
  });

  // Handle Register
  document.getElementById("register-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const full_name = document.getElementById("reg-fullname").value.trim();
    const email = document.getElementById("reg-email").value.trim();
    const password = document.getElementById("reg-password").value;
    const role = document.getElementById("reg-role").value;

    try {
      const resp = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: getHeaders(false),
        body: JSON.stringify({ full_name, email, password, role }),
      });
      const data = await resp.json();
      if (resp.ok) {
        closeModal(modalRegister);
        document.getElementById("register-form").reset();
        showAlert("Регистрация успешна! Теперь вы можете войти.");
        openModal(modalLogin);
      } else {
        showAlert(data.detail || "Ошибка регистрации", "error");
      }
    } catch {
      showAlert("Ошибка соединения при регистрации", "error");
    }
  });

  // Handle Booking Submit
  document.getElementById("booking-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const spaceId = parseInt(document.getElementById("booking-space-id").value, 10);
    const startVal = document.getElementById("booking-start").value;
    const endVal = document.getElementById("booking-end").value;

    const startTime = new Date(startVal).toISOString();
    const endTime = new Date(endVal).toISOString();

    try {
      const resp = await fetch(`${API_BASE}/bookings`, {
        method: "POST",
        headers: getHeaders(true),
        body: JSON.stringify({
          space_id: spaceId,
          start_time: startTime,
          end_time: endTime,
        }),
      });
      const data = await resp.json();
      if (resp.ok) {
        closeModal(modalBooking);
        showAlert(`Бронирование #${data.id} успешно оформлено!`);
        loadSpaces();
      } else {
        showAlert(data.detail || "Не удалось создать бронирование", "error");
      }
    } catch {
      showAlert("Ошибка сети при отправке брони", "error");
    }
  });

  // Handle Admin Create Space
  document.getElementById("create-space-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("space-title").value.trim();
    const space_type = document.getElementById("space-type").value;
    const capacity = parseInt(document.getElementById("space-capacity").value, 10);
    const has_projector = document.getElementById("space-projector").checked;
    const has_whiteboard = document.getElementById("space-whiteboard").checked;
    const description = document.getElementById("space-description").value.trim();

    try {
      const resp = await fetch(`${API_BASE}/spaces`, {
        method: "POST",
        headers: getHeaders(true),
        body: JSON.stringify({
          title,
          space_type,
          capacity,
          has_projector,
          has_whiteboard,
          description: description || null,
        }),
      });
      const data = await resp.json();
      if (resp.ok) {
        showAlert(`Пространство "${data.title}" создано!`);
        document.getElementById("create-space-form").reset();
        document.querySelector('[data-tab="tab-spaces"]').click();
        loadSpaces();
      } else {
        showAlert(data.detail || "Ошибка при создании пространства", "error");
      }
    } catch {
      showAlert("Ошибка соединения с сервером", "error");
    }
  });

  document.getElementById("apply-filters-btn").addEventListener("click", loadSpaces);
  document.getElementById("reset-filters-btn").addEventListener("click", () => {
    document.getElementById("filter-type").value = "";
    document.getElementById("filter-min-capacity").value = "";
    document.getElementById("filter-projector").checked = false;
    document.getElementById("filter-whiteboard").checked = false;
    loadSpaces();
  });
  document.getElementById("refresh-bookings-btn").addEventListener("click", loadMyBookings);

  // Formatting utils
  function formatType(type) {
    const map = {
      desk: "Рабочий стол",
      meeting_room: "Переговорная",
      lounge_zone: "Лаунж-зона",
    };
    return map[type] || type;
  }

  function formatStatus(status) {
    const map = {
      confirmed: "Подтверждено",
      cancelled: "Отменено",
      expired: "Истекло",
    };
    return map[status] || status;
  }

  function formatDateTime(isoString) {
    const d = new Date(isoString);
    return d.toLocaleString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function toLocalISO(date) {
    const pad = (n) => String(n).padStart(2, "0");
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
  }

  function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  // Init
  checkCurrentUser();
  loadSpaces();
})();
