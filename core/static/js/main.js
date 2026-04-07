// Auto-dismiss toasts after 4 seconds
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.toast').forEach(function (toast) {
    setTimeout(function () {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity .4s';
      setTimeout(function () { toast.remove(); }, 400);
    }, 4000);
  });
});