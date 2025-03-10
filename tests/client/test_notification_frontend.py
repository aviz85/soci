import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@pytest.mark.client
class TestNotificationFrontend:
    """Test frontend notification functionality with Selenium."""
    
    @pytest.fixture
    def login_user(self, live_server, selenium, create_user):
        """Login a user for selenium tests."""
        selenium.get(f"{live_server.url}/login/")
        
        # Fill in login form
        selenium.find_element(By.ID, "id_username").send_keys(create_user.username)
        selenium.find_element(By.ID, "id_password").send_keys("password")
        selenium.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Wait for redirect to complete
        WebDriverWait(selenium, 10).until(
            EC.url_to_be(f"{live_server.url}/")
        )
        
        return create_user
    
    @pytest.fixture
    def create_test_notification(self, create_user):
        """Create a test notification for the current user."""
        from apps.interactions.models import Notification
        
        return Notification.objects.create(
            recipient=create_user,
            notification_type="like",
            title="New Like",
            message="Sophia liked your post about UI design trends",
            link="/post/106",
            is_read=False
        )
    
    def test_notification_badge_visibility(self, live_server, selenium, login_user, create_test_notification):
        """Test that notification badge appears when there are unread notifications."""
        # Navigate to home page
        selenium.get(f"{live_server.url}/")
        
        # Check if notification badge is visible
        notification_badge = WebDriverWait(selenium, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".notification-badge"))
        )
        
        # Verify badge shows count of 1
        assert notification_badge.text == "1"
    
    def test_notification_toast_appears(self, live_server, selenium, login_user):
        """Test that notification toast appears when a new notification is received."""
        # Navigate to home page
        selenium.get(f"{live_server.url}/")
        
        # Execute JavaScript to simulate a new notification
        selenium.execute_script("""
            if (window.NotificationManager) {
                window.NotificationManager.showToast({
                    title: 'Test Notification',
                    message: 'This is a test notification',
                    type: 'info'
                });
            }
        """)
        
        # Check if toast notification appears
        toast = WebDriverWait(selenium, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".notification-toast"))
        )
        
        # Verify toast content
        assert "Test Notification" in toast.text
        assert "This is a test notification" in toast.text
    
    def test_mark_notification_as_read(self, live_server, selenium, login_user, create_test_notification):
        """Test marking a notification as read."""
        # Navigate to notifications page
        selenium.get(f"{live_server.url}/notifications/")
        
        # Wait for notifications to load
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".notification-item"))
        )
        
        # Get the notification
        notification = selenium.find_element(By.CSS_SELECTOR, ".notification-item")
        
        # Verify it has the unread class
        assert "unread" in notification.get_attribute("class")
        
        # Click the mark as read button
        mark_read_btn = notification.find_element(By.CSS_SELECTOR, ".mark-read-btn")
        mark_read_btn.click()
        
        # Wait for the API call to complete and page to refresh
        time.sleep(1)
        
        # Verify the notification is no longer shown in unread tab
        # Switch to unread tab
        unread_tab = selenium.find_element(By.CSS_SELECTOR, "button[data-tab='unread']")
        unread_tab.click()
        
        # Should show empty state
        WebDriverWait(selenium, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".empty-state"))
        )
        
        # Go back to all tab
        all_tab = selenium.find_element(By.CSS_SELECTOR, "button[data-tab='all']")
        all_tab.click()
        
        # Wait for notifications to load again
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".notification-item"))
        )
        
        # Verify the notification no longer has unread class
        notification = selenium.find_element(By.CSS_SELECTOR, ".notification-item")
        assert "unread" not in notification.get_attribute("class")
    
    def test_mark_all_notifications_as_read(self, live_server, selenium, login_user):
        """Test marking all notifications as read."""
        # Create multiple notifications
        from apps.interactions.models import Notification
        
        for i in range(3):
            Notification.objects.create(
                recipient=login_user,
                notification_type="system",
                title=f"Notification {i}",
                message=f"System message {i}",
                is_read=False
            )
        
        # Navigate to notifications page
        selenium.get(f"{live_server.url}/notifications/")
        
        # Wait for notifications to load
        WebDriverWait(selenium, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".notification-item"))
        )
        
        # Click the mark all as read button
        mark_all_btn = selenium.find_element(By.ID, "mark-all-read")
        mark_all_btn.click()
        
        # Wait for the API call to complete
        time.sleep(1)
        
        # Switch to unread tab
        unread_tab = selenium.find_element(By.CSS_SELECTOR, "button[data-tab='unread']")
        unread_tab.click()
        
        # Should show empty state
        WebDriverWait(selenium, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".empty-state"))
        )
        
        # Check notification badge is no longer visible
        selenium.get(f"{live_server.url}/")
        
        # Wait for page to load
        time.sleep(1)
        
        # Badge should be hidden
        badge = selenium.find_element(By.CSS_SELECTOR, ".notification-badge")
        assert not badge.is_displayed() or "hidden" in badge.get_attribute("class")
    
    def test_notification_links_to_correct_page(self, live_server, selenium, login_user, create_test_notification):
        """Test that clicking a notification navigates to the correct page."""
        # Navigate to notifications page
        selenium.get(f"{live_server.url}/notifications/")
        
        # Wait for notifications to load
        WebDriverWait(selenium, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".notification-item"))
        )
        
        # Get the notification text area (not the action buttons)
        notification_content = selenium.find_element(By.CSS_SELECTOR, ".notification-content")
        
        # Click on the notification
        notification_content.click()
        
        # Wait for navigation
        time.sleep(1)
        
        # Should navigate to the post page
        assert "/post/106" in selenium.current_url 