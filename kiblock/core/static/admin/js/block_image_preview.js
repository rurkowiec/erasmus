(function() {
    'use strict';
    
    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {
        // Find the image input field
        const imageInput = document.querySelector('input[name="image"]');
        const clearCheckbox = document.querySelector('input[name="image-clear"]');
        
        if (!imageInput) return;
        
        // Function to update preview
        function updatePreview(file) {
            const preview = document.getElementById('preview-image');
            if (!preview) return;
            
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    // Replace the preview div/image with new image
                    const newImg = document.createElement('img');
                    newImg.id = 'preview-image';
                    newImg.src = e.target.result;
                    newImg.style.cssText = 'max-width: 200px; max-height: 200px; border: 1px solid #ddd; border-radius: 4px;';
                    
                    preview.parentNode.replaceChild(newImg, preview);
                };
                
                reader.readAsDataURL(file);
            } else if (!file) {
                // No file selected or cleared
                const newDiv = document.createElement('div');
                newDiv.id = 'preview-image';
                newDiv.style.cssText = 'color: #999; font-style: italic;';
                newDiv.textContent = 'No image uploaded';
                
                if (preview.parentNode) {
                    preview.parentNode.replaceChild(newDiv, preview);
                }
            }
        }
        
        // Listen for file input changes
        imageInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                updatePreview(this.files[0]);
                // Uncheck the clear checkbox if user selects a new file
                if (clearCheckbox) {
                    clearCheckbox.checked = false;
                }
            }
        });
        
        // Listen for clear checkbox changes
        if (clearCheckbox) {
            clearCheckbox.addEventListener('change', function() {
                if (this.checked) {
                    updatePreview(null);
                    // Clear the file input
                    imageInput.value = '';
                }
            });
        }
    });
})();
