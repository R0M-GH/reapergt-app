import { useState, useEffect } from 'react';

const GOOGLE_CLIENT_ID = '622283455287-8so6inc3t57nroj191930h9oldr4t2rh.apps.googleusercontent.com';

export const useGoogleAuth = () => {
    const [isLoading, setIsLoading] = useState(true);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState(null);
    const [error, setError] = useState(null);
    const [accessToken, setAccessToken] = useState(null);

    useEffect(() => {
        // Load Google Identity Services
        const loadGoogleScript = () => {
            if (window.google && window.google.accounts) {
                initializeGoogleAuth();
                return;
            }

            // Check if script is already being loaded
            const existingScript = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
            if (existingScript) {
                console.log('Google script already exists, waiting for it to load...');
                existingScript.onload = () => {
                    setTimeout(initializeGoogleAuth, 500);
                };
                return;
            }

            const script = document.createElement('script');
            script.src = 'https://accounts.google.com/gsi/client';
            script.async = true;
            script.defer = true;
            script.onload = () => {
                // Add a small delay to ensure Google object is fully loaded
                setTimeout(initializeGoogleAuth, 500);
            };
            script.onerror = (error) => {
                console.error('Failed to load Google Identity Services script:', error);
                setError(new Error('Failed to load Google authentication'));
                setIsLoading(false);
            };
            document.head.appendChild(script);
        };

        const initializeGoogleAuth = () => {
            try {
                console.log('Initializing Google Auth...');

                // Double-check that Google object is available
                if (!window.google || !window.google.accounts || !window.google.accounts.id) {
                    console.error('Google Identity Services not fully loaded');
                    setError(new Error('Google authentication not available'));
                    setIsLoading(false);
                    return;
                }

                window.google.accounts.id.initialize({
                    client_id: GOOGLE_CLIENT_ID,
                    callback: handleCredentialResponse,
                    auto_select: false,
                    cancel_on_tap_outside: false,
                });

                console.log('Google Auth initialized successfully');

                // Check if user is already signed in
                const savedToken = localStorage.getItem('google_access_token');
                const savedUser = localStorage.getItem('google_user');

                if (savedToken && savedUser) {
                    console.log('Found saved user session');
                    setAccessToken(savedToken);
                    setUser(JSON.parse(savedUser));
                    setIsAuthenticated(true);
                }

                setIsLoading(false);
            } catch (err) {
                console.error('Error initializing Google Auth:', err);
                setError(err);
                setIsLoading(false);
            }
        };

        const handleCredentialResponse = (response) => {
            try {
                console.log('Received credential response:', response);
                // Decode the JWT token to get user info
                const payload = JSON.parse(atob(response.credential.split('.')[1]));
                console.log('Decoded payload:', payload);

                const userData = {
                    id: payload.sub,
                    email: payload.email,
                    name: payload.name,
                    picture: payload.picture,
                };

                console.log('Setting user data:', userData);
                setUser(userData);
                setAccessToken(response.credential);
                setIsAuthenticated(true);

                // Save to localStorage
                localStorage.setItem('google_access_token', response.credential);
                localStorage.setItem('google_user', JSON.stringify(userData));

            } catch (err) {
                console.error('Error handling credential response:', err);
                setError(err);
            }
        };

        loadGoogleScript();

        // Cleanup function
        return () => {
            // Reset error state when component unmounts or remounts
            setError(null);
        };
    }, []);

    // Trigger Google sign-in
    const signInWithGoogle = () => {
        console.log('Sign in with Google clicked');

        if (!window.google) {
            console.error('Google object not available');
            setError(new Error('Google authentication not available'));
            return;
        }

        if (!window.google.accounts || !window.google.accounts.id) {
            console.error('Google accounts object not available');
            setError(new Error('Google authentication not properly initialized'));
            return;
        }

        try {
            console.log('Creating temporary Google button for sign-in...');

            // Create a temporary invisible button and trigger it
            const tempDiv = document.createElement('div');
            tempDiv.style.position = 'absolute';
            tempDiv.style.top = '-9999px';
            tempDiv.style.left = '-9999px';
            tempDiv.style.visibility = 'hidden';
            document.body.appendChild(tempDiv);

            // Render Google's button
            window.google.accounts.id.renderButton(tempDiv, {
                theme: 'outline',
                size: 'large',
                width: 200,
                type: 'standard'
            });

            // Find and click the rendered button
            setTimeout(() => {
                try {
                    const googleButton = tempDiv.querySelector('div[role="button"]');
                    if (googleButton) {
                        console.log('Triggering Google sign-in...');
                        googleButton.click();
                    } else {
                        console.error('Could not find Google button to click');
                        setError(new Error('Unable to initiate Google sign-in'));
                    }
                } catch (clickErr) {
                    console.error('Error clicking Google button:', clickErr);
                    setError(new Error('Unable to initiate Google sign-in'));
                } finally {
                    // Clean up the temporary element
                    if (document.body.contains(tempDiv)) {
                        document.body.removeChild(tempDiv);
                    }
                }
            }, 200);

        } catch (err) {
            console.error('Error setting up Google sign-in:', err);
            setError(err);
        }
    };

    const removeUser = () => {
        setUser(null);
        setAccessToken(null);
        setIsAuthenticated(false);
        localStorage.removeItem('google_access_token');
        localStorage.removeItem('google_user');

        // Sign out from Google
        if (window.google) {
            window.google.accounts.id.disableAutoSelect();
        }
    };



    return {
        isLoading,
        isAuthenticated,
        user,
        error,
        accessToken,
        signInWithGoogle,
        removeUser,
    };
}; 