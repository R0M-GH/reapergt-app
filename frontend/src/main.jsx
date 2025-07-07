import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { AuthProvider } from 'react-oidc-context';

console.log('main.jsx loaded');

const cognitoAuthConfig = {
    authority: "https://us-east-1cagrtsvtf.auth.us-east-1.amazoncognito.com",
    client_id: "7d3t35plvsbnv0a2dkt8ic24ls",
    redirect_uri: "https://app.getreaper.com/",
    post_logout_redirect_uri: "https://app.getreaper.com/",
    response_type: "code",
    scope: "email openid phone",
};

createRoot(document.getElementById('root')).render(
    <StrictMode>
        <AuthProvider {...cognitoAuthConfig}>
            <App />
        </AuthProvider>
    </StrictMode>,
)
