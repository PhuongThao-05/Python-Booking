async function checkToken() {
    const customer_token = localStorage.getItem('customer_token');
    const currentUrl = window.location.pathname + window.location.search;

    if (!customer_token) {
        alert('Bạn chưa đăng nhập');
        window.location.href = `/login?redirect=${encodeURIComponent(currentUrl)}`;
        return;
    }

    try {
        const response = await fetch('/check_token_acc/', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${customer_token}`
            }
        });
        if (!response.ok) {
            alert('Hết phiên sử dụng. Vui lòng đăng nhập lại.');
            window.location.href = `/login?redirect=${encodeURIComponent(currentUrl)}`;
        }
    } catch (error) {
        alert(error.message);
        window.location.href = `/login?redirect=${encodeURIComponent(currentUrl)}`;
    }
}

checkToken();
console.log('Checked customer');
