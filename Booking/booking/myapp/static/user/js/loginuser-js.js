document.getElementById("loginForm").addEventListener("submit", async function(event) {
    event.preventDefault();
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const result = await response.json();
        if (result.success) {  
            if(!result.identify)
            {
                localStorage.setItem('token', result.token);
                const userInfo = {
                    identify: result.identify,
                    hoten: result.hoten,
                    username:result.username,
                };
                localStorage.setItem('userInfo', JSON.stringify(userInfo));
                await fetch('/api/user/expire', {
                    method: 'PUT',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + localStorage.getItem('token')
                     },
                });
                await fetch('/api/user/renewaccount', {
                    method: 'PUT',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + localStorage.getItem('token')
                     },
                });
                const params = new URLSearchParams(window.location.search);
                const redirectUrl = params.get('redirect');
                if (redirectUrl) {
                window.location.href = redirectUrl; 
                } else {
                    window.location.href = '/user/home'; 
                }
            }
            else { 
                document.getElementById('errorMessage').textContent ='Account is not authorized';            
            }
        } else {
            document.getElementById('errorMessage').textContent = result.message || 'Đã xảy ra lỗi';
        }
    } catch (error) {
        console.error("Error:", error);
        alert("Đã xảy ra lỗi khi đăng nhập.");
    }
});