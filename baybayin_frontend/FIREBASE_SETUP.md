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
    },
    "admins": {
      ".read": "auth != null && auth.token.email == 'admin@gmail.com'",
      "$uid": {
        ".write": "auth != null && auth.uid == $uid && auth.token.email == 'admin@gmail.com'"
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
    },
    "admins": {
      ".read": "auth != null && auth.token.email == 'admin@gmail.com'",
      "$uid": {
        ".write": "auth != null && auth.uid == $uid && auth.token.email == 'admin@gmail.com'",
        "email": {
          ".validate": "newData.isString()"
        },
        "displayName": {
          ".validate": "newData.isString() && newData.val().length > 0"
        },
        "isAdmin": {
          ".validate": "newData.val() == true"
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

## 🧹 IMPORTANT: Clean Up Admin Data from Users Path

**After updating the rules, you need to:**

1. **Delete admin data from users path:**
   - In Firebase console, go to Data tab
   - Find and delete the admin entry under `users/` (the one with `"isAdmin": true`)
   - This will ensure complete separation between users and admins

2. **Test admin login:**
   - Log out from the app
   - Log back in as admin (admin@gmail.com)
   - The app will automatically create the admin profile in the new `admins/` path

## ✅ After These Steps:
- Admin will have their own separate `admins/` path in the database
- Users will only be in the `users/` path
- Complete separation between admin and user data
- Route guards will work properly

## Troubleshooting:

- Make sure your Firebase project has Realtime Database enabled
- Verify your Firebase config in `src/environments/environment.ts`
- Check that users are properly authenticated before accessing leaderboard
- Look for any console errors in the browser developer tools
- Try logging out and logging back in after updating rules
