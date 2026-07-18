// Theme Toggling Logic
const themeToggleBtn = document.getElementById('themeToggleBtn');
const themeIcon = themeToggleBtn.querySelector('i');

// Check saved theme or use system preference
const savedTheme = localStorage.getItem('theme');
const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

if (savedTheme === 'dark' || (!savedTheme && systemDark)) {
    document.body.classList.add('dark-mode');
    themeIcon.classList.replace('fa-moon', 'fa-sun');
} else {
    document.body.classList.remove('dark-mode');
    themeIcon.classList.replace('fa-sun', 'fa-moon');
}

// Click listener to toggle theme
themeToggleBtn.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    
    if (isDark) {
        themeIcon.classList.replace('fa-moon', 'fa-sun');
        localStorage.setItem('theme', 'dark');
    } else {
        themeIcon.classList.replace('fa-sun', 'fa-moon');
        localStorage.setItem('theme', 'light');
    }
});

// FAQ Accordion Toggle Actions
document.addEventListener('DOMContentLoaded', () => {
    const faqQuestions = document.querySelectorAll('.faq-question');
    
    faqQuestions.forEach(question => {
        question.addEventListener('click', () => {
            const faqItem = question.parentElement;
            
            // Toggle current item
            faqItem.classList.toggle('open');
            
            // Close other open FAQ items
            faqQuestions.forEach(otherQuestion => {
                const otherItem = otherQuestion.parentElement;
                if (otherItem !== faqItem && otherItem.classList.contains('open')) {
                    otherItem.classList.remove('open');
                }
            });
        });
    });
});

// Helper for displaying a simple status message in the workspace
function showStatusMessage(container, text, type = 'info') {
    const color = type === 'error' ? '#ef4444' : (type === 'success' ? '#10b981' : '#3b82f6');
    container.innerHTML = `
        <div style="padding: 1rem; border-radius: 8px; border: 1px solid ${color}; background-color: rgba(59,130,246,0.05); text-align: center; font-weight: 500;">
            ${text}
        </div>
    `;
}
