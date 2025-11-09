function guestLogin() {
    sessionStorage.setItem('userRole', 'guest');
    window.location.href = 'kiosk-main.html';
}

function adminLogin(event) {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorMsg = document.getElementById('error-msg');

    if (username === 'admin' && password === 'admin123') {
        sessionStorage.setItem('userRole', 'admin');
        window.location.href = 'kiosk-main.html';
    } else {
        errorMsg.textContent = 'Invalid credentials';
        setTimeout(() => {
            errorMsg.textContent = '';
        }, 3000);
    }
}
