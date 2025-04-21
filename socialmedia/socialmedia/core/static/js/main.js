// core/static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality for friends page
    function openTab(tabId) {
        const tabContents = document.querySelectorAll('.tab-content');
        const tabButtons = document.querySelectorAll('.tab-btn');
        
        tabContents.forEach(content => {
            content.classList.remove('active');
        });
        
        tabButtons.forEach(button => {
            button.classList.remove('active');
        });
        
        document.getElementById(tabId).classList.add('active');
        event.currentTarget.classList.add('active');
    }
    
    // Add click event to tab buttons if they exist
    const tabButtons = document.querySelectorAll('.tab-btn');
    if (tabButtons.length > 0) {
        tabButtons.forEach(button => {
            button.addEventListener('click', function() {
                const tabId = this.getAttribute('onclick').match(/'([^']+)'/)[1];
                openTab(tabId);
            });
        });
    }
    
    // Preview image before upload
    const mediaFileInput = document.getElementById('id_media_file');
    if (mediaFileInput) {
        mediaFileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // You could add a preview here if needed
                }
                reader.readAsDataURL(file);
            }
        });
    }
    
    // Confirm before deleting posts
    const deleteButtons = document.querySelectorAll('.delete-post');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this post?')) {
                e.preventDefault();
            }
        });
    });
    
    // Show file name when selected
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileName = this.files[0]?.name || 'No file selected';
            const label = this.previousElementSibling;
            if (label && label.classList.contains('media-option')) {
                label.textContent = fileName;
            }
        });
    });
});