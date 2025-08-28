# Forgot Password Implementation Guide

## Current Implementation

The forgot password functionality has been updated to allow sending reset links to non-verified users as long as their account exists with that email in the local database.

### How It Works

1. **Endpoint**: `POST /api/auth/forgot-password`
2. **Request Body**: `{"email": "user@example.com"}`
3. **Verification**: Checks if user exists in local database
4. **Link Generation**: Uses Firebase Admin SDK to generate password reset link
5. **Response**: Returns success message and generated reset link

### Key Changes Made

1. **`routers/auth.py`**: Added database check to verify user exists locally
2. **`firebase_client.py`**: Enhanced documentation and returns generated reset link
3. **`test_forgot_password.py`**: Updated test to include database session

## Email Sending Options

The Firebase Admin SDK's `generate_password_reset_link()` only generates the reset link but does NOT send the email automatically. Here are the recommended approaches:

### Option 1: Firebase Email Templates (Recommended)
1. Go to Firebase Console → Authentication → Templates
2. Configure the "Password reset" email template
3. Firebase will automatically send emails when reset links are generated

### Option 2: Third-Party Email Service
Integrate with services like SendGrid, Mailgun, or AWS SES:

```python
# Example with SendGrid
import sendgrid
from sendgrid.helpers.mail import Mail, Email, Content

async def send_reset_email_via_sendgrid(email: str, reset_link: str):
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("noreply@yourdomain.com")
    to_email = Email(email)
    subject = "Password Reset Request"
    content = Content("text/plain", f"Click here to reset your password: {reset_link}")
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    return response.status_code
```

### Option 3: Firebase Client SDK
Let the frontend handle email sending using Firebase client SDK:

```javascript
// Frontend implementation
import { getAuth, sendPasswordResetEmail } from "firebase/auth";

const auth = getAuth();
sendPasswordResetEmail(auth, email)
  .then(() => {
    console.log("Password reset email sent!");
  })
  .catch((error) => {
    console.error("Error sending reset email:", error);
  });
```

## Testing

Run the test to verify the functionality:

```bash
python test_forgot_password.py
```

The test will:
1. Check if the user exists in the local database
2. Generate a password reset link
3. Return the link for manual testing

## Security Considerations

- Never reveal whether an email exists in the system (prevents email enumeration)
- Reset links should have appropriate expiration times (configured in Firebase)
- Use HTTPS in production for secure link transmission

## Next Steps

1. Choose and implement one of the email sending options above
2. Configure Firebase email templates for automatic sending
3. Update frontend to handle the reset link appropriately
4. Add rate limiting to prevent abuse of the forgot password endpoint
