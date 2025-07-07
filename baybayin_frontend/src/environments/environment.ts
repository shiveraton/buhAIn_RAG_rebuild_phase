// This file can be replaced during build by using the `fileReplacements` array.
// `ng build` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.

export const environment = {
  production: false,
  django:{
    apiUrl: "http://127.0.0.1:8000/api"
  },
  firebase: {
    apiKey: "AIzaSyBzw6BIloiuuJ9OnbCADAnnk2YJpgzTuZY",
    authDomain: "buhain-f7e04.firebaseapp.com",
    databaseURL: "https://buhain-f7e04-default-rtdb.asia-southeast1.firebasedatabase.app",
    projectId: "buhain-f7e04",
    storageBucket: "buhain-f7e04.firebasestorage.app",
    messagingSenderId: "844860185915",
    appId: "1:844860185915:web:e6c2a53966faa8121fab1e",
    measurementId: "G-PLV6MFY3TV"
  }
};

/*
 * For easier debugging in development mode, you can import the following file
 * to ignore zone related error stack frames such as `zone.run`, `zoneDelegate.invokeTask`.
 *
 * This import should be commented out in production mode because it will have a negative impact
 * on performance if an error is thrown.
 */
// import 'zone.js/plugins/zone-error';  // Included with Angular CLI.
