// SOS Handler Utility - Include this in all pages with SOS button
// This file contains the updated SOS sending functionality

/**
 * Send SOS request with full user information and geolocation
 * @param {Element} sosButton - The button element (optional)
 */
function sendSOSRequest(sosButton) {
  // Get user information
  const userID = sessionStorage.getItem('user_id');
  const userName = sessionStorage.getItem('user_name');
  const userEmail = sessionStorage.getItem('user_email');
  const userRole = sessionStorage.getItem('user_role');
  const userPhone = sessionStorage.getItem('user_phone');
  const userClass = sessionStorage.getItem('user_class');

  // Validate login
  if (!userID || !userEmail) {
    alert('Bạn phải đăng nhập trước khi gửi SOS!');
    window.location.href = 'login.html';
    return;
  }

  // Check if user is valid (not placeholder values)
  if (userID === 'Unknown' || userEmail === 'unknown@email.com') {
    alert('Thông tin đăng nhập không hợp lệ. Vui lòng đăng nhập lại.');
    sessionStorage.clear();
    window.location.href = 'login.html';
    return;
  }

  if (!confirm('Bạn chắc chắn muốn gửi tín hiệu SOS?')) {
    return;
  }

  const buttonElement = sosButton || document.getElementById('sos-button');
  const originalLabel = buttonElement ? buttonElement.innerHTML : '<i class="fas fa-exclamation-triangle"></i> SOS Khẩn Cấp';
  
  if (buttonElement) {
    buttonElement.disabled = true;
    buttonElement.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Đang gửi...';
  }

  // Get current location
  let location = 'Không xác định';
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        location = `Vĩ độ: ${position.coords.latitude}, Kinh độ: ${position.coords.longitude}`;
        sendSOSToServer(userID, userName, userEmail, userPhone, userClass, location, userRole, buttonElement, originalLabel);
      },
      (error) => {
        console.log('Geolocation error:', error);
        sendSOSToServer(userID, userName, userEmail, userPhone, userClass, location, userRole, buttonElement, originalLabel);
      }
    );
  } else {
    sendSOSToServer(userID, userName, userEmail, userPhone, userClass, location, userRole, buttonElement, originalLabel);
  }
}

/**
 * Send SOS to backend server
 */
function sendSOSToServer(userID, userName, userEmail, userPhone, userClass, location, userRole, buttonElement, originalLabel) {
  // Determine user type label
  let userTypeLabel = 'Học sinh';
  if (userRole === 'GV') userTypeLabel = 'Giáo viên';
  else if (userRole === 'PH') userTypeLabel = 'Phụ huynh';

  const payload = {
    student_id: userID,
    student_name: userName || 'N/A',
    student_email: userEmail,
    student_phone: userPhone || '',
    student_class: userClass || '',
    location: location,
    message: `Báo cáo khẩn từ ${userTypeLabel}`
  };

  console.log('Sending SOS:', payload);

  fetch('/api/sos/send', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  })
    .then(res => {
      console.log('Response status:', res.status);
      if (!res.ok) {
        return res.json().then(data => {
          throw new Error(data.error || `HTTP ${res.status}: ${res.statusText}`);
        }).catch(() => {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        });
      }
      return res.json();
    })
    .then(data => {
      console.log('SOS response:', data);
      if (data.success) {
        alert('Tín hiệu SOS đã được gửi thành công! Vui lòng chờ hỗ trợ từ quản trị viên.');
      } else {
        alert('Lỗi khi gửi SOS: ' + (data.error || 'Unknown error'));
      }
    })
    .catch(error => {
      console.error('SOS Error:', error);
      alert('Lỗi khi gửi SOS: ' + error.message);
    })
    .finally(() => {
      if (buttonElement) {
        buttonElement.disabled = false;
        buttonElement.innerHTML = originalLabel;
      }
    });
}

/**
 * Setup SOS button click handler
 */
function setupSOSButton() {
  const sosButton = document.getElementById('sos-button');
  if (!sosButton) return;
  sosButton.addEventListener('click', function() {
    sendSOSRequest(sosButton);
  });
}

/**
 * Trigger SOS from sidebar (for onclick handlers)
 */
function triggerSOS() {
  // For pages with sos-button element
  if (document.getElementById('sos-button')) {
    document.getElementById('sos-button').click();
  } else {
    // Direct SOS request for pages without sos-button
    sendSOSRequest();
  }
  
  // Close sidebar if open
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (sidebar) sidebar.classList.remove('active');
  if (overlay) overlay.classList.remove('active');
}
