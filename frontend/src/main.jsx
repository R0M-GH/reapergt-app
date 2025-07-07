import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { AuthProvider } from 'react-oidc-context';

console.log('main.jsx loaded');

const cognitoAuthConfig = {
    authority: "https://us-east-1_ZErx06uN7.auth.us-east-1.amazoncognito.com",
    client_id: "ghq72js41cdk53vcren6v436e",
    redirect_uri: "https://app.getreaper.com/",
    post_logout_redirect_uri: "https://app.getreaper.com/",
    response_type: "code",
    scope: "email openid phone",
    metadata: {
        authorization_endpoint: "https://us-east-1_ZErx06uN7.auth.us-east-1.amazoncognito.com/oauth2/authorize",
        token_endpoint: "https://us-east-1_ZErx06uN7.auth.us-east-1.amazoncognito.com/oauth2/token",
        end_session_endpoint: "https://us-east-1_ZErx06uN7.auth.us-east-1.amazoncognito.com/logout",
        userinfo_endpoint: "https://us-east-1_ZErx06uN7.auth.us-east-1.amazoncognito.com/oauth2/userInfo"
    }
};

createRoot(document.getElementById('root')).render(
    <StrictMode>
        <AuthProvider {...cognitoAuthConfig}>
            <App />
        </AuthProvider>
    </StrictMode>,
)
