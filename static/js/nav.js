/**
 * SmartCart Responsive Mobile Navigation Bars & Menu Controller
 * Provides:
 * 1. Mobile Top Hamburger Drawer Menu Toggle
 * 2. Amazon-Style Mobile Sub-Navbar Bar (Categories & Quick Links)
 * 3. Fixed Mobile Bottom Navigation Tab Bar (Home, Store, Orders, You, Cart)
 * 4. Automatic Route Highlighting & Dynamic Cart Badge Synchronization
 */
document.addEventListener('DOMContentLoaded', function () {
    const currentPath = window.location.pathname.toLowerCase();

    // 1. Initialize Top Header Hamburger & Drawer
    function initHeaderDrawer() {
        const headers = document.querySelectorAll('.vintage-header, .modern-header');
        headers.forEach(header => {
            const inner = header.querySelector('.header-inner');
            const nav = header.querySelector('nav');
            if (!inner || !nav) return;

            // Ensure toggle button exists in header-inner
            let toggleBtn = header.querySelector('.nav-toggle-btn');
            if (!toggleBtn) {
                toggleBtn = document.createElement('button');
                toggleBtn.className = 'nav-toggle-btn';
                toggleBtn.type = 'button';
                toggleBtn.setAttribute('aria-label', 'Toggle Navigation Menu');
                toggleBtn.innerHTML = `
                    <span class="hamburger-bar"></span>
                    <span class="hamburger-bar"></span>
                    <span class="hamburger-bar"></span>
                `;
                inner.appendChild(toggleBtn);
            }

            // Click listener to toggle drawer
            toggleBtn.addEventListener('click', function (e) {
                e.stopPropagation();
                const isOpen = header.classList.toggle('nav-open');
                toggleBtn.classList.toggle('is-open', isOpen);
            });

            // Handle mobile click on user-profile-pill to expand dropdown
            const userMenu = nav.querySelector('.user-account-menu');
            if (userMenu) {
                const userPill = userMenu.querySelector('.user-profile-pill');
                if (userPill) {
                    userPill.addEventListener('click', function (e) {
                        if (window.innerWidth <= 880) {
                            e.preventDefault();
                            e.stopPropagation();
                            userMenu.classList.toggle('menu-expanded');
                        }
                    });
                }
            }

            // Close drawer when clicking regular links
            const regularLinks = nav.querySelectorAll('a:not(.user-profile-pill)');
            regularLinks.forEach(link => {
                link.addEventListener('click', function () {
                    if (window.innerWidth <= 880) {
                        header.classList.remove('nav-open');
                        toggleBtn.classList.remove('is-open');
                    }
                });
            });

            // Close when clicking outside header
            document.addEventListener('click', function (e) {
                if (!header.contains(e.target)) {
                    header.classList.remove('nav-open');
                    toggleBtn.classList.remove('is-open');
                }
            });

            // Close when window resized to desktop
            window.addEventListener('resize', function () {
                if (window.innerWidth > 880) {
                    header.classList.remove('nav-open');
                    toggleBtn.classList.remove('is-open');
                }
            });
        });
    }

    // 2. Inject or Configure Mobile Sub-Navbar (Quick-Access Bar under header)
    function initMobileSubBar() {
        const header = document.querySelector('.vintage-header, .modern-header');
        if (!header) return;

        // If sub-bar not already in DOM, create and insert right after header
        let subBar = document.querySelector('.mobile-sub-bar');
        if (!subBar) {
            subBar = document.createElement('div');
            subBar.className = 'mobile-sub-bar';
            subBar.innerHTML = `
                <div class="mobile-sub-bar-inner">
                    <button type="button" class="mobile-sub-pill mobile-menu-trigger" aria-label="Open Menu">☰ All Menu</button>
                    <a href="/user/products" class="mobile-sub-pill ${currentPath === '/user/products' ? 'active' : ''}">🛍️ Store</a>
                    <a href="/user/products?category=Electronics" class="mobile-sub-pill">⚡ Electronics</a>
                    <a href="/user/products?category=Fashion" class="mobile-sub-pill">👕 Fashion</a>
                    <a href="/user/products?category=Fitness" class="mobile-sub-pill">🚴 Fitness</a>
                    <a href="/user/products?category=Books" class="mobile-sub-pill">📚 Books</a>
                    <a href="/user/my-orders" class="mobile-sub-pill ${currentPath.includes('order') ? 'active' : ''}">📦 Orders</a>
                    <a href="/user/cart" class="mobile-sub-pill ${currentPath.includes('cart') ? 'active' : ''}">🛒 Cart</a>
                </div>
            `;
            header.parentNode.insertBefore(subBar, header.nextSibling);
        }

        // Connect "☰ All Menu" button to open the header drawer
        const menuTrigger = subBar.querySelector('.mobile-menu-trigger');
        if (menuTrigger) {
            menuTrigger.addEventListener('click', function (e) {
                e.stopPropagation();
                const isOpen = header.classList.toggle('nav-open');
                const toggleBtn = header.querySelector('.nav-toggle-btn');
                if (toggleBtn) toggleBtn.classList.toggle('is-open', isOpen);
                if (isOpen) {
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }
            });
        }
    }

    // 3. Inject or Configure Mobile Bottom Fixed Tab Bar
    function initMobileBottomBar() {
        let bottomBar = document.querySelector('.mobile-bottom-bar');
        if (bottomBar) return; // Already present in DOM

        // Determine user profile / account target URL & icon
        const isLoggedIn = !!document.querySelector('.user-account-menu') || currentPath.includes('/user/') || currentPath.includes('/user-dashboard');
        const profileUrl = isLoggedIn ? '/user/profile' : '/user-login';
        const profileLabel = isLoggedIn ? 'You' : 'Sign In';

        // Get live cart count
        const cartCountEl = document.getElementById('cart-count') || document.querySelector('.cart-counter-pill');
        const cartCount = cartCountEl ? cartCountEl.textContent.trim() : '0';

        // Check active states
        const isHome = currentPath === '/' || currentPath === '/index';
        const isProducts = currentPath === '/user/products' || currentPath.startsWith('/user/product/');
        const isOrders = currentPath.includes('/my-orders') || currentPath.includes('/order');
        const isProfile = currentPath.includes('/profile') || currentPath.includes('/user-login') || currentPath.includes('/user-dashboard');
        const isCart = currentPath.includes('/cart') || currentPath.includes('/payment');

        bottomBar = document.createElement('nav');
        bottomBar.className = 'mobile-bottom-bar';
        bottomBar.setAttribute('aria-label', 'Mobile Bottom Navigation');
        bottomBar.innerHTML = `
            <div class="mobile-bottom-bar-inner">
                <a href="/" class="mobile-bottom-item ${isHome ? 'active' : ''}">
                    <span class="mobile-bottom-icon">🏠</span>
                    <span class="mobile-bottom-label">Home</span>
                </a>
                <a href="/user/products" class="mobile-bottom-item ${isProducts ? 'active' : ''}">
                    <span class="mobile-bottom-icon">🛍️</span>
                    <span class="mobile-bottom-label">Store</span>
                </a>
                <a href="/user/my-orders" class="mobile-bottom-item ${isOrders ? 'active' : ''}">
                    <span class="mobile-bottom-icon">📦</span>
                    <span class="mobile-bottom-label">Orders</span>
                </a>
                <a href="${profileUrl}" class="mobile-bottom-item ${isProfile ? 'active' : ''}">
                    <span class="mobile-bottom-icon">👤</span>
                    <span class="mobile-bottom-label">${profileLabel}</span>
                </a>
                <a href="/user/cart" class="mobile-bottom-item ${isCart ? 'active' : ''}">
                    <span class="mobile-bottom-icon">
                        🛒
                        <span class="mobile-cart-badge" id="mobile-cart-count">${cartCount}</span>
                    </span>
                    <span class="mobile-bottom-label">Cart</span>
                </a>
            </div>
        `;

        document.body.appendChild(bottomBar);

        // Periodically sync cart count if updated dynamically
        const observer = new MutationObserver(() => {
            const updatedEl = document.getElementById('cart-count') || document.querySelector('.cart-counter-pill');
            const mobileBadge = document.getElementById('mobile-cart-count');
            if (updatedEl && mobileBadge) {
                mobileBadge.textContent = updatedEl.textContent.trim();
            }
        });

        const targetCountEl = document.getElementById('cart-count') || document.querySelector('.cart-counter-pill');
        if (targetCountEl) {
            observer.observe(targetCountEl, { childList: true, characterData: true, subtree: true });
        }
    }

    // Initialize all components
    initHeaderDrawer();
    initMobileSubBar();
    initMobileBottomBar();
});
