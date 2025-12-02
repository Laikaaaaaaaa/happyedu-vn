// SOS Notification System - Include this in all admin pages
// This file handles real-time SOS popup notifications for admin users

let lastCheckedSosId = null;
let currentSosModalOpen = false;
let sosCheckInterval = null;
let sosAlertSoundInterval = null;
let sosVibrationInterval = null;

/**
 * Play alert sound once
 */
function playSosAlertSoundOnce() {
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = 800;
    oscillator.type = 'sine';
    
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
    
    setTimeout(() => {
      try {
        const osc2 = audioContext.createOscillator();
        const gain2 = audioContext.createGain();
        osc2.connect(gain2);
        gain2.connect(audioContext.destination);
        
        osc2.frequency.value = 1000;
        osc2.type = 'sine';
        
        gain2.gain.setValueAtTime(0.3, audioContext.currentTime);
        gain2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        osc2.start(audioContext.currentTime);
        osc2.stop(audioContext.currentTime + 0.5);
      } catch(e) {}
    }, 600);
  } catch(e) {
    console.log('Audio context not available:', e);
  }
}

/**
 * Play alert sound continuously while modal is open
 */
function startContinuousSosAlert() {
  if (sosAlertSoundInterval) {
    clearInterval(sosAlertSoundInterval);
  }
  
  // Play sound immediately
  playSosAlertSoundOnce();
  
  // Then repeat every 2 seconds while modal is open
  sosAlertSoundInterval = setInterval(() => {
    if (currentSosModalOpen) {
      playSosAlertSoundOnce();
    } else {
      clearInterval(sosAlertSoundInterval);
      sosAlertSoundInterval = null;
    }
  }, 2000);
}

/**
 * Stop continuous alert sound
 */
function stopContinuousSosAlert() {
  if (sosAlertSoundInterval) {
    clearInterval(sosAlertSoundInterval);
    sosAlertSoundInterval = null;
  }
}

/**
 * Trigger device vibration continuously on mobile
 */
function startContinuousVibration() {
  if (sosVibrationInterval) {
    clearInterval(sosVibrationInterval);
  }
  
  if (navigator.vibrate) {
    // Vibrate immediately
    navigator.vibrate([300, 100, 300, 100, 300]);
    
    // Then repeat every 1 second while modal is open
    sosVibrationInterval = setInterval(() => {
      if (currentSosModalOpen && navigator.vibrate) {
        navigator.vibrate([300, 100, 300, 100, 300]);
      } else if (sosVibrationInterval) {
        clearInterval(sosVibrationInterval);
        sosVibrationInterval = null;
      }
    }, 1000);
  }
}

/**
 * Stop continuous vibration
 */
function stopContinuousVibration() {
  if (sosVibrationInterval) {
    clearInterval(sosVibrationInterval);
    sosVibrationInterval = null;
  }
}

/**
 * Check for new unresolved SOS reports
 * Shows popup notification if new SOS found
 */
function checkForNewSosReports() {
  const userRole = sessionStorage.getItem('user_role');
  
  if (userRole !== 'AD') {
    console.log('Not admin, skipping SOS check');
    return;
  }
  
  if (currentSosModalOpen) {
    console.log('Modal already open, skipping check');
    return;
  }

  console.log('Checking for SOS reports...');
  
  fetch('/api/sos/reports')
    .then(response => {
      console.log('SOS API Response status:', response.status);
      return response.json();
    })
    .then(data => {
      console.log('SOS API Response data:', data);
      
      if (data.success && data.data && data.data.length > 0) {
        console.log('Total SOS reports:', data.data.length);
        
        // Get all unresolved SOS reports
        const unresolvedSOSList = data.data.filter(sos => !sos.resolved);
        console.log('Unresolved SOS count:', unresolvedSOSList.length);
        
        if (unresolvedSOSList.length > 0) {
          // Get list of ignored SOS IDs
          const ignoredSosIds = JSON.parse(sessionStorage.getItem('ignoredSosIds') || '[]');
          console.log('Ignored SOS IDs:', ignoredSosIds);
          
          // Filter out ignored SOS
          const notIgnoredSOS = unresolvedSOSList.filter(sos => !ignoredSosIds.includes(sos.id));
          console.log('Not ignored SOS count:', notIgnoredSOS.length);
          
          if (notIgnoredSOS.length > 0) {
            // Get the most recent unresolved and not-ignored SOS
            const latestSOS = notIgnoredSOS[0];
            console.log('Latest unresolved SOS:', latestSOS.id);
            
            // Get the ID of the last shown SOS from sessionStorage
            const lastShownSosId = sessionStorage.getItem('lastShownSosId');
            console.log('Last shown SOS ID:', lastShownSosId);
            
            // If this is a new SOS or we haven't shown any modal yet, show it
            if (!lastShownSosId || latestSOS.id !== lastShownSosId) {
              console.log('New SOS detected - showing modal:', latestSOS.id);
              showSosNotificationPopup(latestSOS);
              // Save this SOS ID so we don't show it again unless page reloads
              sessionStorage.setItem('lastShownSosId', latestSOS.id);
            } else {
              console.log('SOS already shown, skipping');
            }
          } else {
            console.log('All unresolved SOS are ignored');
          }
        } else {
          console.log('No unresolved SOS found');
        }
      } else {
        console.log('No SOS data or API failed:', data);
      }
    })
    .catch(error => {
      console.error('Error checking SOS reports:', error);
    });
}

/**
 * Display SOS notification popup with emergency styling
 */
function showSosNotificationPopup(sosData) {
  console.log('Showing SOS modal for:', sosData.id);
  
  currentSosModalOpen = true;
  
  // Start continuous alert sound and vibration
  startContinuousSosAlert();
  startContinuousVibration();
  
  // Create modal overlay with emergency styling
  const overlay = document.createElement('div');
  overlay.id = 'sos-notification-overlay';
  overlay.style.cssText = `
    display: flex;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.85);
    z-index: 99999;
    align-items: center;
    justify-content: center;
  `;

  // Create modal container with emergency red theme
  const modal = document.createElement('div');
  modal.style.cssText = `
    background: white;
    border-radius: 16px;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
    max-width: 500px;
    width: calc(100% - 32px);
    margin: 16px;
    animation: sosRadar 2s infinite;
    position: relative;
  `;

  // Add CSS animations
  if (!document.getElementById('sos-styles')) {
    const style = document.createElement('style');
    style.id = 'sos-styles';
    style.textContent = `
      @keyframes sosRadar {
        0%, 100% { 
          transform: scale(1);
          box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.7), 0 25px 50px rgba(0, 0, 0, 0.3);
        }
        50% { 
          transform: scale(1.02);
          box-shadow: 0 0 0 15px rgba(220, 38, 38, 0), 0 25px 50px rgba(0, 0, 0, 0.3);
        }
      }
      @keyframes sosPulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
      }
      .sos-pulse {
        animation: sosPulse 0.6s infinite;
      }
    `;
    document.head.appendChild(style);
  }

  const timestamp = new Date(sosData.timestamp).toLocaleString('vi-VN');

  modal.innerHTML = `
    <div style="background: linear-gradient(135deg, #DC2626 0%, #991B1B 100%); padding: 24px; border-radius: 16px 16px 0 0; border-bottom: 4px solid #7F1D1D;">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
        <div style="display: flex; align-items: center; gap: 12px;">
          <div style="width: 20px; height: 20px; background: #FCA5A5; border-radius: 50%; font-size: 18px; display: flex; align-items: center; justify-content: center;" class="sos-pulse">🔴</div>
          <h3 style="font-size: 1.5rem; font-weight: 800; color: white; margin: 0;">🚨 SOS KHẨN CẤP</h3>
        </div>
      </div>
      <p style="color: #FEE2E2; margin: 0; font-size: 14px;">⚠️ Có yêu cầu hỗ trợ khẩn cấp từ người dùng</p>
    </div>

    <div style="padding: 24px; background: white;">
      <div style="border-left: 4px solid #DC2626; padding-left: 16px; margin-bottom: 20px;">
        <p style="color: #7F1D1D; font-size: 12px; margin: 0; font-weight: 600;">NGƯỜI GỬI</p>
        <p style="font-size: 20px; font-weight: 700; color: #DC2626; margin: 8px 0 0 0;">${sosData.student_name}</p>
      </div>

      <div style="background: #FEF2F2; border-radius: 12px; padding: 16px; margin-bottom: 20px; font-size: 14px; line-height: 1.8; color: #5F2120;">
        <p style="margin: 0 0 10px 0;"><strong style="color: #991B1B;">📧 Email:</strong> ${sosData.student_email}</p>
        <p style="margin: 0 0 10px 0;"><strong style="color: #991B1B;">📱 Điện thoại:</strong> ${sosData.student_phone || '—'}</p>
        <p style="margin: 0 0 10px 0;"><strong style="color: #991B1B;">🎓 Lớp:</strong> ${sosData.student_class || '—'}</p>
        <p style="margin: 0 0 10px 0;"><strong style="color: #991B1B;">📍 Vị trí:</strong> ${sosData.location || 'Không xác định'}</p>
        <p style="margin: 0 0 10px 0;"><strong style="color: #991B1B;">🕐 Thời gian:</strong> ${timestamp}</p>
        ${sosData.message ? `<p style="margin: 10px 0 0 0; padding-top: 10px; border-top: 1px solid #FECACA;"><strong style="color: #991B1B;">💬 Lời nhắn:</strong> ${sosData.message}</p>` : ''}
      </div>

      <div style="display: flex; gap: 12px;">
        <button onclick="closeSosModal()" style="flex: 1; padding: 14px 16px; background: #E5E7EB; color: #1F2937; border: none; border-radius: 8px; font-weight: 600; font-size: 14px; cursor: pointer; transition: all 0.2s; font-size: 15px;">
          Bỏ qua
        </button>
        <button onclick="goToSosReports()" style="flex: 1; padding: 14px 16px; background: #DC2626; color: white; border: none; border-radius: 8px; font-weight: 600; font-size: 15px; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 8px;">
          👁️ Xem xét
        </button>
      </div>
    </div>
  `;

  overlay.appendChild(modal);
  document.body.appendChild(overlay);

  // Click outside to close
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      closeSosModal();
    }
  });

  // ESC key to close
  const escHandler = (e) => {
    if (e.key === 'Escape') {
      closeSosModal();
      document.removeEventListener('keydown', escHandler);
    }
  };
  document.addEventListener('keydown', escHandler);

  // Auto-close after 60 seconds if not interacted
  setTimeout(() => {
    const element = document.getElementById('sos-notification-overlay');
    if (element) {
      closeSosModal();
    }
  }, 60000);
}

/**
 * Close SOS modal
 */
function closeSosModal() {
  const overlay = document.getElementById('sos-notification-overlay');
  if (overlay) {
    overlay.remove();
  }
  currentSosModalOpen = false;
  
  // Stop continuous alert sound and vibration
  stopContinuousSosAlert();
  stopContinuousVibration();
  
  // Mark all unresolved SOS as "ignored" so they won't show again in this session
  fetch('/api/sos/reports')
    .then(r => r.json())
    .then(data => {
      if (data.success && data.data) {
        data.data.forEach(sos => {
          if (!sos.resolved) {
            const ignoredList = JSON.parse(sessionStorage.getItem('ignoredSosIds') || '[]');
            if (!ignoredList.includes(sos.id)) {
              ignoredList.push(sos.id);
              sessionStorage.setItem('ignoredSosIds', JSON.stringify(ignoredList));
            }
          }
        });
      }
    })
    .catch(e => console.log('Error updating ignored SOS:', e));
}

/**
 * Navigate to SOS reports page and close the notification
 */
function goToSosReports() {
  closeSosModal();
  window.location.href = 'admin_sos_reports.html';
}

/**
 * Start monitoring for new SOS reports
 */
function initSosNotificationMonitoring() {
  const userRole = sessionStorage.getItem('user_role');
  
  if (userRole === 'AD') {
    console.log('Initializing SOS monitoring for admin');
    
    // Check immediately
    checkForNewSosReports();
    
    // Clear existing interval if any
    if (sosCheckInterval) clearInterval(sosCheckInterval);
    
    // Check every 1 second for new SOS reports
    sosCheckInterval = setInterval(() => {
      checkForNewSosReports();
    }, 1000);
  }
}

/**
 * Clean up when leaving page
 */
function cleanupSosMonitoring() {
  if (sosCheckInterval) {
    clearInterval(sosCheckInterval);
    sosCheckInterval = null;
  }
}

// Initialize on page load - RUN IMMEDIATELY
console.log('SOS Notification Script Loaded');
const userRole = sessionStorage.getItem('user_role');
console.log('User role:', userRole);

if (userRole === 'AD') {
  console.log('Admin detected - initializing SOS monitoring immediately');
  initSosNotificationMonitoring();
}

// Also initialize on DOMContentLoaded as backup
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOMContentLoaded - initializing SOS monitoring');
  initSosNotificationMonitoring();
});

// Cleanup on page unload
window.addEventListener('beforeunload', cleanupSosMonitoring);

