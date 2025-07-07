# Firebase Database Setup Instructions

## ✅ STATUS: RESOLVED - Leaderboard Now Working!

The leaderboard is now showing all users correctly after updating Firebase Database security rules.

## Issue Fixed: Permission Denied Error

The leaderboard was showing "Permission denied" because Firebase Realtime Database had restrictive security rules.

## ✅ Solution Applied: Updated Firebase Database Rules

1. Go to your Firebase Console: https://console.firebase.google.com
2. Select your project
3. Go to **Realtime Database** in the left sidebar
4. Click on the **Rules** tab
5. Replace the current rules with these **REQUIRED RULES**:

```json
{
  "rules": {
    "users": {
      ".read": "auth != null",
      "$uid": {
        ".write": "auth != null && auth.uid == $uid"
      }
    }
  }
}
```

## Alternative: More Permissive Development Rules

If you want to test quickly with full access (NOT recommended for production):

```json
{
  "rules": {
    ".read": "auth != null",
    ".write": "auth != null"
  }
}
```

## For Production (More Secure Rules):

```json
{
  "rules": {
    "users": {
      ".read": "auth != null",
      "$uid": {
        ".write": "auth != null && auth.uid == $uid",
        "totalScore": {
          ".validate": "newData.isNumber() && newData.val() >= 0"
        },
        "displayName": {
          ".validate": "newData.isString() && newData.val().length > 0"
        },
        "email": {
          ".validate": "newData.isString()"
        }
      }
    }
  }
}
```

## CRITICAL: Click "Publish" after updating rules!

After updating the rules:
1. Click **Publish** in Firebase Console
2. Wait 2-3 minutes for rules to propagate globally
3. Refresh your Ionic app
4. The leaderboard should now show all users

## Troubleshooting:

- Make sure your Firebase project has Realtime Database enabled
- Verify your Firebase config in `src/environments/environment.ts`
- Check that users are properly authenticated before accessing leaderboard
- Look for any console errors in the browser developer tools
- Try logging out and logging back in after updating rules
