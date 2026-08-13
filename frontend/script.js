var typed = new Typed('#element', {
    strings: ['Data Science Enthusiast', 'Machine Learning Developer', 'AI Explorer', 'Problem Solver',],
    typeSpeed: 50,
    backSpeed: 30,
    loop: true
});

const sections = document.querySelectorAll('.section');
const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, {
    threshold: 0.1
});

sections.forEach(section => {
    observer.observe(section);
});

const themeToggle = document.getElementById('theme-toggle');
const body = document.body;

function applyTheme(theme) {
    if (theme === 'dark') {
        body.classList.add('dark-mode');
        themeToggle.classList.remove('fa-moon');
        themeToggle.classList.add('fa-sun');
    } else {
        body.classList.remove('dark-mode');
        themeToggle.classList.remove('fa-sun');
        themeToggle.classList.add('fa-moon');
    }
}

const savedTheme = localStorage.getItem('theme') || 'light';
applyTheme(savedTheme);

themeToggle.addEventListener('click', () => {
    let newTheme = body.classList.contains('dark-mode') ? 'light' : 'dark';
    applyTheme(newTheme);
    localStorage.setItem('theme', newTheme);
});

// Contact Form Submit Handler
const contactForm = document.getElementById('contactForm');
const sendBtn = document.getElementById('sendBtn');
const responseMsg = document.getElementById('responseMsg');

if (contactForm) {
    contactForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const name = document.getElementById('name').value.trim();
        const email = document.getElementById('email').value.trim();
        const message = document.getElementById('message').value.trim();

        if (!name || !email || !message) {
            showResponse("Please fill in all fields.", "error");
            return;
        }

        // Show loading state
        sendBtn.disabled = true;
        sendBtn.textContent = 'Sending...';
        responseMsg.className = 'response-msg';
        responseMsg.textContent = '';

        try {
            const response = await fetch('/api/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, message })
            });

            const result = await response.json();

            if (response.ok) {
                showResponse(result.message || 'Message sent successfully!', 'success');
                contactForm.reset();
            } else {
                showResponse(result.message || 'Failed to send message. Please try again.', 'error');
            }
        } catch (error) {
            console.error('Error sending feedback:', error);
            showResponse('An error occurred. Please check your connection and try again.', 'error');
        } finally {
            sendBtn.disabled = false;
            sendBtn.textContent = 'Send Message';
        }
    });
}

function showResponse(text, type) {
    if (responseMsg) {
        responseMsg.textContent = text;
        responseMsg.className = `response-msg ${type}`;
        responseMsg.style.display = 'block';
    }
}
