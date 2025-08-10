import '@testing-library/jest-dom';

// Polyfill for TextEncoder/TextDecoder which is required by React Router v7
if (typeof global.TextEncoder === 'undefined') {
  global.TextEncoder = require('util').TextEncoder;
}

if (typeof global.TextDecoder === 'undefined') {
  global.TextDecoder = require('util').TextDecoder;
}