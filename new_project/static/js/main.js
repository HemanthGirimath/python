// Theme Toggle
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.querySelector('.theme-toggle');
    const body = document.body;
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        body.classList.add(savedTheme);
        updateThemeIcon(savedTheme === 'light-theme');
    }

    if (themeToggle) {  // Only add listener if element exists
        themeToggle.addEventListener('click', function() {
            body.classList.toggle('light-theme');
            body.classList.toggle('dark-theme');
            
            const isLight = body.classList.contains('light-theme');
            updateThemeIcon(isLight);
            
            // Save theme preference
            localStorage.setItem('theme', isLight ? 'light-theme' : 'dark-theme');
        });
    }
});

function updateThemeIcon(isLight) {
    const icon = document.querySelector('.theme-toggle i');
    icon.classList.remove('fa-sun', 'fa-moon');
    icon.classList.add(isLight ? 'fa-moon' : 'fa-sun');
}

// Navigation Active State
const navItems = document.querySelectorAll('.nav-item');
navItems.forEach(item => {
    item.addEventListener('click', function() {
        navItems.forEach(nav => nav.classList.remove('active'));
        this.classList.add('active');
    });
});

// User Dropdown
document.addEventListener('click', function(e) {
    const userMenu = document.querySelector('.user-menu');
    const dropdown = document.querySelector('.user-dropdown');
    
    if (!userMenu.contains(e.target)) {
        dropdown.style.display = 'none';
    }
});

// Notification Badge Update
function updateNotificationBadge(count) {
    const badge = document.querySelector('.notification-badge');
    if (count > 0) {
        badge.style.display = 'inline';
        badge.textContent = count;
    } else {
        badge.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Remove the old navigation click handlers
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        // Remove any existing click event listeners
        item.removeEventListener('click', function(e) {
            e.preventDefault(); // This was causing the # in URL
        });
    });
}); 