import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { AuthProvider } from 'react-oidc-context';

console.log('main.jsx loaded');

const cognitoAuthConfig = {
    authority: "https://reapergt.auth.us-east-1.amazoncognito.com",
    client_id: "ghq72js41cdk53vcren6v436e",
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
