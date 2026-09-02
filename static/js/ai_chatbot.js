// QuickCart Floating AI Assistant Client Engine
document.addEventListener('DOMContentLoaded', function () {
  const toggleBtn = document.getElementById('qc-chatbot-toggle-btn');
  const chatWindow = document.getElementById('qc-chatbot-window');
  const closeBtn = document.getElementById('qc-chatbot-close-btn');
  const chatForm = document.getElementById('qc-chat-form');
  const chatInput = document.getElementById('qc-chat-input');
  const messagesContainer = document.getElementById('qc-chat-messages');
  const typingIndicator = document.getElementById('qc-chat-typing');

  if (!toggleBtn || !chatWindow) return;

  // Toggle Chatbot Window
  toggleBtn.addEventListener('click', function () {
    const isHidden = chatWindow.classList.contains('d-none');
    if (isHidden) {
      chatWindow.classList.remove('d-none');
      chatInput.focus();
    } else {
      chatWindow.classList.add('d-none');
    }
  });

  // Global helper to open chatbot and automatically send an initial message
  window.openQuickCartChatbot = function(initialMessage) {
    if (!chatWindow) return;
    chatWindow.classList.remove('d-none');
    if (initialMessage && chatInput && chatForm) {
      chatInput.value = initialMessage;
      chatForm.dispatchEvent(new Event('submit'));
    } else if (chatInput) {
      chatInput.focus();
    }
  };

  if (closeBtn) {
    closeBtn.addEventListener('click', function () {
      chatWindow.classList.add('d-none');
    });
  }

  // Quick Prompt Chips Click
  document.querySelectorAll('.qc-ai-chip').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const prompt = this.getAttribute('data-prompt');
      chatInput.value = prompt;
      chatForm.dispatchEvent(new Event('submit'));
    });
  });

  // Handle Form Submission
  chatForm.addEventListener('submit', function (e) {
    e.preventDefault();
    const userMessage = chatInput.value.trim();
    if (!userMessage) return;

    // Append User Message Bubble
    appendUserBubble(userMessage);
    chatInput.value = '';
    scrollToBottom();

    // Show Typing Indicator
    if (typingIndicator) typingIndicator.classList.remove('d-none');

    // Call Backend API: POST /api/v1/assistant/message/
    fetch('/api/v1/assistant/message/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || ''
      },
      body: JSON.stringify({ message: userMessage })
    })
      .then(function (res) { return res.json(); })
      .then(function (res) {
        if (typingIndicator) typingIndicator.classList.add('d-none');

        if (res.success && res.data) {
          appendAiResponse(res.data);
        } else {
          appendAiBubble("I apologize, I'm currently unable to process your request. Please try searching or checking our FAQ.");
        }
        scrollToBottom();
      })
      .catch(function (err) {
        if (typingIndicator) typingIndicator.classList.add('d-none');
        appendAiBubble("Sorry, I encountered a temporary connection glitch. Please try again in a moment.");
        scrollToBottom();
      });
  });

  function appendUserBubble(text) {
    const bubble = document.createElement('div');
    bubble.className = 'd-flex justify-content-end';
    bubble.innerHTML = `
      <div class="qc-chat-bubble-user">
        ${escapeHtml(text)}
      </div>
    `;
    messagesContainer.appendChild(bubble);
  }

  function appendAiBubble(htmlText) {
    const bubble = document.createElement('div');
    bubble.className = 'd-flex gap-2 align-items-start';
    bubble.innerHTML = `
      <div class="rounded-circle d-flex align-items-center justify-content-center bg-dark text-white flex-shrink-0" style="width: 28px; height: 28px; font-size: 0.75rem;">
        <i class="bi bi-robot"></i>
      </div>
      <div class="qc-chat-bubble-ai">
        ${htmlText}
      </div>
    `;
    messagesContainer.appendChild(bubble);
  }

  function appendAiResponse(data) {
    const text = data.response || data.reply_text || data.message || '';
    let replyHtml = `<p class="mb-2">${escapeHtml(text)}</p>`;

    // If products were recommended, append product cards
    if (data.suggested_products && data.suggested_products.length > 0) {
      replyHtml += `<div class="d-flex flex-column gap-2 mt-2 pt-2 border-top">`;
      data.suggested_products.slice(0, 3).forEach(function (p) {
        replyHtml += `
          <div class="qc-chat-product-card">
            <img src="${p.image}" alt="${escapeHtml(p.name)}" class="rounded" style="width: 44px; height: 44px; object-fit: cover;">
            <div class="flex-grow-1 overflow-hidden" style="line-height: 1.2;">
              <a href="${p.url}" class="fw-semibold text-truncate d-block small" style="color: var(--text-main);">${escapeHtml(p.name)}</a>
              <span class="fw-bold small" style="color: var(--text-main);">₹${p.price}</span>
              ${p.trust_score ? `<span class="badge bg-dark text-white rounded-pill ms-1" style="font-size: 0.65rem;">${p.trust_score}% Trust</span>` : ''}
            </div>
            <a href="${p.url}" class="btn btn-dark btn-sm py-1 px-2 flex-shrink-0" style="font-size: 0.75rem;">View</a>
          </div>
        `;
      });
      replyHtml += `</div>`;
    }

    appendAiBubble(replyHtml);
  }

  function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function escapeHtml(string) {
    const div = document.createElement('div');
    div.innerText = string;
    return div.innerHTML;
  }

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
});
