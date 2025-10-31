// This file can be replaced during build by using the `fileReplacements` array.
// `ng build` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.

export const environment = {
  production: false,
  django:{
    apiUrl: "http://127.0.0.1:8000/api"
  },
  firebaseConfig: {
    apiKey: "AIzaSyDH9tg9CT_JlB1o2gAT-OVxJV_shsI2YmM",
    authDomain: "buhain-eecbb.firebaseapp.com",
    projectId: "buhain-eecbb",
    storageBucket: "buhain-eecbb.firebasestorage.app",
    messagingSenderId: "362433499085",
    appId: "1:362433499085:web:9482dca5e920b3c24e7e84",
    measurementId: "G-R9400P4FTJ"
  }
};

// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
/*
 * For easier debugging in development mode, you can import the following file
 * to ignore zone related error stack frames such as `zone.run`, `zoneDelegate.invokeTask`.
 *
 * This import should be commented out in production mode because it will have a negative impact
 * on performance if an error is thrown.
 */
// import 'zone.js/plugins/zone-error';  // Included with Angular CLI.



// const firebaseConfig = {
//   apiKey: "AIzaSyDH9tg9CT_JlB1o2gAT-OVxJV_shsI2YmM",
//   authDomain: "buhain-eecbb.firebaseapp.com",
//   projectId: "buhain-eecbb",
//   storageBucket: "buhain-eecbb.firebasestorage.app",
//   messagingSenderId: "362433499085",
//   appId: "1:362433499085:web:9482dca5e920b3c24e7e84",
//   measurementId: "G-R9400P4FTJ"
// };

// // Initialize Firebase
// const app = initializeApp(firebaseConfig);
// const analytics = getAnalytics(app);