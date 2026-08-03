document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Lucide Icons if available (loaded via CDN in base template)
    if (window.lucide) {
        window.lucide.createIcons();
    }

    // 2. Mobile Navigation Toggle Drawer
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', () => {
            navLinks.classList.toggle('open');
            // Toggle hamburger icon between menu and x
            const icon = menuToggle.querySelector('i');
            if (icon) {
                if (navLinks.classList.contains('open')) {
                    icon.setAttribute('data-lucide', 'x');
                } else {
                    icon.setAttribute('data-lucide', 'menu');
                }
                if (window.lucide) window.lucide.createIcons();
            }
        });
    }

    // 3. Auto-Dismiss Toast Notifications after 5 seconds
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        const closeBtn = toast.querySelector('.toast-close');
        
        // Manual close
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                toast.style.animation = 'slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) reverse forwards';
                setTimeout(() => toast.remove(), 300);
            });
        }
        
        // Auto dismiss
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(-10px)';
                toast.style.transition = 'all 0.4s ease';
                setTimeout(() => toast.remove(), 400);
            }
        }, 5000);
    });

    // 4. Video Learning Module Tabs
    const tabButtons = document.querySelectorAll('.video-tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    if (tabButtons.length > 0 && tabPanes.length > 0) {
        tabButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetTab = btn.getAttribute('data-tab');
                
                // Set active button
                tabButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Set active pane
                tabPanes.forEach(pane => {
                    if (pane.id === targetTab) {
                        pane.classList.add('active');
                    } else {
                        pane.classList.remove('active');
                    }
                });
            });
        });
    }

    // 5. AJAX Toggle Lecture Completion Progress
    const completeCheckbox = document.getElementById('complete-checkbox');
    if (completeCheckbox) {
        completeCheckbox.addEventListener('change', async (e) => {
            const lectureId = completeCheckbox.getAttribute('data-lecture-id');
            const courseSlug = completeCheckbox.getAttribute('data-course-slug');
            
            try {
                // Disable temporarily to prevent multiple rapid clicks
                completeCheckbox.disabled = true;
                
                const response = await fetch('/api/progress/toggle', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ lecture_id: parseInt(lectureId) })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Update checking styles in playlist sidebar dynamically
                    const playlistItem = document.querySelector(`.playlist-item-btn[data-lecture-id="${lectureId}"]`);
                    if (playlistItem) {
                        if (data.completed) {
                            playlistItem.classList.add('completed');
                            const iconWrap = playlistItem.querySelector('.playlist-item-status-icon');
                            if (iconWrap) {
                                iconWrap.innerHTML = '<i data-lucide="check"></i>';
                            }
                        } else {
                            playlistItem.classList.remove('completed');
                            const iconWrap = playlistItem.querySelector('.playlist-item-status-icon');
                            if (iconWrap) {
                                iconWrap.innerHTML = '';
                            }
                        }
                        if (window.lucide) window.lucide.createIcons();
                    }
                    
                    // Update ProgressBar percentage indicator in UI
                    const progressBars = document.querySelectorAll('.progress-bar');
                    const progressNums = document.querySelectorAll('.progress-num');
                    const completionCountLabels = document.querySelectorAll('.completed-count');
                    
                    progressBars.forEach(bar => {
                        bar.style.width = `${data.progress_percent}%`;
                    });
                    
                    progressNums.forEach(num => {
                        num.textContent = `${data.progress_percent}%`;
                    });

                    completionCountLabels.forEach(lbl => {
                        lbl.textContent = data.completed_count;
                    });
                    
                    // Optional toast confirmation
                    showToast(data.completed ? 'Lesson marked as completed!' : 'Lesson marked as incomplete.', 'info');
                } else {
                    showToast(data.error || 'Failed to update progress.', 'danger');
                    // Revert checkbox state on failure
                    completeCheckbox.checked = !completeCheckbox.checked;
                }
            } catch (err) {
                console.error('Error toggling progress:', err);
                showToast('Network error updating progress.', 'danger');
                completeCheckbox.checked = !completeCheckbox.checked;
            } finally {
                completeCheckbox.disabled = false;
            }
        });
    }

    // 6. Live Search and Category Filtering (Catalog Filter optimization)
    const catalogSearch = document.getElementById('catalog-search');
    const courseCards = document.querySelectorAll('.course-card');
    
    if (catalogSearch && courseCards.length > 0) {
        catalogSearch.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            
            courseCards.forEach(card => {
                const title = card.querySelector('.course-card-title').textContent.toLowerCase();
                const desc = card.querySelector('.course-card-desc').textContent.toLowerCase();
                const category = card.getAttribute('data-category').toLowerCase();
                const activeCategoryTab = document.querySelector('.filter-tab.active');
                const selectedCat = activeCategoryTab ? activeCategoryTab.getAttribute('data-category').toLowerCase() : 'all';
                
                // Text matching conditions
                const matchesText = title.includes(query) || desc.includes(query);
                // Category matching conditions
                const matchesCategory = selectedCat === 'all' || category === selectedCat;
                
                if (matchesText && matchesCategory) {
                    card.style.display = 'flex';
                    card.style.animation = 'slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // Dynamic toast creation utility
    function showToast(message, type = 'info') {
        const container = document.querySelector('.toast-container');
        if (!container) return;
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        let iconName = 'info';
        if (type === 'success') iconName = 'check-circle';
        if (type === 'warning') iconName = 'alert-triangle';
        if (type === 'danger') iconName = 'x-circle';
        
        toast.innerHTML = `
            <i data-lucide="${iconName}"></i>
            <span>${message}</span>
            <button class="toast-close"><i data-lucide="x"></i></button>
        `;
        
        container.appendChild(toast);
        if (window.lucide) window.lucide.createIcons();
        
        // Re-apply event listeners for close btn
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            toast.remove();
        });
        
        // Auto-remove
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-10px)';
            toast.style.transition = 'all 0.4s ease';
            setTimeout(() => toast.remove(), 400);
        }, 4000);
    }
});
