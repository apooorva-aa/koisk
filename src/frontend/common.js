function navigate(page) {
    window.location.href = page;
}

function goBack() {
    window.history.back();
}

function goHome() {
    window.location.href = 'kiosk-main.html';
}

function checkAuth() {
    const userRole = sessionStorage.getItem('userRole');
    if (!userRole) {
        window.location.href = 'auth.html';
        return null;
    }
    return userRole;
}

function checkAdminAuth() {
    const userRole = checkAuth();
    if (userRole !== 'admin') {
        alert('Admin access required');
        window.location.href = 'kiosk-main.html';
        return false;
    }
    return true;
}

function logout() {
    sessionStorage.clear();
    window.location.href = 'auth.html';
}
