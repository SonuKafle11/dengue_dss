// Auto-hide Django messages after 3 seconds
document.addEventListener('DOMContentLoaded', function () {
    const messages = document.querySelectorAll('.message');

    messages.forEach(function (msg) {
        setTimeout(function () {
            msg.style.display = 'none';
        }, 3000);
    });
});