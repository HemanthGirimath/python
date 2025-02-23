document.addEventListener('DOMContentLoaded', function() {
    // No need for click handlers - let the links work naturally
    const currentPath = window.location.pathname;
    
    // Update active state based on current URL
    document.querySelectorAll('.navbar-menu a').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}); 