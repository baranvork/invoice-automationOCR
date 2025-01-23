document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const fileInput = document.querySelector('input[type="file"]');
    
    if (form) {
        form.onsubmit = function(e) {
            if (!fileInput.value) {
                e.preventDefault();
                alert('Lütfen bir dosya seçin');
            }
        };
    }
}); 