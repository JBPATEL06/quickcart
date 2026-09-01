/**
 * QuickCart - Interactive JavaScript & AJAX Engine
 * Flowstep UI interactions, Sticky Compare Bar, Voice Search, Cart & Wishlist
 */

$(document).ready(function () {
    // 1. Theme Toggle (Light / Dark)
    const currentTheme = localStorage.getItem('qc_theme') || 'light';
    $('html').attr('data-theme', currentTheme);
    $('#theme-switch').prop('checked', currentTheme === 'dark');

    $('#theme-switch').on('change', function () {
        const theme = $(this).is(':checked') ? 'dark' : 'light';
        $('html').attr('data-theme', theme);
        localStorage.setItem('qc_theme', theme);
    });

    // 2. Voice Search (Web Speech API + Visual Feedback)
    const micBtn = $('.qc-mic-btn');
    let recognition = null;
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        try {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            recognition.onstart = function () {
                micBtn.addClass('listening');
                showToast('🎙️ Listening... Speak your search query now');
            };

            recognition.onresult = function (event) {
                const transcript = event.results[0][0].transcript;
                $('.qc-search-input').val(transcript);
                micBtn.removeClass('listening');
                showToast(`Searching for "${transcript}"...`);
                window.location.href = `/search/?q=${encodeURIComponent(transcript)}`;
            };

            recognition.onerror = function (event) {
                micBtn.removeClass('listening');
                console.warn('Speech recognition error:', event.error);
                if (event.error === 'not-allowed') {
                    showToast('Microphone access blocked. Please allow mic permission.');
                } else {
                    showToast('Voice recognition ended. Try speaking again.');
                }
            };

            recognition.onend = function () {
                micBtn.removeClass('listening');
            };
        } catch (e) {
            console.error('Speech recognition init error:', e);
        }
    }

    micBtn.on('click', function (e) {
        e.preventDefault();
        if (recognition) {
            try {
                recognition.start();
            } catch (err) {
                // If already active, restart
                try {
                    recognition.stop();
                    recognition.start();
                } catch (e2) {
                    showToast('🎙️ Listening... Speak your search query now');
                }
            }
        } else {
            // Fallback for browsers without speech recognition support
            const promptQuery = prompt("Voice Search not supported in this browser. Enter spoken search:", "Smart watch under 2000");
            if (promptQuery) {
                $('.qc-search-input').val(promptQuery);
                window.location.href = `/search/?q=${encodeURIComponent(promptQuery)}`;
            }
        }
    });

    // 3. Search Autocomplete
    let searchDebounceTimer;
    $('.qc-search-input').on('input', function () {
        clearTimeout(searchDebounceTimer);
        const query = $(this).val().trim();
        const dropdown = $('.qc-search-autocomplete');

        if (query.length < 2) {
            dropdown.hide().empty();
            return;
        }

        searchDebounceTimer = setTimeout(() => {
            $.get('/api/search/autocomplete/', { q: query }, function (data) {
                dropdown.empty();
                if (data.results && data.results.length > 0) {
                    data.results.forEach(item => {
                        dropdown.append(`
                            <a href="${item.url}" class="qc-autocomplete-item">
                                <img src="${item.image}" class="qc-autocomplete-thumb" alt="${item.name}">
                                <div class="flex-1">
                                    <div class="fw-semibold text-truncate small">${item.name}</div>
                                    <div class="text-muted small">₹${item.price}</div>
                                </div>
                            </a>
                        `);
                    });
                    dropdown.show();
                } else {
                    dropdown.hide();
                }
            });
        }, 250);
    });

    $(document).on('click', function (e) {
        if (!$(e.target).closest('.qc-search-wrapper').length) {
            $('.qc-search-autocomplete').hide();
        }
    });

    // 4. Sticky Product Comparison Bar (Screen 3 & Screen 6)
    let comparedIds = JSON.parse(sessionStorage.getItem('qc_compare_ids') || '[]');

    function updateCompareUI() {
        $('.qc-compare-checkbox').each(function () {
            const id = parseInt($(this).val());
            $(this).prop('checked', comparedIds.includes(id));
        });

        const bar = $('#qc-compare-bar');
        const thumbsContainer = $('#qc-compare-thumbs');
        const countSpan = $('#qc-compare-count');

        if (comparedIds.length > 0) {
            bar.addClass('show');
            countSpan.text(comparedIds.length);
            thumbsContainer.empty();

            comparedIds.forEach(id => {
                const card = $(`[data-product-id="${id}"]`);
                const imgSrc = card.data('product-image') || '/static/images/placeholder.jpg';
                thumbsContainer.append(`
                    <img src="${imgSrc}" class="qc-compare-thumb" alt="Compare item">
                `);
            });

            // Fill empty slots up to min 3 or active length + 1
            const maxSlots = Math.min(Math.max(comparedIds.length + 1, 3), 10);
            for (let i = comparedIds.length; i < maxSlots; i++) {
                thumbsContainer.append(`
                    <div class="qc-compare-thumb d-flex align-items-center justify-content-center text-muted" style="border: 1px dashed var(--border-color)">
                        <i class="bi bi-plus"></i>
                    </div>
                `);
            }
        } else {
            bar.removeClass('show');
        }
    }

    $(document).on('change', '.qc-compare-checkbox', function () {
        const id = parseInt($(this).val());
        if ($(this).is(':checked')) {
            if (comparedIds.length >= 10) {
                $(this).prop('checked', false);
                showToast('You can compare up to 10 products at a time.');
                return;
            }
            if (!comparedIds.includes(id)) {
                comparedIds.push(id);
                showToast('Product added to comparison bar.');
            }
        } else {
            comparedIds = comparedIds.filter(item => item !== id);
            showToast('Product removed from comparison.');
        }

        sessionStorage.setItem('qc_compare_ids', JSON.stringify(comparedIds));
        updateCompareUI();
    });

    $('#btn-compare-now').on('click', function () {
        if (comparedIds.length < 2) {
            showToast('Please select at least 2 products to compare.');
            return;
        }
        window.location.href = `/compare/?ids=${comparedIds.join(',')}`;
    });

    $('#btn-clear-compare').on('click', function () {
        comparedIds = [];
        sessionStorage.setItem('qc_compare_ids', JSON.stringify([]));
        updateCompareUI();
    });

    updateCompareUI();

    // 5. AJAX Add to Cart
    $(document).on('click', '.btn-add-cart', function (e) {
        e.preventDefault();
        const btn = $(this);
        const productId = btn.data('product-id');
        const quantity = parseInt(btn.data('quantity') || 1);

        btn.prop('disabled', true).addClass('opacity-75');

        $.ajax({
            url: '/cart/api/add/',
            type: 'POST',
            data: {
                product_id: productId,
                quantity: quantity,
                csrfmiddlewaretoken: getCsrfToken()
            },
            success: function (res) {
                btn.prop('disabled', false).removeClass('opacity-75');
                $('#cart-badge-count').text(res.total_items).removeClass('d-none');
                showToast(res.message || 'Added to cart successfully!');
            },
            error: function () {
                btn.prop('disabled', false).removeClass('opacity-75');
                showToast('Failed to add to cart. Please try again.');
            }
        });
    });

    // 6. AJAX Wishlist Heart Toggle
    $(document).on('click', '.btn-wishlist-toggle', function (e) {
        e.preventDefault();
        const btn = $(this);
        const productId = btn.data('product-id');

        $.ajax({
            url: '/api/wishlist/toggle/',
            type: 'POST',
            data: {
                product_id: productId,
                csrfmiddlewaretoken: getCsrfToken()
            },
            success: function (res) {
                if (res.saved) {
                    btn.addClass('active text-danger');
                    btn.find('i').removeClass('bi-heart').addClass('bi-heart-fill');
                } else {
                    btn.removeClass('active text-danger');
                    btn.find('i').removeClass('bi-heart-fill').addClass('bi-heart');
                }
                showToast(res.message);
            },
            error: function (xhr) {
                if (xhr.status === 401) {
                    showToast('Please login to add items to your wishlist.');
                    setTimeout(() => {
                        window.location.href = `/accounts/login/?next=${window.location.pathname}`;
                    }, 1200);
                } else {
                    showToast('Could not update wishlist.');
                }
            }
        });
    });

    // 7. Cart Quantity Stepper +/-
    $(document).on('click', '.qc-qty-btn', function () {
        const btn = $(this);
        const action = btn.data('action');
        const itemId = btn.data('item-id');
        const row = $(`#cart-item-row-${itemId}`);

        $.ajax({
            url: '/cart/api/update/',
            type: 'POST',
            data: {
                item_id: itemId,
                action: action,
                csrfmiddlewaretoken: getCsrfToken()
            },
            success: function (res) {
                if (res.item_quantity > 0) {
                    row.find('.qc-qty-val').text(res.item_quantity);
                    row.find('.item-total-price').text('₹' + res.item_total);
                } else {
                    row.fadeOut(300, function () { $(this).remove(); });
                }

                $('#cart-subtotal').text('₹' + res.cart_subtotal);
                if (res.cart_discount && parseFloat(res.cart_discount) > 0) {
                    $('#cart-discount-row').removeClass('d-none');
                    $('#cart-discount').text('-₹' + res.cart_discount);
                } else {
                    $('#cart-discount-row').addClass('d-none');
                }
                $('#cart-shipping').text(res.cart_shipping > 0 ? '₹' + res.cart_shipping : 'FREE');
                $('#cart-tax').text('₹' + res.cart_tax);
                $('#cart-grand-total').text('₹' + res.cart_grand_total);
                $('#cart-badge-count').text(res.cart_total_items);

                if (res.cart_total_items === 0) {
                    location.reload();
                }
            }
        });
    });

    // 8. Remove Item From Cart
    $(document).on('click', '.btn-remove-cart-item', function () {
        const itemId = $(this).data('item-id');
        const row = $(`#cart-item-row-${itemId}`);

        $.ajax({
            url: '/cart/api/remove/',
            type: 'POST',
            data: {
                item_id: itemId,
                csrfmiddlewaretoken: getCsrfToken()
            },
            success: function (res) {
                row.fadeOut(300, function () { $(this).remove(); });
                $('#cart-subtotal').text('₹' + res.cart_subtotal);
                if (res.cart_discount && parseFloat(res.cart_discount) > 0) {
                    $('#cart-discount-row').removeClass('d-none');
                    $('#cart-discount').text('-₹' + res.cart_discount);
                } else {
                    $('#cart-discount-row').addClass('d-none');
                }
                $('#cart-shipping').text(res.cart_shipping > 0 ? '₹' + res.cart_shipping : 'FREE');
                $('#cart-tax').text('₹' + res.cart_tax);
                $('#cart-grand-total').text('₹' + res.cart_grand_total);
                $('#cart-badge-count').text(res.cart_total_items);

                if (res.cart_total_items === 0) {
                    location.reload();
                }
            }
        });
    });

    // 9. Apply Promo Code
    function applyPromoCode(code) {
        if (!code) {
            showToast('Please enter a promo code.');
            return;
        }

        $.ajax({
            url: '/cart/api/promo/apply/',
            type: 'POST',
            data: {
                promo_code: code,
                csrfmiddlewaretoken: getCsrfToken()
            },
            success: function (res) {
                if (res.success) {
                    $('#cart-promo-label').text(res.promo_code);
                    $('#cart-discount').text('-₹' + res.discount_amount);
                    $('#cart-discount-row').removeClass('d-none');
                    $('#btn-remove-promo').removeClass('d-none');
                    $('#promo-code-input').val(res.promo_code);

                    $('#cart-subtotal').text('₹' + res.subtotal);
                    $('#cart-shipping').text(parseFloat(res.shipping) > 0 ? '₹' + res.shipping : 'FREE');
                    $('#cart-tax').text('₹' + res.tax);
                    $('#cart-grand-total').text('₹' + res.grand_total);

                    showToast(res.message);
                }
            },
            error: function (xhr) {
                const err = xhr.responseJSON ? xhr.responseJSON.message : 'Failed to apply promo code.';
                showToast(err);
            }
        });
    }

    $(document).on('click', '#btn-apply-promo', function () {
        const code = $('#promo-code-input').val().trim();
        applyPromoCode(code);
    });

    $(document).on('keypress', '#promo-code-input', function (e) {
        if (e.which === 13) {
            e.preventDefault();
            const code = $(this).val().trim();
            applyPromoCode(code);
        }
    });

    $(document).on('click', '.promo-chip', function () {
        const code = $(this).data('code');
        $('#promo-code-input').val(code);
        applyPromoCode(code);
    });

    // 10. Remove Promo Code
    $(document).on('click', '#btn-remove-promo', function () {
        $.ajax({
            url: '/cart/api/promo/remove/',
            type: 'POST',
            data: {
                csrfmiddlewaretoken: getCsrfToken()
            },
            success: function (res) {
                $('#cart-discount-row').addClass('d-none');
                $('#btn-remove-promo').addClass('d-none');
                $('#promo-code-input').val('');

                $('#cart-subtotal').text('₹' + res.subtotal);
                $('#cart-shipping').text(parseFloat(res.shipping) > 0 ? '₹' + res.shipping : 'FREE');
                $('#cart-tax').text('₹' + res.tax);
                $('#cart-grand-total').text('₹' + res.grand_total);

                showToast(res.message);
            }
        });
    });

    // Helper: CSRF Token from Cookie
    function getCsrfToken() {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, 10) === ('csrftoken=')) {
                    cookieValue = decodeURIComponent(cookie.substring(10));
                    break;
                }
            }
        }
        return cookieValue || $('[name=csrfmiddlewaretoken]').val();
    }

    // Helper: Toast Notifications
    window.showToast = function (message) {
        let container = $('.qc-toast-container');
        if (!container.length) {
            $('body').append('<div class="qc-toast-container"></div>');
            container = $('.qc-toast-container');
        }

        const toast = $(`
            <div class="qc-toast">
                <i class="bi bi-info-circle-fill"></i>
                <span>${message}</span>
            </div>
        `);
        container.append(toast);

        setTimeout(() => {
            toast.fadeOut(300, function () { $(this).remove(); });
        }, 3000);
    };
});
