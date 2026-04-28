// ── LOADING OVERLAY ──────────────────────────────
function showLoading(msg) {
  var ol = document.getElementById('loadingOverlay');
  if (!ol) return;
  var t = ol.querySelector('.loading-text');
  if (t && msg) t.textContent = msg;
  ol.classList.add('active');
}
function hideLoading() {
  var ol = document.getElementById('loadingOverlay');
  if (ol) ol.classList.remove('active');
}

// ── FLASH AUTO DISMISS ───────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  var flashes = document.querySelectorAll('.flash');
  flashes.forEach(function (f) {
    setTimeout(function () {
      f.style.opacity = '0';
      f.style.transform = 'translateY(-10px)';
      setTimeout(function () { f.remove(); }, 400);
    }, 4000);
  });
  var closes = document.querySelectorAll('.flash-close');
  closes.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var f = btn.closest('.flash');
      if (f) { f.style.opacity = '0'; setTimeout(function () { f.remove(); }, 300); }
    });
  });
});

// ── NAVBAR SCROLL ────────────────────────────────
(function () {
  var navbar = document.querySelector('.navbar');
  if (!navbar) return;
  window.addEventListener('scroll', function () {
    if (window.scrollY > 50) { navbar.classList.add('scrolled'); }
    else { navbar.classList.remove('scrolled'); }
  });
})();

// ── MOBILE NAV TOGGLE ────────────────────────────
function toggleMobileNav() {
  var links = document.querySelector('.nav-links');
  var toggle = document.querySelector('.nav-toggle');
  if (!links) return;
  links.classList.toggle('open');
  if (toggle) toggle.textContent = links.classList.contains('open') ? '✕' : '☰';
}

// ── SMOOTH SCROLL FOR ANCHOR LINKS ──────────────
document.addEventListener('DOMContentLoaded', function () {
  var anchors = document.querySelectorAll('a[href^="#"]');
  anchors.forEach(function (a) {
    a.addEventListener('click', function (e) {
      var href = a.getAttribute('href');
      if (href === '#') return;
      var target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        var links = document.querySelector('.nav-links');
        if (links) links.classList.remove('open');
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
});

// ── CONTACT FORM ─────────────────────────────────
function handleContactForm(e) {
  e.preventDefault();
  var form = e.target;
  var name = form.querySelector('[name="name"]');
  var email = form.querySelector('[name="email"]');
  var msg = form.querySelector('[name="message"]');
  var err = [];
  if (!name || !name.value.trim()) err.push('Name is required.');
  if (!email || !/^[^@]+@[^@]+\.[^@]+$/.test(email.value.trim())) err.push('Valid email is required.');
  if (!msg || msg.value.trim().length < 10) err.push('Message must be at least 10 characters.');
  var errDiv = form.querySelector('.contact-error');
  var successDiv = form.querySelector('.contact-success');
  if (err.length) {
    if (errDiv) { errDiv.textContent = err.join(' '); errDiv.style.display = 'block'; }
    if (successDiv) successDiv.style.display = 'none';
    return;
  }
  if (errDiv) errDiv.style.display = 'none';
  if (successDiv) successDiv.style.display = 'none';
  var btn = form.querySelector('button[type="submit"]');
  if (btn) { btn.disabled = true; btn.textContent = 'Sending…'; }

  var endpoint = form.getAttribute('action') || '/contact';
  fetch(endpoint, {
    method: 'POST',
    body: new FormData(form)
  })
    .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
    .then(function (res) {
      if (btn) { btn.disabled = false; btn.textContent = 'Send Message'; }
      if (!res.ok || !res.data.success) {
        if (errDiv) {
          errDiv.textContent = (res.data && res.data.message) || 'Could not submit the form.';
          errDiv.style.display = 'block';
        }
        return;
      }
      form.reset();
      if (successDiv) {
        successDiv.textContent = res.data.message || "Message sent! We'll be in touch soon.";
        successDiv.style.display = 'block';
      }
      setTimeout(function () { if (successDiv) successDiv.style.display = 'none'; }, 5000);
    })
    .catch(function () {
      if (btn) { btn.disabled = false; btn.textContent = 'Send Message'; }
      if (errDiv) {
        errDiv.textContent = 'Network error. Please try again.';
        errDiv.style.display = 'block';
      }
    });
}

// ── REGISTER PASSWORD VALIDATION ─────────────────
document.addEventListener('DOMContentLoaded', function () {
  var regForm = document.getElementById('registerForm');
  if (!regForm) return;
  regForm.addEventListener('submit', function (e) {
    var pw = regForm.querySelector('[name="password"]');
    var pw2 = regForm.querySelector('[name="confirm_password"]');
    if (!pw || !pw2) return;
    if (pw.value.length < 6) {
      e.preventDefault();
      showFieldError(pw, 'Password must be at least 6 characters.');
      return;
    }
    if (pw.value !== pw2.value) {
      e.preventDefault();
      showFieldError(pw2, 'Passwords do not match.');
      return;
    }
  });
});

function showFieldError(field, msg) {
  var existing = field.parentNode.querySelector('.field-error');
  if (existing) existing.remove();
  var span = document.createElement('span');
  span.className = 'field-error';
  span.style.cssText = 'color:#e74c3c;font-size:0.8rem;display:block;margin-top:4px;';
  span.textContent = msg;
  field.parentNode.appendChild(span);
  field.focus();
  setTimeout(function () { if (span.parentNode) span.remove(); }, 4000);
}

// ── SIDEBAR MOBILE TOGGLE ────────────────────────
function toggleSidebar() {
  var sb = document.querySelector('.sidebar');
  if (sb) sb.classList.toggle('open');
}

// ── STAFF TAB SWITCHING ──────────────────────────
function switchTab(tabId) {
  var panes = document.querySelectorAll('.tab-pane');
  var btns = document.querySelectorAll('.tab-btn');
  panes.forEach(function (p) { p.classList.remove('active'); });
  btns.forEach(function (b) { b.classList.remove('active'); });
  var target = document.getElementById(tabId);
  if (target) target.classList.add('active');
  var activeBtn = document.querySelector('[data-tab="' + tabId + '"]');
  if (activeBtn) activeBtn.classList.add('active');
}

// ── COPY DEMO CREDENTIALS ────────────────────────
function copyCredential(el) {
  var text = el.textContent;
  navigator.clipboard && navigator.clipboard.writeText(text).then(function () {
    var orig = el.textContent;
    el.textContent = 'Copied!';
    setTimeout(function () { el.textContent = orig; }, 1200);
  });
}

// ── BOOKING PRICE CALCULATOR ─────────────────────
document.addEventListener('DOMContentLoaded', function () {
  var checkin = document.getElementById('check_in');
  var checkout = document.getElementById('check_out');
  var priceDisplay = document.getElementById('totalPriceDisplay');
  var pricePerNight = parseFloat(document.getElementById('pricePerNight') ? document.getElementById('pricePerNight').value : 0);
  function updatePrice() {
    if (!checkin || !checkout || !priceDisplay) return;
    var inDate = new Date(checkin.value);
    var outDate = new Date(checkout.value);
    if (isNaN(inDate) || isNaN(outDate) || outDate <= inDate) {
      priceDisplay.textContent = '—';
      return;
    }
    var nights = Math.round((outDate - inDate) / 86400000);
    var total = nights * pricePerNight;
    var tax = total * 0.12;
    priceDisplay.innerHTML = nights + ' night' + (nights !== 1 ? 's' : '') +
      ' &times; ₹' + pricePerNight.toLocaleString() +
      ' = ₹' + total.toLocaleString() +
      ' + ₹' + Math.round(tax).toLocaleString() + ' tax = <strong>₹' + Math.round(total + tax).toLocaleString() + '</strong>';
  }
  if (checkin) checkin.addEventListener('change', updatePrice);
  if (checkout) checkout.addEventListener('change', updatePrice);

  // Set min date to today
  var today = new Date().toISOString().split('T')[0];
  if (checkin) checkin.setAttribute('min', today);
  if (checkout) checkout.setAttribute('min', today);
  if (checkin) checkin.addEventListener('change', function () {
    if (checkout) checkout.setAttribute('min', checkin.value);
  });
});

// ── FOOD CART ────────────────────────────────────
var cart = {};

function addToCart(id, name, price) {
  if (!cart[id]) cart[id] = { name: name, price: price, qty: 0 };
  cart[id].qty++;
  renderCart();
}

function removeFromCart(id) {
  if (!cart[id]) return;
  cart[id].qty--;
  if (cart[id].qty <= 0) delete cart[id];
  renderCart();
}

function renderCart() {
  var cartItems = document.getElementById('cartItems');
  var cartTotal = document.getElementById('cartTotal');
  var cartCount = document.getElementById('cartCount');
  var cartEmpty = document.getElementById('cartEmpty');
  var checkoutBtn = document.getElementById('checkoutBtn');

  var keys = Object.keys(cart);
  var total = 0;
  var count = 0;

  if (cartItems) {
    if (keys.length === 0) {
      cartItems.innerHTML = '';
      if (cartEmpty) cartEmpty.style.display = 'block';
    } else {
      if (cartEmpty) cartEmpty.style.display = 'none';
      cartItems.innerHTML = keys.map(function (id) {
        var item = cart[id];
        total += item.price * item.qty;
        count += item.qty;
        return '<div class="cart-item">' +
          '<div class="cart-item-info"><span class="cart-item-name">' + item.name + '</span>' +
          '<span class="cart-item-price">₹' + (item.price * item.qty).toLocaleString() + '</span></div>' +
          '<div class="cart-item-qty">' +
          '<button class="qty-btn" onclick="removeFromCart(\'' + id + '\')" aria-label="decrease">−</button>' +
          '<span>' + item.qty + '</span>' +
          '<button class="qty-btn" onclick="addToCart(\'' + id + '\', \'' + item.name.replace(/'/g, "\\'") + '\', ' + item.price + ')" aria-label="increase">+</button>' +
          '</div></div>';
      }).join('');
    }
  }

  if (cartTotal) cartTotal.textContent = '₹' + total.toLocaleString();
  if (cartCount) { cartCount.textContent = count; cartCount.style.display = count > 0 ? 'inline-flex' : 'none'; }
  if (checkoutBtn) checkoutBtn.disabled = keys.length === 0;
}

function toggleCart() {
  var panel = document.querySelector('.cart-panel');
  if (panel) panel.classList.toggle('cart-open');
}

function placeOrder() {
  var keys = Object.keys(cart);
  if (keys.length === 0) return;
  var items = keys.map(function (id) { return { id: id, name: cart[id].name, price: cart[id].price, qty: cart[id].qty }; });
  showLoading('Placing your order…');
  fetch('/guest/place-order', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items: items })
  }).then(function (r) { return r.json(); }).then(function (data) {
    hideLoading();
    if (data.success) {
      cart = {};
      renderCart();
      showToast('Order placed successfully!', 'success');
      setTimeout(function () { location.reload(); }, 1500);
    } else {
      showToast(data.error || 'Failed to place order.', 'error');
    }
  }).catch(function () { hideLoading(); showToast('Network error. Try again.', 'error'); });
}

// ── TOAST NOTIFICATIONS ──────────────────────────
function showToast(msg, type) {
  var container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.cssText = 'position:fixed;bottom:2rem;right:2rem;z-index:9999;display:flex;flex-direction:column;gap:0.5rem;';
    document.body.appendChild(container);
  }
  var toast = document.createElement('div');
  toast.style.cssText = 'background:' + (type === 'success' ? '#27ae60' : '#e74c3c') +
    ';color:#fff;padding:0.8rem 1.2rem;border-radius:8px;font-size:0.9rem;' +
    'box-shadow:0 4px 20px rgba(0,0,0,0.3);opacity:1;transition:opacity 0.4s;max-width:300px;';
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(function () { toast.style.opacity = '0'; setTimeout(function () { toast.remove(); }, 400); }, 3000);
}

// ── STATUS POLLING ───────────────────────────────
function pollOrderStatus(orderId, statusEl) {
  if (!orderId || !statusEl) return;
  setInterval(function () {
    fetch('/guest/api/order-status/' + orderId)
      .then(function (r) { return r.json(); })
      .then(function (d) { if (d.status) { statusEl.textContent = d.status; statusEl.className = 'badge badge-' + d.status.toLowerCase().replace(/\s/g, '-'); } })
      .catch(function () {});
  }, 15000);
}

function pollServiceStatus(reqId, statusEl) {
  if (!reqId || !statusEl) return;
  setInterval(function () {
    fetch('/guest/api/service-status/' + reqId)
      .then(function (r) { return r.json(); })
      .then(function (d) { if (d.status) { statusEl.textContent = d.status; statusEl.className = 'badge badge-' + d.status.toLowerCase().replace(/\s/g, '-'); } })
      .catch(function () {});
  }, 15000);
}

// ── STAFF INLINE STATUS UPDATE ───────────────────
function updateStatus(form) {
  showLoading('Updating…');
  var fd = new FormData(form);
  fetch(form.action, { method: 'POST', body: fd })
    .then(function (r) { return r.json(); })
    .then(function (d) {
      hideLoading();
      if (d.success) { showToast('Status updated!', 'success'); }
      else { showToast(d.error || 'Update failed.', 'error'); }
    }).catch(function () { hideLoading(); showToast('Network error.', 'error'); });
  return false;
}

// ── INVOICE PRINT ────────────────────────────────
function printInvoice() { window.print(); }

// ── ROOM FILTER ──────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  var filterBtns = document.querySelectorAll('.filter-btn');
  filterBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      filterBtns.forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      var filter = btn.getAttribute('data-filter');
      var cards = document.querySelectorAll('.room-card');
      cards.forEach(function (card) {
        if (filter === 'all' || card.getAttribute('data-type') === filter) {
          card.style.display = '';
        } else {
          card.style.display = 'none';
        }
      });
    });
  });
});

// ── SERVICE TYPE SELECTOR ────────────────────────
function selectServiceType(el, value) {
  var btns = document.querySelectorAll('.service-type-btn');
  btns.forEach(function (b) { b.classList.remove('active'); });
  el.classList.add('active');
  var input = document.getElementById('service_type_input');
  if (input) input.value = value;
}

// ── DEMO CREDENTIAL FILL ─────────────────────────
function fillLogin(email, password, tab) {
  // Switch to right tab first
  if (tab) {
    var tabBtns = document.querySelectorAll('.login-tab');
    var panels = document.querySelectorAll('.login-panel');
    tabBtns.forEach(function (b) { b.classList.remove('active'); });
    panels.forEach(function (p) { p.classList.remove('active'); });
    var btn = document.querySelector('[data-panel="' + tab + '"]');
    var panel = document.getElementById(tab + 'Panel');
    if (btn) btn.classList.add('active');
    if (panel) panel.classList.add('active');
  }
  setTimeout(function () {
    var emailField = tab === 'staff'
      ? document.querySelector('#staffPanel [name="email"]')
      : document.querySelector('#guestPanel [name="email"]');
    var passField = tab === 'staff'
      ? document.querySelector('#staffPanel [name="password"]')
      : document.querySelector('#guestPanel [name="password"]');
    if (emailField) emailField.value = email;
    if (passField) passField.value = password;
  }, 100);
}

// ── INIT ─────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  renderCart();
  hideLoading();
});
