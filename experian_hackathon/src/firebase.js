// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyCeEuexKPCgKWcLhgfz-qL926RzCRXWlJs",
  authDomain: "firsttimer-fc0b8.firebaseapp.com",
  projectId: "firsttimer-fc0b8",
  storageBucket: "firsttimer-fc0b8.appspot.com",
  messagingSenderId: "801926205331",
  appId: "1:801926205331:web:a02a168e7842392a982266",
  measurementId: "G-DK5JX9F1NG"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);