async function checkToken() {
    const partner_token = localStorage.getItem('partner_token');
    const currentUrl = window.location.pathname + window.location.search;

    if (!partner_token) {
        alert('Bạn chưa đăng nhập');
        window.location.href = `/login?redirectpartner=${encodeURIComponent(currentUrl)}`;
        return;
    }

    try {
        const response = await fetch('/check_token_acc/', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${partner_token}`
            }
        });
        if (!response.ok) {
            alert('Hết phiên sử dụng. Vui lòng đăng nhập lại.');
            window.location.href = `/login?redirectpartner=${encodeURIComponent(currentUrl)}`;
        }
    } catch (error) {
        alert(error.message);
        window.location.href = `/login?redirectpartner=${encodeURIComponent(currentUrl)}`;
    }
}

checkToken();
console.log('Checked');
