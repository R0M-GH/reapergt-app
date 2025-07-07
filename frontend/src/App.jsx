import { useAuth } from "react-oidc-context";
import React, { useState, useEffect } from "react";
import { crnService } from "./services/api";
import styles from "./App.module.css";

function Header({ onSettings, showSettings }) {
    return (
        <header className={styles.header}>
            <div className={styles.headerContent}>
                <img src="/logo.png" alt="ReaperGT Logo" className={styles.logo} />
                <span className={styles.title}>ReaperGT</span>
            </div>
            {showSettings && (
                <button
                    onClick={onSettings}
                    className={styles.settingsButton}
                    aria-label="Settings"
                >
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 15C13.6569 15 15 13.6569 15 12C15 10.3431 13.6569 9 12 9C10.3431 9 9 10.3431 9 12C9 13.6569 10.3431 15 12 15Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        <path d="M19.4 15C19.2669 15.3016 19.2272 15.6362 19.286 15.9606C19.3448 16.285 19.4995 16.5843 19.73 16.82L19.79 16.88C19.976 17.0657 20.1235 17.2863 20.2241 17.5291C20.3248 17.7719 20.3766 18.0322 20.3766 18.295C20.3766 18.5578 20.3248 18.8181 20.2241 19.0609C20.1235 19.3037 19.976 19.5243 19.79 19.71C19.6043 19.896 19.3837 20.0435 19.1409 20.1441C18.8981 20.2448 18.6378 20.2966 18.375 20.2966C18.1122 20.2966 17.8519 20.2448 17.6091 20.1441C17.3663 20.0435 17.1457 19.896 16.96 19.71L16.9 19.65C16.6643 19.4195 16.365 19.2648 16.0406 19.206C15.7162 19.1472 15.3816 19.1869 15.08 19.32C14.7842 19.4468 14.532 19.6572 14.3543 19.9255C14.1766 20.1938 14.0813 20.5082 14.08 20.83V21C14.08 21.5304 13.8693 22.0391 13.4942 22.4142C13.1191 22.7893 12.6104 23 12.08 23C11.5496 23 11.0409 22.7893 10.6658 22.4142C10.2907 22.0391 10.08 21.5304 10.08 21V20.91C10.0723 20.579 9.96512 20.2579 9.77251 19.9887C9.5799 19.7195 9.31074 19.5149 9 19.4C8.69838 19.2669 8.36381 19.2272 8.03941 19.286C7.71502 19.3448 7.41568 19.4995 7.18 19.73L7.12 19.79C6.93425 19.976 6.71368 20.1235 6.47088 20.2241C6.22808 20.3248 5.96783 20.3766 5.705 20.3766C5.44217 20.3766 5.18192 20.3248 4.93912 20.2241C4.69632 20.1235 4.47575 19.976 4.29 19.79C4.10405 19.6043 3.95653 19.3837 3.85588 19.1409C3.75523 18.8981 3.70343 18.6378 3.70343 18.375C3.70343 18.1122 3.75523 17.8519 3.85588 17.6091C3.95653 17.3663 4.10405 17.1457 4.29 16.96L4.35 16.9C4.58054 16.6643 4.73519 16.365 4.794 16.0406C4.85282 15.7162 4.81312 15.3816 4.68 15.08C4.55324 14.7842 4.34276 14.532 4.07447 14.3543C3.80618 14.1766 3.49179 14.0813 3.17 14.08H3C2.46957 14.08 1.96086 13.8693 1.58579 13.4942C1.21071 13.1191 1 12.6104 1 12.08C1 11.5496 1.21071 11.0409 1.58579 10.6658C1.96086 10.2907 2.46957 10.08 3 10.08H3.09C3.42099 10.0723 3.74206 9.96512 4.01128 9.77251C4.2805 9.5799 4.48514 9.31074 4.6 9C4.73312 8.69838 4.77282 8.36381 4.714 8.03941C4.65519 7.71502 4.50054 7.41568 4.27 7.18L4.21 7.12C4.02405 6.93425 3.87653 6.71368 3.77588 6.47088C3.67523 6.22808 3.62343 5.96783 3.62343 5.705C3.62343 5.44217 3.67523 5.18192 3.77588 4.93912C3.87653 4.69632 4.02405 4.47575 4.21 4.29C4.39575 4.10405 4.61632 3.95653 4.85912 3.85588C5.10192 3.75523 5.36217 3.70343 5.625 3.70343C5.88783 3.70343 6.14808 3.75523 6.39088 3.85588C6.63368 3.95653 6.85425 4.10405 7.04 4.29L7.1 4.35C7.33568 4.58054 7.63502 4.73519 7.95941 4.794C8.28381 4.85282 8.61838 4.81312 8.92 4.68H9C9.29577 4.55324 9.54802 4.34276 9.72569 4.07447C9.90337 3.80618 9.99872 3.49179 10 3.17V3C10 2.46957 10.2107 1.96086 10.5858 1.58579C10.9609 1.21071 11.4696 1 12 1C12.5304 1 13.0391 1.21071 13.4142 1.58579C13.7893 1.96086 14 2.46957 14 3V3.09C14.0013 3.41179 14.0966 3.72618 14.2743 3.99447C14.452 4.26276 14.7042 4.47324 15 4.6C15.3016 4.73312 15.6362 4.77282 15.9606 4.714C16.285 4.65519 16.5843 4.50054 16.82 4.27L16.88 4.21C17.0657 4.02405 17.2863 3.87653 17.5291 3.77588C17.7719 3.67523 18.0322 3.62343 18.295 3.62343C18.5578 3.62343 18.8181 3.67523 19.0609 3.77588C19.3037 3.87653 19.5243 4.02405 19.71 4.21C19.896 4.39575 20.0435 4.61632 20.1441 4.85912C20.2448 5.10192 20.2966 5.36217 20.2966 5.625C20.2966 5.88783 20.2448 6.14808 20.1441 6.39088C20.0435 6.63368 19.896 6.85425 19.71 7.04L19.65 7.1C19.4195 7.33568 19.2648 7.63502 19.206 7.95941C19.1472 8.28381 19.1869 8.61838 19.32 8.92V9C19.4468 9.29577 19.6572 9.54802 19.9255 9.72569C20.1938 9.90337 20.5082 9.99872 20.83 10H21C21.5304 10 22.0391 10.2107 22.4142 10.5858C22.7893 10.9609 23 11.4696 23 12C23 12.5304 22.7893 13.0391 22.4142 13.4142C22.0391 13.7893 21.5304 14 21 14H20.91C20.5882 14.0013 20.2738 14.0966 20.0055 14.2743C19.7372 14.452 19.5268 14.7042 19.4 15Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                </button>
            )}
        </header>
    );
}

function SettingsModal({ open, onClose, onSignOut, notificationPermission, notificationSubscription, onToggleNotifications }) {
    if (!open) return null;
    return (
        <div className={styles.modalOverlay}>
            <div className={styles.modalContent}>
                <div className={styles.modalHeader}>
                    <h2 className={styles.modalTitle}>Settings</h2>
                    <button
                        onClick={onClose}
                        className={styles.modalCloseButton}
                        aria-label="Close settings"
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </button>
                </div>

                <div className={styles.modalBody}>
                    <div className={styles.settingSection}>
                        <h3 className={styles.settingTitle}>Notifications</h3>
                        <p className={styles.settingDescription}>
                            Get notified when courses you're tracking become available.
                        </p>
                        <div className={styles.notificationToggle}>
                            {notificationPermission === 'granted' && notificationSubscription ? (
                                <button
                                    onClick={onToggleNotifications}
                                    className={styles.notificationButton}
                                >
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M18 8A6 6 0 0 0 6 8C6 15 3 17 3 17H21C21 17 18 15 18 8Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                        <path d="M13.73 21A2 2 0 0 1 10.27 21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                    Disable Notifications
                                </button>
                            ) : (
                                <button
                                    onClick={onToggleNotifications}
                                    className={styles.notificationButton}
                                    disabled={notificationPermission === 'denied'}
                                >
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M18 8A6 6 0 0 0 6 8C6 15 3 17 3 17H21C21 17 18 15 18 8Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                        <path d="M13.73 21A2 2 0 0 1 10.27 21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                    {notificationPermission === 'denied' ? 'Notifications Blocked' : 'Enable Notifications'}
                                </button>
                            )}
                        </div>
                    </div>

                    <div className={styles.settingSection}>
                        <h3 className={styles.settingTitle}>Account</h3>
                        <p className={styles.settingDescription}>Manage your account settings and preferences.</p>
                    </div>

                    <div className={styles.modalActions}>
                        <button
                            onClick={onSignOut}
                            className={styles.signOutButton}
                        >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M9 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                <path d="M16 17L21 12L16 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                <path d="M21 12H9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                            Sign out
                        </button>

                        <button
                            onClick={onClose}
                            className={styles.cancelButton}
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

function Message({ message, type, onClose }) {
    if (!message) return null;

    const borderColor = type === 'success' ? '#4CAF50' : '#f44336';
    const textColor = type === 'success' ? '#4CAF50' : '#f44336';

    return (
        <div style={{
            position: 'fixed',
            bottom: '24px',
            left: '50%',
            transform: 'translateX(-50%)',
            color: textColor,
            fontSize: '13px',
            fontWeight: 500,
            padding: '8px 16px',
            border: `1px solid ${borderColor}`,
            borderRadius: '8px',
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            zIndex: 1000,
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
        }}>
            <span>{message}</span>
            <button
                onClick={onClose}
                style={{
                    background: 'none',
                    border: 'none',
                    color: textColor,
                    cursor: 'pointer',
                    fontSize: 14,
                    padding: 0,
                    display: 'flex',
                    alignItems: 'center',
                    marginLeft: '4px'
                }}
            >
                ×
            </button>
        </div>
    );
}

function App() {
    const auth = useAuth();
    const [settingsOpen, setSettingsOpen] = useState(false);
    const [crn, setCrn] = useState('');
    const [crns, setCrns] = useState([]);
    const [loading, setLoading] = useState(false);
    const [adding, setAdding] = useState(false);
    const [removing, setRemoving] = useState({});
    const [message, setMessage] = useState(null);
    const [messageType, setMessageType] = useState('success');
    const [showInstallPrompt, setShowInstallPrompt] = useState(false);
    const [deferredPrompt, setDeferredPrompt] = useState(null);
    const [notificationPermission, setNotificationPermission] = useState('default');
    const [notificationSubscription, setNotificationSubscription] = useState(null);

    // PWA Install Prompt
    useEffect(() => {
        const handler = (e) => {
            e.preventDefault();
            setDeferredPrompt(e);
            setShowInstallPrompt(true);
        };

        window.addEventListener('beforeinstallprompt', handler);
        return () => window.removeEventListener('beforeinstallprompt', handler);
    }, []);

    const handleInstallClick = async () => {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            if (outcome === 'accepted') {
                setShowInstallPrompt(false);
                setDeferredPrompt(null);
            }
        }
    };

    const dismissInstallPrompt = () => {
        setShowInstallPrompt(false);
        setDeferredPrompt(null);
    };

    // Service Worker Registration
    useEffect(() => {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then((registration) => {
                    console.log('Service Worker registered successfully:', registration);
                })
                .catch((error) => {
                    console.error('Service Worker registration failed:', error);
                });
        }
    }, []);

    // Notification Setup
    useEffect(() => {
        if ('serviceWorker' in navigator && 'PushManager' in window) {
            checkNotificationPermission();
        }
    }, []);

    const checkNotificationPermission = () => {
        if ('Notification' in window) {
            setNotificationPermission(Notification.permission);
        }
    };

    const requestNotificationPermission = async () => {
        if (!('Notification' in window)) {
            showMessage('Notifications are not supported in this browser', 'error');
            return;
        }

        try {
            const permission = await Notification.requestPermission();
            setNotificationPermission(permission);

            if (permission === 'granted') {
                await subscribeToNotifications();
                showMessage('Notifications enabled!', 'success');
            } else if (permission === 'denied') {
                showMessage('Notifications blocked. Please enable them in your browser settings.', 'error');
            }
        } catch (error) {
            console.error('Error requesting notification permission:', error);
            showMessage('Failed to enable notifications', 'error');
        }
    };

    const subscribeToNotifications = async () => {
        try {
            const registration = await navigator.serviceWorker.ready;

            // Check if already subscribed
            const existingSubscription = await registration.pushManager.getSubscription();
            if (existingSubscription) {
                setNotificationSubscription(existingSubscription);
                return;
            }

            // Create new subscription
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: urlBase64ToUint8Array('YOUR_VAPID_PUBLIC_KEY') // You'll need to replace this with your actual VAPID key
            });

            setNotificationSubscription(subscription);

            // Send subscription to your backend
            // await sendSubscriptionToServer(subscription);

        } catch (error) {
            console.error('Error subscribing to notifications:', error);
            showMessage('Failed to subscribe to notifications', 'error');
        }
    };

    const unsubscribeFromNotifications = async () => {
        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();

            if (subscription) {
                await subscription.unsubscribe();
                setNotificationSubscription(null);
                showMessage('Notifications disabled', 'success');
            }
        } catch (error) {
            console.error('Error unsubscribing from notifications:', error);
            showMessage('Failed to disable notifications', 'error');
        }
    };

    // Utility function to convert VAPID key
    const urlBase64ToUint8Array = (base64String) => {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    };

    // Load CRNs when authenticated
    useEffect(() => {
        if (auth.isAuthenticated) {
            loadCRNs();
        }
    }, [auth.isAuthenticated]);

    const loadCRNs = async () => {
        setLoading(true);
        try {
            const crnList = await crnService.getCRNs();
            setCrns(crnList);
        } catch (error) {
            showMessage('Failed to load CRNs', 'error');
        } finally {
            setLoading(false);
        }
    };

    const addCRN = async () => {
        if (!crn.trim()) return;

        setAdding(true);
        try {
            const newCRN = await crnService.addCRN(crn.trim());
            setCrns(prev => [...prev, newCRN]);
            setCrn('');
            showMessage(`CRN ${crn.trim()} added successfully!`, 'success');
        } catch (error) {
            const errorMsg = error.response?.data?.error || 'Failed to add CRN';
            showMessage(errorMsg, 'error');
        } finally {
            setAdding(false);
        }
    };

    const removeCRN = async (crnToRemove) => {
        setRemoving(prev => ({ ...prev, [crnToRemove]: true }));
        try {
            await crnService.removeCRN(crnToRemove);
            setCrns(prev => prev.filter(c => c.crn !== crnToRemove));
            showMessage(`CRN ${crnToRemove} removed successfully!`, 'success');
        } catch (error) {
            const errorMsg = error.response?.data?.error || 'Failed to remove CRN';
            showMessage(errorMsg, 'error');
        } finally {
            setRemoving(prev => ({ ...prev, [crnToRemove]: false }));
        }
    };

    const showMessage = (msg, type = 'success') => {
        setMessage(msg);
        setMessageType(type);
        setTimeout(() => setMessage(null), 5000);
    };

    const copyToClipboard = async (text) => {
        try {
            await navigator.clipboard.writeText(text);
            showMessage(`CRN ${text} copied to clipboard!`, 'success');
        } catch (error) {
            showMessage('Failed to copy CRN', 'error');
        }
    };

    const triggerCelebration = (element) => {
        // Add celebration class for animation
        element.classList.add(styles.celebrate);
        setTimeout(() => {
            element.classList.remove(styles.celebrate);
        }, 600);
    };

    const handleCheckClick = (crnData, event) => {
        if (crnData.isOpen) {
            triggerCelebration(event.currentTarget);
            showMessage(`🎉 enjoy ${crnData.course_name}!`, 'success');
        }
        // Always remove the CRN from tracking
        removeCRN(crnData.crn);
    };

    const handleSignOut = () => {
        auth.removeUser();
        // Use a more explicit sign out approach
        const logoutUrl = `https://reapergt.auth.us-east-1.amazoncognito.com/logout?client_id=ghq72js41cdk53vcren6v436e&logout_uri=https://app.getreaper.com/`;
        window.location.href = logoutUrl;
    };

    if (auth.isLoading) {
        return (
            <div className={styles.gradientContainer}>
                <div className={styles.container}>
                    <Header />
                    <div style={{ color: '#ECECEC', textAlign: 'center', marginTop: 80, fontSize: 24 }}>Loading...</div>
                </div>
            </div>
        );
    }

    if (auth.error) {
        return (
            <div className={styles.gradientContainer}>
                <div className={styles.container}>
                    <Header />
                    <div style={{ color: '#ff5555', textAlign: 'center', marginTop: 80, fontSize: 20 }}>Encountering error... {auth.error.message}</div>
                </div>
            </div>
        );
    }

    if (auth.isAuthenticated) {
        return (
            <div className={styles.gradientContainer}>
                <div className={styles.container}>
                    <Header onSettings={() => setSettingsOpen(true)} showSettings={true} />
                    <SettingsModal
                        open={settingsOpen}
                        onClose={() => setSettingsOpen(false)}
                        onSignOut={handleSignOut}
                        notificationPermission={notificationPermission}
                        notificationSubscription={notificationSubscription}
                        onToggleNotifications={notificationSubscription ? unsubscribeFromNotifications : requestNotificationPermission}
                    />
                    {/* PWA Install Prompt */}
                    {showInstallPrompt && (
                        <div className={styles.installPrompt}>
                            <div className={styles.installContent}>
                                <span>📱 Install ReaperGT for a better experience</span>
                                <div className={styles.installActions}>
                                    <button onClick={handleInstallClick} className={styles.installButton}>
                                        Install
                                    </button>
                                    <button onClick={dismissInstallPrompt} className={styles.dismissButton}>
                                        Not now
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                    <div className={styles.inputContainer}>
                        <input
                            type="text"
                            value={crn}
                            onChange={(e) => setCrn(e.target.value)}
                            placeholder="Enter CRN (5 digits)"
                            maxLength={5}
                            pattern="[0-9]{5}"
                            disabled={adding}
                            className={styles.input}
                            onKeyPress={(e) => {
                                if (e.key === 'Enter') {
                                    addCRN();
                                }
                            }}
                        />
                        <button
                            onClick={addCRN}
                            disabled={!crn.trim() || adding}
                            className={styles.subscribeButton}
                        >
                            <span className={styles.subscribeText}>{adding ? 'Adding...' : 'Add CRN'}</span>
                        </button>
                        <Message message={message} type={messageType} onClose={() => setMessage(null)} />
                    </div>
                    <div className={styles.listContainer}>
                        {loading ? (
                            <div style={{ color: '#ECECEC', textAlign: 'center', padding: 40 }}>Loading your CRNs...</div>
                        ) : crns.length === 0 ? (
                            <div className={styles.emptyContainer}>
                                <div className={styles.emptyText}>No CRNs tracked yet</div>
                            </div>
                        ) : (
                            // Sort CRNs: open courses first, then closed courses
                            crns
                                .sort((a, b) => {
                                    // First sort by open status (open courses first)
                                    if (a.isOpen && !b.isOpen) return -1;
                                    if (!a.isOpen && b.isOpen) return 1;
                                    // Then sort alphabetically by course name
                                    return (a.course_name || '').localeCompare(b.course_name || '');
                                })
                                .map((crnData) => (
                                    <div
                                        key={crnData.crn}
                                        className={
                                            `${styles.crnCard} ${crnData.isOpen ? styles.openCard : ''}`
                                        }
                                    >
                                        <div className={styles.crnInfo}>
                                            <div className={styles.crnText}>{crnData.course_id || 'Loading...'} - {crnData.course_name || 'Loading...'}</div>
                                            <div className={styles.courseDetails}>
                                                <span className={styles.detailBox}>Section: {crnData.course_section || 'Loading...'}</span>
                                                <span className={styles.detailBox}>CRN: {crnData.crn}</span>
                                            </div>
                                        </div>
                                        <div className={styles.actionButtons}>
                                            <button
                                                onClick={() => copyToClipboard(crnData.crn)}
                                                className={styles.copyButton}
                                                title="Copy CRN to clipboard"
                                            >
                                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                    <path d="M8 4V16C8 17.1046 8.89543 18 10 18H18C19.1046 18 20 17.1046 20 16V7.24264C20 6.97742 19.8946 6.7228 19.7071 6.53553L16.4645 3.29289C16.2772 3.10536 16.0226 3 15.7574 3H10C8.89543 3 8 3.89543 8 5Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                                    <path d="M16 18V20C16 21.1046 15.1046 22 14 22H6C4.89543 22 4 21.1046 4 20V8C4 6.89543 4.89543 6 6 6H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                                </svg>
                                            </button>
                                            <button
                                                onClick={(e) => crnData.isOpen ? handleCheckClick(crnData, e) : removeCRN(crnData.crn)}
                                                disabled={removing[crnData.crn]}
                                                className={`${styles.actionButton} ${crnData.isOpen ? styles.checkButton : styles.trashButton}`}
                                                title={crnData.isOpen ? "Course is open!" : "Remove CRN"}
                                            >
                                                {removing[crnData.crn] ? (
                                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                        <path d="M12 2V6M12 18V22M4.93 4.93L7.76 7.76M16.24 16.24L19.07 19.07M2 12H6M18 12H22M4.93 19.07L7.76 16.24M16.24 7.76L19.07 4.93" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                                    </svg>
                                                ) : crnData.isOpen ? (
                                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                        <path d="M20 6L9 17L4 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                                    </svg>
                                                ) : (
                                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                        <path d="M3 6H5H21M8 6V4C8 3.46957 8.21071 2.96086 8.58579 2.58579C8.96086 2.21071 9.46957 2 10 2H14C14.5304 2 15.0391 2.21071 15.4142 2.58579C15.7893 2.96086 16 3.46957 16 4V6M19 6V20C19 20.5304 18.7893 21.0391 18.4142 21.4142C18.0391 21.7893 17.5304 22 17 22H7C6.46957 22 5.96086 21.7893 5.58579 21.4142C5.21071 21.0391 5 20.5304 5 20V6H19Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                                    </svg>
                                                )}
                                            </button>
                                        </div>
                                    </div>
                                ))
                        )}
                    </div>

                    {/* Oscar Button */}
                    <a
                        href="https://registration.banner.gatech.edu/StudentRegistrationSsb/ssb/registration/registration"
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.oscarBottomButton}
                    >
                        <span>OSCAR</span>
                    </a>
                </div>
            </div>
        );
    }

    // Not authenticated
    return (
        <div className={styles.gradientContainer}>
            <div className={styles.container}>
                <Header />
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
                    <button
                        onClick={() => auth.signinRedirect()}
                        className={styles.subscribeButton}
                        style={{ marginTop: 48 }}
                    >
                        <span className={styles.subscribeText}>Sign in</span>
                    </button>
                </div>
            </div>
        </div>
    );
}

export default App;
